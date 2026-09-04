# Changelog

All notable changes to SaltWatch are documented here.

## Unreleased

## 2.2.1 - 2026-09-04

- Updated the validated ESPHome toolchain from 2026.8.1 to 2026.8.2.
- Reclaimed the ESP32 SRAM1 region as 40 KB of additional instruction RAM on
  the ESP-IDF 5.5.5 factory-bootloader baseline.
- Reorganized the local device page into Status, Calibration, Forecast and
  Refill, and Diagnostics sections with task-oriented entity ordering.

## 2.2.0 - 2026-09-02

- Rebuilt the Home Assistant notification blueprint around the canonical Salt
  Status priority instead of three potentially overlapping problem entities.
- Added automatic device names to notification titles, an optional forecast
  toggle, and one optional reminder for a continuously active low-salt state.
- Grouped required, notification, and advanced inputs for a clearer setup flow.
- Reduced the required SaltWatch selections to Salt Status, Salt Level,
  Calibration Details, and Estimated Days Until Low Salt.
- Documented status transitions, reminder behavior, timer limitations, and the
  clean replacement of the earlier blueprint input model.

## 2.1.0 - 2026-09-02

- Added a persistent Last Recorded Refill timestamp for automatically confirmed
  and manually recorded refills.
- Kept refill recording and forecast-cycle transitions operational while the
  Home Assistant clock is unavailable; the pending timestamp is completed at
  the next successful synchronization.
- Documented refill timestamp semantics, confirmation timing, persistence, and
  failure behavior.

## 2.0.2 - 2026-09-02

- Added a hardware-free ESPHome host emulator for testing SaltWatch and
  SaltWatch Card without a physical sensor.
- Added adjustable emulator controls for salt level, device status, forecast
  days, forecast status, and forecast details, including unavailable-state
  testing.
- Documented local emulator setup and added automated validation and compilation
  to continuous integration.

## 2.0.1 - 2026-09-02

- Removed obsolete fixed entity-ID defaults from the notification blueprint;
  all required entities are now selected explicitly and filtered to ESPHome.
- Updated the notification setup guide and regression checks for MAC-suffixed
  SaltWatch entity IDs.

## 2.0.0 - 2026-09-02

- Added Forecast Details with learning progress and concise explanations for
  blocked forecasts, including insufficient usage, inconsistent readings, and
  refill confirmation.
- Added MAC-suffixed ESPHome node names so multiple SaltWatch devices have
  unique discovery names, hostnames, and Home Assistant device relationships.
- Updated installation, forecast, technical, and development documentation for
  the new diagnostic entity and multi-device naming.

## 1.5.1 - 2026-08-31

- Added a dedicated SaltWatch favicon to the browser installer.
- Added a Home Assistant dashboard preview to the README and identified
  SaltWatch Card as the preferred dashboard card for SaltWatch.

## 1.5.0 - 2026-08-29

- Moved Estimated Days Until Low Salt from a manually installed Home Assistant
  package into the SaltWatch device firmware.
- Added sparse-data gates, six-hour and daily aggregation, a robust 28-day
  Theil–Sen trend, residual-quality checks, and persisted completed-cycle rates.
- Added two-step automatic refill confirmation that recognizes both abrupt and
  gradual refills while excluding unconfirmed surface shifts from the trend.
- Added Record Salt Refill for small or unusual top-ups and retained learned
  prior-cycle consumption so forecasts can resume immediately after a refill.
- Added Forecast Status and an optional Forecast Confidence diagnostic.
- Made forecasting fail safe during sensor faults, invalid calibration, stale
  levels, missing time, restored-data inconsistency, and pending refill checks.
- Split forecast and notification guidance into focused documentation pages;
  notification setup remains a one-click Home Assistant blueprint import.
- Expanded regression coverage for noisy/outlier trends, refill spikes and
  confirmation, restored state, minimum evidence, and threshold boundaries.
- Added post-refill operating guidance and forecast items to the hardware
  acceptance checklist.
- Hardened forecast notifications with a stable delayed warning window and
  explicit measurement, low-salt, sensor, and calibration health checks.

## 1.4.0 - 2026-08-29

- Fixed recovery when the VL53L0X is disconnected and reconnected before the
  fault timeout by allowing one guarded recovery reboot for a present but
  stalled sensor.
- Added a persistent reboot-loop guard that is cleared by a valid measurement
  or a newly observed physical sensor disconnection.
- Normalized calibration comparisons to 0.1 cm units so an exact displayed
  10.0 cm span is always accepted.
- Normalized low-salt and hysteresis comparisons to the displayed 0.1% value so
  equality behaves consistently.
- Replaced the 32-bit startup timer with ESP-IDF's 64-bit monotonic timer.
- Added Calibration Details and Last Valid Measurement Age diagnostics.
- Added an optional Recorder-backed Home Assistant estimate for days until the
  configured low-salt threshold.
- Added an optional Home Assistant notification blueprint for low salt, sensor
  faults, calibration problems, forecast warnings, and recovery.
- Added table-driven regression checks for calibration, percentage, threshold,
  hysteresis, status priority, forecast availability, and timer behavior.

## 1.3.0 - 2026-08-29

- Removed the web-interface username and password at the owner's request.
- Removed the native ESPHome OTA password at the owner's request.
- Moved the local web UI and both OTA platforms into the shared configuration,
  so they are present immediately after web installation and remain present
  after Device Builder adoption without additional YAML edits.
- Reduced required secrets to Wi-Fi credentials and the encrypted native API
  key, and added explicit trusted-LAN warnings for the open control/update paths.
- Reworked the README into a concise, outcome-focused beginner guide and moved
  installation, hardware, calibration, technical, and development detail into
  dedicated documentation pages.
- Consolidated installer troubleshooting and network notes into one collapsed
  Help section so the primary install path stays visually clean.
- Reduced that disclosure to a subtle **Security and additional help** link,
  relying on ESP Web Tools for generic serial-port troubleshooting and keeping
  only SaltWatch-specific security and documentation guidance.
- Added a flat Contents section to the README for faster navigation.
- Reworked the README introduction around the Home Assistant outcome and
  removed release metadata from the opening section.
- Clarified that the installation cable may be USB-C-to-USB-C or
  USB-A-to-USB-C; only the ATOM Lite end and data capability are fixed.

## 1.2.0 - 2026-08-29

- Added a Digest-authenticated local ESPHome web interface.
- Added authenticated manual firmware upload through the web interface while
  retaining password-protected native ESPHome OTA.
- Embedded the web UI assets so the local interface does not depend on internet
  access, and disabled browser log streaming to reduce exposure and overhead.
- Added C008 programming-mode and USB serial troubleshooting instructions to
  the hosted installer and README.
- Kept automatic HTTP update checks and remote firmware downloads disabled.

## 1.1.0 - 2026-08-29

- Added an ESP Web Tools bootstrap installer hosted with GitHub Pages.
- Added USB-serial Wi-Fi provisioning and ESPHome dashboard adoption metadata
  to the public bootstrap build.
- Kept the normal production configuration encrypted and password-protected;
  public bootstrap credentials are never embedded in the firmware.
- Added GitHub Actions validation and compile checks for both firmware entry points.

## 1.0.0 - 2026-08-29

- Initial SaltWatch release for M5Stack ATOM Lite C008 and ToF Unit U010.
- Added validated, five-sample median-filtered VL53L0X distance measurement.
- Added independent startup/measurement watchdogs and stale-state invalidation.
- Added persistent full/empty calibration, capture buttons, percentage calculation,
  low-salt hysteresis, fault/calibration indicators, and combined status.
- Added encrypted native API, password-protected OTA, and
  disabled API/Wi-Fi reboot timeouts.
