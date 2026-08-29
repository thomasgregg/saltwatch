# SaltWatch

Reliable salt-level monitoring for a water-softener brine tank, built with
ESPHome and Home Assistant.

[![ESPHome validation](https://github.com/thomasgregg/saltwatch/actions/workflows/esphome.yml/badge.svg)](https://github.com/thomasgregg/saltwatch/actions/workflows/esphome.yml)

**[Install SaltWatch in your browser](https://thomasgregg.github.io/saltwatch/)**

SaltWatch turns an M5Stack ATOM Lite and ToF distance sensor into a practical
salt monitor. It shows how far the salt surface is from the lid, converts that
measurement into a calibrated percentage, and makes faults or missing
calibration obvious instead of leaving a stale value in Home Assistant.

Version **1.3.0** · ESPHome project **`saltwatch.salt-monitor`**

## Contents

- [Why SaltWatch](#why-saltwatch)
- [Hardware](#hardware)
- [Quick start](#quick-start)
- [Calibration](#calibration)
- [Home Assistant entities](#home-assistant-entities)
- [Trustworthy failure behavior](#trustworthy-failure-behavior)
- [Local web interface and updates](#local-web-interface-and-updates)
- [Documentation](#documentation)
- [Supported hardware and firmware](#supported-hardware-and-firmware)
- [License](#license)

## Why SaltWatch

A softener can keep running after the salt is nearly gone, and a failed sensor
can look deceptively normal if its last reading remains visible. SaltWatch is
designed around those two problems:

- see the current lid-to-salt distance and estimated salt percentage;
- get a stable low-salt warning with hysteresis;
- calibrate full and empty levels from Home Assistant;
- distinguish low salt from invalid calibration and sensor failure;
- remove stale measurements automatically when valid readings stop; and
- continue measuring when Home Assistant is offline.

The firmware deliberately avoids predictions, regeneration tracking, cloud
services, historical buffers, MQTT, and other features that do not improve the
core measurement.

## Hardware

- M5Stack ATOM Lite **C008**
- M5Stack ToF Unit **U010** with VL53L0X
- Included Grove cable
- USB-A-to-USB-C data cable for installation
- 5 V USB power supply
- 3M Dual Lock SJ3550 and a rubber cable grommet for mounting

The ToF Unit mounts inside the lid and points down at the salt. The ATOM Lite
stays outside the tank. See the [hardware and acceptance guide](docs/hardware.md)
before permanent installation.

## Quick start

1. Open the **[SaltWatch web installer](https://thomasgregg.github.io/saltwatch/)**
   in desktop Chrome or Microsoft Edge.
2. Connect the ATOM Lite directly to the computer with a USB data cable. The
   C008 normally enters programming mode automatically.
3. Select **Connect and install SaltWatch**, choose the serial port, and approve
   the installation.
4. Enter the 2.4 GHz Wi-Fi credentials when prompted.
5. Open the local interface at the address shown by the installer. No login is
   required.
6. Open ESPHome Device Builder in Home Assistant and select **Adopt** for the
   discovered SaltWatch device. Adoption generates the encrypted native API
   configuration automatically.
7. Add the discovered ESPHome integration under **Settings → Devices &
   services**.
8. Install the sensor in the lid and complete both calibration steps below.

No command line, local ESPHome installation, OTA password, or web-server
password is required for this route. For alternative installation and update
methods, see the [installation guide](docs/installation.md).

## Calibration

Salt Level remains unavailable until both calibration points are completed.
This prevents placeholder values from appearing as a believable percentage.

### Set the full point

1. Fill the tank to its normal desired full level and close the lid normally.
2. Wait two to three minutes for **Distance to Salt** to settle.
3. Press **Set Current Distance as Full** in Home Assistant or the local web UI.

### Set the empty point

1. At the lowest useful salt level, close the lid normally.
2. Wait for **Distance to Salt** to settle.
3. Press **Set Current Distance as Empty**.
4. Confirm **Calibration Required** turns off and **Salt Level** becomes
   available.

Empty means the lowest useful and reliably measurable level, not necessarily
the physical bottom of the tank. Both distances can also be entered manually.
See the [calibration and operation guide](docs/calibration.md) for validation
rules, manual calibration, and low-salt behavior.

## Home Assistant entities

| Entity | Purpose |
| --- | --- |
| **Distance to Salt** | Median-filtered distance from the lid to the salt surface in centimetres. |
| **Salt Level** | Calibrated and clamped estimate from 0–100%. |
| **Salt Status** | `Initializing`, `Sensor Fault`, `Calibration Required`, `Low Salt`, or `Good`. |
| **Low Salt** | Problem indicator that includes five percentage points of hysteresis. |
| **Sensor Fault** | Reports missing, timed-out, invalid, or out-of-range measurements. |
| **Calibration Required** | Reports incomplete, reversed, out-of-range, or insufficient calibration. |
| **Full Distance** | Persistent full-level calibration value. |
| **Empty Distance** | Persistent empty-level calibration value. |
| **Low Salt Threshold** | Persistent warning threshold; default 20%. |
| **Set Current Distance as Full** | Captures the current filtered distance as full. |
| **Set Current Distance as Empty** | Captures the current filtered distance as empty. |
| **WiFi Signal** | Standard ESPHome diagnostic signal strength. |

Entity names and identifiers are kept stable so firmware updates do not create
duplicates in Home Assistant.

## Trustworthy failure behavior

SaltWatch accepts only finite readings from 5–120 cm and feeds only valid
measurements into its five-sample median. Independent startup and measurement
watchdogs ensure that a disconnected, blocked, or malfunctioning sensor cannot
leave an old distance displayed indefinitely.

When measurement fails, Distance to Salt and Salt Level become unavailable,
Sensor Fault turns on, Low Salt turns off, and Salt Status becomes Sensor Fault.
Valid measurements recover automatically. Calibration persists across normal
restarts and sensor recovery.

The detailed filtering, timeout, status-priority, persistence, and recovery
design is documented in the [technical reference](docs/technical-reference.md).

## Local web interface and updates

After Wi-Fi provisioning, open `http://saltwatch.local/` or the device IP. The
local interface shows the SaltWatch entities, supports calibration controls,
and accepts manual OTA firmware uploads. ESPHome Device Builder can also install
updates wirelessly.

The web interface and both OTA paths intentionally have no password. Anyone who
can reach the device can change calibration or replace its firmware. Keep
SaltWatch on a trusted, preferably isolated IoT network, never expose it to the
internet, and restrict access with firewall rules when possible. Home Assistant
API communication is encrypted after Device Builder adoption.

## Documentation

- [Installation and updates](docs/installation.md) — browser installation,
  Device Builder adoption, manual builds, and OTA updates
- [Hardware installation and acceptance](docs/hardware.md) — mounting, wiring,
  care, and the complete hardware test checklist
- [Calibration and operation](docs/calibration.md) — full/empty calibration,
  manual values, thresholds, hysteresis, and normal use
- [Technical reference](docs/technical-reference.md) — measurement pipeline,
  failure handling, persistence, status rules, entities, and limitations
- [Development and validation](docs/development.md) — repository structure,
  build commands, CI, release artifacts, and validation results
- [Changelog](CHANGELOG.md)

## Supported hardware and firmware

SaltWatch is built for the M5Stack ATOM Lite C008 using the `m5stack-atom`
board definition, ESP-IDF, GPIO26/GPIO32 I²C, and the VL53L0X at address `0x29`
in long-range mode. Release builds are validated with ESPHome 2026.8.1 and
ESP-IDF 5.5.5.

## License

[MIT](LICENSE)
