#!/usr/bin/env python3
"""Exercise the actual firmware state/LED lambdas with a native C++ harness.

The fake light records commands; physical LED timing/color and ESPHome restore
behavior still need a firmware build and the hardware acceptance checklist.
"""

from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from validate_yaml import load_yaml


def run() -> None:
    core = load_yaml("saltwatch-core.yaml")

    def firmware_lambda(script_id):
        script = next(s for s in core["script"] if s["id"] == script_id)
        source = script["then"][0]["lambda"]
        return re.sub(
            r"\$\{(\w+)\}", lambda m: str(core["substitutions"][m[1]]), source
        )

    evaluate = firmware_lambda("evaluate_state")
    update = firmware_lambda("update_low_salt_led")
    used_ids = set(re.findall(r"id\((\w+)\)", evaluate + update))
    declarations = []
    for item in core["globals"]:
        if item["id"] in used_ids:
            declarations.append(
                f'{item["type"]} {item["id"]} = {item["initial_value"]};'
            )
    for domain, cpp_type in (
        ("sensor", "float"), ("number", "float"),
        ("binary_sensor", "bool"), ("switch", "bool"),
        ("text_sensor", "std::string"),
    ):
        for item in core[domain]:
            if item.get("id") in used_ids:
                declarations.append(f'Value<{cpp_type}> {item["id"]};')

    source = r'''
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <string>
#define id(name) name
#define ESP_LOGI(...) ((void)0)
#define ESP_LOGW(...) ((void)0)
#define ESP_LOGE(...) ((void)0)
uint64_t now_ms = 0;
uint64_t esp_timer_get_time() { return now_ms * 1000ULL; }
template<typename T> struct Value {
  T state{};
  bool known = false;
  bool has_state() const { return known; }
  void publish_state(T value) { state = value; known = true; }
};
struct Light {
  struct Remote {
    bool on = false;
    bool is_on() const { return on; }
  } remote_values;
  std::string effect = "None";
  int calls = 0;
  struct Call {
    Light &light;
    bool state = false, save = true, publish = true;
    float red = -1, green = -1, blue = -1, brightness = -1;
    std::string effect;
    void set_state(bool x) { state = x; }
    void set_save(bool x) { save = x; }
    void set_publish(bool x) { publish = x; }
    void set_rgb(float r, float g, float b) { red = r; green = g; blue = b; }
    void set_brightness(float x) { brightness = x; }
    void set_effect(const char *x) { effect = x; }
    void perform() {
      assert(!save && publish);
      if (state) {
        assert(effect == "Low Salt Blink");
        assert(red == 1 && green == 0 && blue == 0);
        assert(brightness > 0 && brightness <= 0.5f);
      } else {
        // ESPHome stops the effect on a normal off command; requesting an
        // explicit effect simultaneously is rejected by LightCall.
        assert(effect.empty());
        effect = "None";
      }
      light.remote_values.on = state;
      light.effect = effect;
      ++light.calls;
    }
  };
  Call make_call() { return Call{*this}; }
};
struct Device {
  // DECLARATIONS
  Light low_salt_led;
  void evaluate() {
    // EVALUATE
  }
  void update() {
    // UPDATE
  }
  void run() { evaluate(); update(); }
  void enable(bool enabled) { low_salt_led_alert.publish_state(enabled); update(); }
  void sample(float level) {
    has_valid_measurement = true;
    last_valid_measurement_ms = now_ms;
    consecutive_invalid_readings = 0;
    distance_to_salt.publish_state(110 - level);
    run();
  }
  void calibrate() {
    full_calibration_completed = empty_calibration_completed = true;
    full_distance.publish_state(10);
    empty_distance.publish_state(110);
  }
  bool blinking() const { return low_salt_led.remote_values.on; }
};
int main() {
  for (float threshold : {5.0f, 20.0f, 35.0f, 50.0f}) {
    now_ms = 0;
    Device d;
    d.low_salt_threshold.publish_state(threshold);
    d.calibrate();
    d.enable(true); // Restored/enabled preference cannot warn before a reading.
    d.run();
    assert(!d.blinking() && d.salt_status.state == "Initializing");
    d.sample(threshold + 0.1f);
    assert(!d.blinking());
    d.sample(threshold);
    assert(d.blinking() && d.low_salt.state);
    int calls = d.low_salt_led.calls;
    for (int i = 0; i < 20; ++i) d.run();
    assert(d.low_salt_led.calls == calls); // Don't restart the blink.
    d.sample(threshold + 5);
    assert(d.blinking());
    d.sample(threshold + 5.1f);
    assert(!d.blinking());
    d.enable(false);
    d.sample(threshold);
    assert(d.low_salt.state && !d.blinking());
    d.enable(true); // Enabling an already-low device takes effect immediately.
    assert(d.blinking());
    d.enable(false);
    assert(!d.blinking() && d.low_salt_led.effect == "None");
    assert(d.low_salt.state); // Disabling the LED must not disable the warning.
    d.enable(true);
    d.empty_calibration_completed = false;
    d.run();
    assert(!d.blinking() && d.calibration_required.state);
    d.calibrate();
    d.run();
    assert(d.blinking());
    d.consecutive_invalid_readings = 3;
    d.run();
    assert(!d.blinking() && d.sensor_fault.state);
    d.sample(threshold);
    assert(d.blinking());
    now_ms = 180000;
    d.run();
    assert(!d.blinking() && d.sensor_fault.state);
    d.sample(threshold);
    assert(d.blinking());
    d.distance_to_salt.publish_state(NAN);
    d.run();
    assert(!d.blinking() && !d.low_salt.state);
  }
  Device d;
  d.calibrate();
  d.low_salt_threshold.publish_state(35);
  d.sample(30);
  assert(d.low_salt.state && !d.blinking()); // Default is opt-in.
  d.enable(true);
  assert(d.blinking());
  d.low_salt_threshold.publish_state(20);
  d.run();
  assert(!d.blinking());
  d.low_salt_threshold.publish_state(40);
  d.run();
  assert(d.blinking());
  assert(!d.forecast_reset_requested); // Threshold/LED edits don't reset learning.
  Device restarted;
  restarted.calibrate();
  restarted.low_salt_threshold.publish_state(40);
  restarted.enable(true);
  restarted.run();
  assert(!restarted.blinking());
  restarted.sample(30);
  assert(restarted.blinking());
  now_ms = 60ULL * 24 * 60 * 60 * 1000; // Long offline uptime.
  restarted.sample(30);
  assert(restarted.blinking() && !restarted.sensor_fault.state);
}
'''
    source = source.replace("// DECLARATIONS", "\n".join(declarations))
    source = source.replace("// EVALUATE", evaluate).replace("// UPDATE", update)
    compiler = shutil.which("c++")
    assert compiler, "A C++ compiler is required for the firmware LED checks"
    with tempfile.TemporaryDirectory(prefix="saltwatch-led-test-") as temp:
        cpp = Path(temp, "test.cpp")
        binary = Path(temp, "test")
        cpp.write_text(source)
        subprocess.run([compiler, "-std=c++17", str(cpp), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    print("SaltWatch firmware LED checks passed")


if __name__ == "__main__":
    run()
