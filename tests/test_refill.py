#!/usr/bin/env python3
"""Run actual firmware actions with fake time, measurements, button and LED.

The harness translates the small synchronous ESPHome action subset used here;
unknown actions fail rather than silently skipping firmware behavior. Hardware
GPIO debounce and the ESPHome median implementation are checked separately.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from validate_yaml import load_yaml


def run():
    core = load_yaml('saltwatch-core.yaml')
    scripts = {s['id']: s for s in core['script']}
    names = ['request_salt_refill', 'process_salt_refill', 'update_low_salt_led',
             'forecast_record_refill', 'commit_salt_refill',
             'forecast_reset_learning', 'forecast_publish_refill_timestamp',
             'forecast_evaluate', 'evaluate_state', 'forecast_finalize_bucket',
             'forecast_recalculate_model']

    def expand(code):
        code = re.sub(r'\$\{(\w+)\}', lambda m: core['substitutions'][m[1]], code)
        return re.sub(r'id\((\w+)\)\.execute\(\)', lambda m: m[1] + '()', code)

    def actions(items):
        out = []
        for a in items:
            if 'lambda' in a:
                # Return exits only the lambda action, not subsequent actions.
                out.append('[&]() {\n' + expand(a['lambda']) + '\n}();')
            elif 'script.execute' in a:
                out.append(a['script.execute'] + '();')
            elif 'script.wait' in a or 'logger.log' in a:
                pass  # All these scripts are synchronous and logs have no state.
            elif 'if' in a:
                branch = a['if']
                out.append('if ([&]() { ' + expand(branch['condition']['lambda']) +
                           ' }()) {\n' + actions(branch['then']) + '\n} else {\n' +
                           actions(branch.get('else', [])) + '\n}')
            else:
                raise AssertionError(f'Unsupported action: {a}')
        return '\n'.join(out)

    declarations = [expand(f"{g['type']} {g['id']} = {g['initial_value']};")
                    for g in core['globals']]
    for domain, typ in [('sensor', 'float'), ('number', 'float'),
                        ('binary_sensor', 'bool'), ('switch', 'bool'),
                        ('text_sensor', 'std::string')]:
        declarations += [f"Value<{typ}> {e['id']};" for e in core[domain] if 'id' in e]
    functions = '\n'.join('void ' + n + '() {\n' + actions(scripts[n]['then']) + '\n}'
                          for n in names)
    raw = core['sensor'][0]['filters'][1]['lambda']
    button = core['binary_sensor'][0]['on_state'][0]['lambda']
    blink = core['light'][0]['effects'][0]['lambda']['lambda']
    guard = scripts['forecast_record_refill']['then'][0]['if']['condition']['lambda']
    source = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <deque>
#include <optional>
#include <string>
#define id(name) name
#define ESP_LOGI(...) ((void)0)
#define ESP_LOGW(...) ((void)0)
#define ESP_LOGE(...) ((void)0)
uint64_t now_ms = 10000;
uint64_t esp_timer_get_time() { return now_ms * 1000ULL; }
template<typename T> struct Value {
  T state{}; bool known = false;
  bool has_state() const { return known; }
  void publish_state(T x) { state = x; known = true; }
};
struct Time {
  bool valid = true; uint32_t timestamp = 1791000000; int hour = 12;
  bool is_valid() const { return valid; }
  int timezone_offset() const { return 0; }
  Time now() const { return *this; }
};
struct Light {
  struct Remote { bool on = false; bool is_on() const { return on; } } remote_values;
  std::string effect = "None"; float red=0, green=0, blue=0, brightness=0;
  struct Call {
    Light &l; bool on=false; std::string effect;
    float r=-1,g=-1,b=-1,brightness=-1;
    void set_state(bool x) { on=x; }
    void set_effect(const char *x) { effect=x; }
    void set_rgb(float x,float y,float z) { r=x;g=y;b=z; }
    void set_brightness(float x) { brightness=x; }
    void set_save(bool x) { assert(!x); }
    void set_publish(bool) {}
    void set_transition_length(int x) { assert(x==0); }
    void perform() {
      l.remote_values.on=on;
      if (!on) { l.effect="None";l.brightness=0; }
      else {
        if (!effect.empty()) l.effect=effect;
        if(r>=0) { l.red=r;l.green=g;l.blue=b; }
        if(brightness>=0) l.brightness=brightness;
      }
    }
  };
  Call make_call() { return Call{*this}; }
};
struct Device {
  // DECLARATIONS
  Time homeassistant_time; Light low_salt_led;
  std::deque<float> samples;
  Device() {
    full_calibration_completed=empty_calibration_completed=true;
    full_distance.publish_state(10); empty_distance.publish_state(110);
    low_salt_threshold.publish_state(20); low_salt_led_brightness.publish_state(30);
    last_recorded_refill_timestamp=1700000000;
    refill_recording_status.publish_state("Ready");
    sample(70);
  }
  // FUNCTIONS
  bool commit_allowed() { // GUARD
  }
  std::optional<float> raw(float x) { // RAW
  }
  void button(bool x) { // BUTTON
  }
  void blink(bool initial_run=false) { // BLINK
  }
  void sample(float distance) {
    const auto value=raw(distance);
    if(value) {
      samples.push_back(*value); if(samples.size()>5) samples.pop_front();
      auto sorted=samples;std::sort(sorted.begin(),sorted.end());
      const auto mid=sorted.size()/2;
      distance_to_salt.publish_state(sorted.size()%2 ? sorted[mid] : (sorted[mid-1]+sorted[mid])/2.0f);
    }
    evaluate_state();process_salt_refill();
  }
  void fresh(float distance=30) { now_ms+=30000;sample(distance); }
  void finish(float distance=30) { for(int i=0;i<5;i++) fresh(distance); }
  void tick(uint64_t ms) { now_ms+=ms;evaluate_state();process_salt_refill();update_low_salt_led(); }
};
int main() {
  // Short presses, exact boundary, held-at-boot, and stuck buttons.
  for(uint64_t duration : {1999ULL,2000ULL,10000ULL,10001ULL}) {
    now_ms=10000;Device d;d.button(false);d.button(true);now_ms+=duration;d.button(false);
    assert(d.refill_pending == (duration>=2000 && duration<=10000));
    if(d.refill_pending) {
      uint64_t start=d.refill_request_started_ms;d.request_salt_refill();
      assert(d.refill_request_started_ms==start && d.refill_fresh_readings==0);
    }
  }
  now_ms=10000;Device boot;boot.button(true);now_ms+=3000;boot.button(false);
  assert(!boot.refill_pending);boot.button(true);now_ms+=2000;boot.button(false);
  assert(boot.refill_pending);boot.button(false);assert(boot.refill_pending);

  // Real raw-filter counting and shared controls: old filtered state is ignored.
  now_ms=10000;Device d;d.forecast_daily_count=4;d.request_salt_refill();
  assert(d.refill_feedback==1 && d.low_salt_led.blue==1);
  assert(d.last_recorded_refill_timestamp==1700000000 && d.forecast_daily_count==4);
  for(int i=0;i<20;i++)d.process_salt_refill();assert(d.refill_fresh_readings==0);
  d.tick(1000);assert(!d.low_salt_led.remote_values.is_on());
  for(int i=0;i<4;i++)d.fresh();assert(d.refill_pending && d.forecast_daily_count==4);
  d.fresh();assert(!d.refill_pending && d.refill_recording_status.state=="Recorded");
  assert(d.salt_level.state==80 && d.forecast_daily_count==0);
  assert(d.forecast_details.state=="0 of 7 days collected");
  assert(d.last_recorded_refill_timestamp==d.homeassistant_time.timestamp);
  assert(d.low_salt_led.green==1 && d.low_salt_led.effect=="None");
  d.tick(1000);assert(!d.low_salt_led.remote_values.is_on());
  d.request_salt_refill();assert(!d.refill_pending && d.refill_recording_status.state=="Recently recorded");
  d.tick(300000);d.sample(30);d.request_salt_refill();assert(d.refill_pending);

  // Invalid samples reset the count, but successful recovery can finish.
  now_ms=10000;Device invalid;invalid.request_salt_refill();invalid.fresh();invalid.fresh();
  invalid.fresh(NAN);assert(invalid.refill_pending && invalid.refill_fresh_readings==0);
  invalid.finish();assert(invalid.refill_recording_status.state=="Recorded");
  for(float value : {NAN,INFINITY,4.9f,120.1f}) {
    now_ms=10000;Device bad;bad.request_salt_refill();bad.fresh(value);bad.fresh(value);bad.fresh(value);
    assert(!bad.refill_pending && bad.last_recorded_refill_timestamp==1700000000);
    assert(bad.refill_recording_status.state=="Sensor fault");
  }
  now_ms=10000;Device stale;stale.request_salt_refill();stale.tick(180000);
  assert(!stale.refill_pending && stale.last_recorded_refill_timestamp==1700000000);
  // Separate timeout scenario keeps a healthy sensor but never five consecutive readings.
  now_ms=10000;Device slow;slow.request_salt_refill();
  for(int i=0;i<10;i++)slow.fresh(i%2 ? NAN : 30);
  assert(!slow.refill_pending && slow.refill_recording_status.state=="Timed out");

  // Calibration edits cancel, including a valid span change; no refill is recorded.
  now_ms=10000;Device cal;cal.request_salt_refill();cal.full_distance.publish_state(11);cal.evaluate_state();
  assert(!cal.refill_pending && cal.refill_recording_status.state=="Calibration changed");
  assert(cal.last_recorded_refill_timestamp==1700000000);
  now_ms=10000;Device required;required.empty_calibration_completed=false;required.evaluate_state();
  required.request_salt_refill();assert(!required.refill_pending);
  assert(required.refill_recording_status.state=="Calibration required");
  now_ms=10000;Device no_sensor;no_sensor.consecutive_invalid_readings=3;no_sensor.evaluate_state();
  no_sensor.request_salt_refill();assert(!no_sensor.refill_pending);

  // Learned current model becomes historical; missing time defers only timestamp.
  now_ms=10000;Device learned;learned.request_salt_refill();
  learned.forecast_current_model_valid=true;learned.forecast_current_rate=1;
  learned.forecast_current_days=14;learned.forecast_refill_candidate=true;
  learned.homeassistant_time.valid=false;learned.finish();
  assert(learned.forecast_historical_rate==1 && learned.forecast_completed_cycles==1);
  assert(!learned.forecast_refill_candidate && learned.forecast_status.state=="Available");
  assert(learned.forecast_details.state=="Based on previous refill cycle");
  assert(learned.estimated_days_until_low_salt.state==60);
  assert(learned.last_recorded_refill_timestamp==-1 && std::isnan(learned.last_recorded_refill.state));
  learned.homeassistant_time.valid=true;learned.forecast_publish_refill_timestamp();
  assert(learned.last_recorded_refill_timestamp==learned.homeassistant_time.timestamp);

  // Historical-only forecasts survive small top-ups and repeated commit calls.
  now_ms=10000;Device historical;historical.forecast_historical_rate=0.5f;
  historical.forecast_historical_variance=0.1f;historical.forecast_completed_cycles=2;
  historical.request_salt_refill();historical.finish(69);
  assert(historical.forecast_historical_rate==0.5f && historical.forecast_completed_cycles==2);
  assert(historical.forecast_historical_variance==0.1f && historical.salt_level.state==41);
  assert(historical.forecast_status.state=="Available");
  auto historical_stamp=historical.last_recorded_refill_timestamp;
  historical.forecast_record_refill();assert(historical.last_recorded_refill_timestamp==historical_stamp);
  assert(historical.forecast_completed_cycles==2);

  // Low salt remains active after a small refill; feedback does not change preferences.
  now_ms=10000;Device low;low.sample(100);low.sample(100);low.low_salt_led_alert.publish_state(true);low.update_low_salt_led();
  low.request_salt_refill();assert(low.low_salt_led.blue==1);
  low.tick(1000);assert(low.low_salt_led.effect=="Low Salt Blink");
  low.finish(95);assert(low.low_salt.state && low.refill_recording_status.state=="Recorded");
  assert(low.low_salt_led.green==1);low.tick(1000);assert(low.low_salt_led.effect=="Low Salt Blink");
  now_ms=10000;Device setting;setting.request_salt_refill();
  setting.low_salt_led_alert.publish_state(true);setting.sample(100);setting.sample(100);
  setting.low_salt_led_brightness.publish_state(70);setting.tick(1000);
  assert(setting.low_salt_led.effect=="Low Salt Blink" && setting.low_salt_led.brightness==0.7f);
  setting.low_salt_led_alert.publish_state(false);setting.update_low_salt_led();
  assert(!setting.low_salt_led.remote_values.is_on());

  // Cancellation feedback restores the latest warning/settings, never an old snapshot.
  now_ms=10000;Device cancelled;cancelled.sample(100);cancelled.sample(100);
  cancelled.low_salt_led_alert.publish_state(true);cancelled.request_salt_refill();
  cancelled.fresh(NAN);cancelled.fresh(NAN);cancelled.fresh(NAN);
  assert(cancelled.refill_feedback==3 && cancelled.low_salt_led.red==1 && cancelled.low_salt_led.green==0.5f);
  cancelled.low_salt_led_brightness.publish_state(90);cancelled.sample(100);cancelled.tick(1000);
  assert(cancelled.low_salt_led.effect=="Low Salt Blink" && cancelled.low_salt_led.brightness==0.9f);
  now_ms=10000;Device cleared;cleared.sample(100);cleared.sample(100);cleared.low_salt_led_alert.publish_state(true);
  cleared.request_salt_refill();cleared.sample(30);cleared.sample(30);cleared.tick(1000);
  assert(!cleared.low_salt.state && !cleared.low_salt_led.remote_values.is_on());

  // Automatic detection wins a simultaneous request and records only one event.
  now_ms=10000;Device automatic;automatic.request_salt_refill();
  automatic.forecast_refill_candidate=true;automatic.forecast_refill_candidate_day=automatic.homeassistant_time.timestamp/86400;
  automatic.forecast_refill_base=20;automatic.forecast_refill_candidate_level=50;
  automatic.forecast_bucket_sum=36*50;automatic.forecast_bucket_sample_count=36;
  automatic.forecast_finalize_bucket();
  assert(!automatic.refill_pending && automatic.refill_recording_status.state=="Auto recorded");
  auto stamp=automatic.last_recorded_refill_timestamp;automatic.finish();
  assert(automatic.last_recorded_refill_timestamp==stamp);
  automatic.request_salt_refill();assert(!automatic.refill_pending);

  // Final commit guard refuses direct bypasses and the timeout boundary.
  now_ms=10000;Device guard;assert(!guard.commit_allowed());guard.request_salt_refill();
  assert(!guard.commit_allowed());guard.refill_fresh_readings=5;assert(guard.commit_allowed());
  now_ms+=90000;assert(!guard.commit_allowed());guard.last_valid_measurement_ms=now_ms;
  now_ms=guard.refill_request_started_ms+300000;assert(!guard.commit_allowed());
  Device restarted;assert(!restarted.refill_pending && restarted.refill_feedback==0);
}
'''
    source = source.replace('// DECLARATIONS', '\n'.join(declarations)).replace('// FUNCTIONS', functions)
    for marker, body in [('GUARD', guard), ('RAW', raw), ('BUTTON', button), ('BLINK', blink)]:
        source = source.replace('// ' + marker, expand(body))
    with tempfile.TemporaryDirectory(prefix='saltwatch-refill-test-') as tmp:
        cpp=Path(tmp,'test.cpp');binary=Path(tmp,'test');cpp.write_text(source)
        subprocess.run([shutil.which('c++'), '-std=c++17', str(cpp), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    print('SaltWatch firmware refill/button/LED checks passed')


if __name__ == '__main__':
    run()
