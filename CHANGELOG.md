# Changelog

All notable changes to SaltWatch are documented here.

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
