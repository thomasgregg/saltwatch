# Changelog

All notable changes to SaltWatch are documented here.

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
