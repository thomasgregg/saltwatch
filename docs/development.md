# Development and validation

[← Back to SaltWatch](../README.md)

## Repository structure

| Path | Purpose |
| --- | --- |
| `saltwatch-core.yaml` | Shared, credential-free hardware and monitoring configuration. |
| `web/` | Bundled offline device interface with the slider unit-alignment fix and upstream license. |
| `tools/build_web_ui.py` | Regenerates the bundled interface from the validated ESPHome version. |
| `saltwatch.yaml` | Production entry point with Wi-Fi credentials and encrypted API key. |
| `saltwatch-webinstall.yaml` | Credential-free browser-installer build and adoption metadata. |
| `saltwatch-emulator.yaml` | Hardware-free ESPHome host device for Home Assistant and card testing. |
| `secrets.yaml.example` | Required secret names for manual production builds. |
| `docs/index.html` | ESP Web Tools installer page. |
| `docs/manifest.json` | Versioned ESP Web Tools manifest. |
| `docs/*.factory.bin` | Published versioned browser-installer factory images. |
| `docs/*.ota.bin` | Canonical managed-update images. |
| `home-assistant/blueprints/` | Optional SaltWatch notification blueprint. |
| `tests/` | Small logic, Home Assistant YAML, and release-metadata regression checks. |
| `.github/workflows/esphome.yml` | Clean configuration and compile validation. |
| `CHANGELOG.md` | Release history. |
| `LICENSE` | MIT license. |

Keeping the hardware and behavior in `saltwatch-core.yaml` ensures that the
production and public installer builds use the same measurement, calibration,
and fault logic.

## Manual build secrets

Copy the example and replace every value:

```sh
cp secrets.yaml.example secrets.yaml
```

```yaml
wifi_ssid: "YOUR_WIFI_NAME"
wifi_password: "YOUR_WIFI_PASSWORD"
api_encryption_key: "YOUR_32_BYTE_BASE64_KEY"
```

Generate a compatible API key with:

```sh
openssl rand -base64 32
```

`secrets.yaml` is ignored by Git and must never be committed. OTA and the local
web interface intentionally do not have credentials.

## ESPHome version

SaltWatch 2.3.5 is validated with:

- ESPHome 2026.9.0
- ESP-IDF 5.5.5
- `m5stack-atom` board definition

Install the matching ESPHome CLI in an isolated environment if required:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "esphome==2026.9.0"
```

## Validate and compile

With `secrets.yaml` present:

```sh
esphome version
esphome config saltwatch.yaml
esphome compile saltwatch.yaml
esphome config saltwatch-webinstall.yaml
esphome compile saltwatch-webinstall.yaml
esphome config saltwatch-emulator.yaml
esphome compile saltwatch-emulator.yaml
python3 tests/test_logic.py
python3 tests/test_led.py
python3 tests/validate_yaml.py
```

The LED regression check requires a native C++ compiler (`c++`). It extracts
and executes the state-evaluation, LED-control, and blink-effect lambdas from
the firmware YAML, checking boundaries, failures, blink timing, and brightness
changes during both phases without rewriting those algorithms in Python.
Physical LED color, brightness, timing, and persistence still need the hardware
acceptance checklist.

Run the emulator interactively with `esphome run saltwatch-emulator.yaml`, then
add the ESPHome integration manually in Home Assistant using the development
computer's LAN address and API port `6053`. The process exposes adjustable test
controls and must remain running while Home Assistant uses the virtual device.

The production and browser-installer builds create:

```text
.esphome/build/saltwatch/build/firmware.factory.bin
.esphome/build/saltwatch/build/firmware.ota.bin
```

Use `firmware.factory.bin` only for USB flashing. Use `firmware.ota.bin` for the
managed updater or local web updater. Public OTA images are built from
`saltwatch-webinstall.yaml`, so they contain no per-installation credentials and
reuse the Wi-Fi and API encryption values provisioned on the device.

## Release validation

The GitHub Actions workflow creates temporary dummy secrets, validates both
entry points, and compiles both complete ESP-IDF firmware variants on a clean
runner. The workflow never uses production credentials.

Additional release checks include:

```sh
git diff --check
git status --short
git check-ignore secrets.yaml .esphome/build/saltwatch
rg -n "web_server|reboot_timeout|api:|ota:|password:" \
  saltwatch.yaml saltwatch-webinstall.yaml saltwatch-core.yaml
```

The published browser and OTA images are scanned for validation credentials,
checked for the ESP32 image header, and hashed before and after GitHub Pages
deployment. The manifest's OTA MD5 must match the published OTA image.

## Current v2.3.5 build results

| Build | RAM | Application flash | Result |
| --- | ---: | ---: | --- |
| Production | 29.4% | 56.9% | Passed |
| Browser installer | 29.5% | 57.5% | Passed |

The v2.3.5 hosted images are generated and verified as part of the release
process. Their final sizes and SHA-256 hashes are recorded below:

```text
Factory size: 1,120,400 bytes
Factory SHA-256: a8ab44f389854a1cbc21bb547268a29776c7c3a6bc6da59ff3df72ec5a46db67
OTA size: 1,054,864 bytes
OTA MD5: e8bff0269bae737c5cc9e37c693089fc
OTA SHA-256: 8e97eacb3f78013e72ad3473a7705024d0e45d0628575077597c34bcdc385d2a
```

## Configuration audit expectations

- `api.reboot_timeout: 0s`
- `wifi.reboot_timeout: 0s`
- production API encryption key supplied only through `secrets.yaml`
- no web-server authentication
- no native or web OTA password
- no MQTT
- no fallback access point or captive portal
- managed update checks use verified HTTPS and never install automatically
- no tracked `secrets.yaml`, build directory, compiled production firmware, or
  logs
