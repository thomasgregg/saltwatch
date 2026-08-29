# Technical reference

[← Back to SaltWatch](../README.md)

This document describes the firmware behavior behind the public SaltWatch
entities. The implementation uses standard ESPHome components plus small YAML
lambdas and watchdog scripts; it does not use a custom C++ component.

## Project identity

| Property | Value |
| --- | --- |
| Project | SaltWatch |
| Node name | `saltwatch` |
| Friendly name | `SaltWatch` |
| ESPHome project | `saltwatch.salt-monitor` |
| Release | 1.4.0 |
| Board | `m5stack-atom` |
| Framework | ESP-IDF |
| I²C | SDA GPIO26, SCL GPIO32 |
| Sensor | VL53L0X at `0x29`, long-range mode |

Entity names are intentionally stable so updates preserve Home Assistant entity
registry entries.

## Measurement pipeline

1. The VL53L0X polls every 30 seconds in long-range mode.
2. Each raw value is inspected before filtering.
3. `NaN`, values below 5 cm, and values above 120 cm are rejected.
4. Rejected readings increment an independent consecutive-invalid counter.
5. Only valid readings enter a five-value moving median with `send_every: 1`.
6. A timeout filter is last in the filtered path and publishes `NaN` after 180
   seconds without a valid input.
7. Public distance is converted from metres to centimetres and exposed with one
   decimal place.

Keeping the timeout last ensures its generated `NaN` cannot be swallowed by a
later filter. An independent startup watchdog covers the special case where the
filter has never received its first valid value.

The first valid reading is published immediately. The median becomes fully
representative after five valid samples, which takes approximately two to three
minutes at the 30-second interval.

## Sensor-fault detection

Sensor Fault activates for any of these conditions:

- no valid measurement within 180 seconds of startup;
- no new valid measurement for 180 seconds during normal operation;
- three consecutive invalid raw readings;
- a raw `NaN` sequence;
- distance below 5 cm or above 120 cm; or
- missing/unavailable VL53L0X hardware.

Fault evaluation does not depend solely on the public filtered sensor. Raw
invalid readings update health state before they are discarded.

When a fault activates:

- Distance to Salt publishes `NaN`;
- Salt Level publishes `NaN`;
- Low Salt turns off;
- Sensor Fault turns on; and
- Salt Status becomes `Sensor Fault`.

A valid reading clears the fault and recalculates all dependent entities. While
faulted, SaltWatch probes the VL53L0X identity register. It permits one
controlled recovery reboot both when a previously absent sensor reappears and
when the sensor is already present but the standard driver has stalled. A
persistent one-shot guard prevents a blocked or malfunctioning sensor from
causing a reboot loop. The guard clears after a valid measurement or a newly
observed physical disconnection. Calibration persists across recovery.

## Calibration persistence and validation

Full Distance and Empty Distance are persistent ESPHome template numbers.
SaltWatch stores two additional persistent boolean flags:

- full calibration completed;
- empty calibration completed.

This prevents numeric defaults from being treated as real calibration.

Manual number edits and successful capture-button actions set the corresponding
flag. Button captures use the current filtered distance and reject the request
during Sensor Fault or when distance is unavailable.

Values are normalized to the displayed 0.1 cm resolution before comparison, so
binary floating-point representation cannot reject a displayed 10.0 cm span.
Calibration is valid only when:

- both completion flags are true;
- both values are within 5–120 cm;
- Full Distance is strictly less than Empty Distance; and
- the span is at least 10 cm.

An invalid relationship is never silently corrected or swapped.

## Salt-level calculation

```text
(Empty Distance - Current Distance)
----------------------------------- × 100
 (Empty Distance - Full Distance)
```

The result is clamped and rounded to its displayed 0.1% resolution. Salt Level
publishes `NaN` whenever Sensor Fault is active, calibration is
incomplete/invalid, or current distance is unavailable. Division is never
attempted for a zero or invalid span.

## Low-salt logic

Low Salt activates at or below Low Salt Threshold; equality counts as low.
After activation it clears only above threshold plus five percentage points.
Threshold comparisons use the same displayed tenth-percent value published to
Home Assistant. Equality therefore behaves consistently despite binary
floating-point representation. This hysteresis prevents warning chatter near
the threshold.

Low Salt is forced off whenever:

- Sensor Fault is active;
- Calibration Required is active; or
- Salt Level is unavailable.

## Status priority

Salt Status is derived from the underlying entities in exactly this order:

1. `Initializing`
2. `Sensor Fault`
3. `Calibration Required`
4. `Low Salt`
5. `Good`

It does not keep an independent state machine. Sensor Fault therefore always
overrides calibration and low-salt conditions, and Good cannot appear while any
higher-priority problem is active.

## Entity reference

| Entity | Type | Important behavior |
| --- | --- | --- |
| Distance to Salt | Sensor, cm | One decimal, measurement state class, five-valid-sample median, unavailable after timeout. |
| Salt Level | Sensor, % | One decimal, measurement state class, clamped 0–100%, unavailable outside valid operating conditions. |
| Full Distance | Number, cm | 5–120 cm, 0.1 cm steps, persistent; editing completes full calibration. |
| Empty Distance | Number, cm | 5–120 cm, 0.1 cm steps, persistent; editing completes empty calibration. |
| Low Salt Threshold | Number, % | 5–50%, whole-percent steps, persistent, default 20%. |
| Set Current Distance as Full | Button | Captures only a valid filtered distance. |
| Set Current Distance as Empty | Button | Captures only a valid filtered distance. |
| Low Salt | Problem binary sensor | Inclusive threshold with five-point clearing hysteresis. |
| Sensor Fault | Problem binary sensor | Raw-invalid, repeated-invalid, startup, timeout, range, and hardware checks. |
| Calibration Required | Problem binary sensor | Persistent completion, range, order, and minimum-span checks. |
| Salt Status | Text sensor | Derived priority state. |
| Calibration Details | Diagnostic text sensor | Exact missing or invalid calibration reason, or `Valid`. |
| WiFi Signal | Diagnostic sensor | Standard ESPHome Wi-Fi RSSI. |
| Last Valid Measurement Age | Diagnostic sensor, s | Monotonic age of the most recent accepted raw reading; disabled by default to avoid unnecessary history. |

## Connectivity and resilience

- Wi-Fi and native API reboot timeouts are disabled (`reboot_timeout: 0s`).
- Home Assistant can remain offline without restarting SaltWatch or clearing
  calibration.
- Measurement and local status evaluation continue without Home Assistant.
- The production native API uses encryption.
- The local web interface is self-contained and does not load its assets from
  the internet.
- Browser log streaming is disabled.
- Web UI, web OTA, and native OTA are intentionally passwordless.
- No fallback access point or captive portal is enabled.

## Deliberately excluded

The SaltWatch firmware does not implement automatic regeneration detection,
last regeneration, overdue warnings, salt-consumption history, historical
buffers, usage trends, fast polling, MQTT, automatic HTTP update checks, remote
firmware downloads, cloud services, RGB status behavior, a custom Home
Assistant dashboard, or tank-height configuration.

An optional Home Assistant package provides a days-until-low estimate, and an
optional blueprint provides notifications. They do not add history or
forecasting state to the firmware and are not required for core operation.

These may be considered later, but none is required for dependable measurement
and explicit failure reporting.

## Limitations

- The VL53L0X is optical. Salt dust, condensation, dark or angled surfaces, and
  external infrared light can reduce range or stability.
- Percentage assumes a linear relationship between distance and stored salt.
  Tank shape and brine voids make it an estimate rather than a mass measurement.
- The five-value median intentionally delays complete response to a changed
  surface by approximately two to three minutes.
- Recovery from a stalled or reconnected I²C sensor may require one controlled
  reboot to initialize the standard ESPHome driver.
- The optional days-until-low value needs at least seven days of Home Assistant
  Recorder history and a meaningful downward trend. It can be unavailable or
  inaccurate around refills and changing water use.
- Network access is equivalent to device administration because the web UI and
  OTA paths are passwordless.

## Authoritative component documentation

- [ESPHome VL53L0X](https://esphome.io/components/sensor/vl53l0x/)
- [ESPHome sensor timeout filter](https://esphome.io/components/sensor/filter/timeout/)
- [ESPHome native API](https://esphome.io/components/api/)
- [ESPHome native OTA](https://esphome.io/components/ota/esphome/)
- [ESPHome web server](https://esphome.io/components/web_server/)
- [ESPHome web-server OTA](https://esphome.io/components/ota/web_server/)
