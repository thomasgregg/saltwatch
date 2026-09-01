# Development and validation

[← Back to SaltWatch](../README.md)

## Repository structure

| Path | Purpose |
| --- | --- |
| `saltwatch-core.yaml` | Shared, credential-free hardware and monitoring configuration. |
| `saltwatch.yaml` | Production entry point with Wi-Fi credentials and encrypted API key. |
| `saltwatch-webinstall.yaml` | Credential-free browser-installer build and adoption metadata. |
| `secrets.yaml.example` | Required secret names for manual production builds. |
| `docs/index.html` | ESP Web Tools installer page. |
| `docs/manifest.json` | Versioned ESP Web Tools manifest. |
| `docs/*.factory.bin` | Published versioned browser-installer factory images. |
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

SaltWatch 2.0.0 is validated with:

- ESPHome 2026.8.1
- ESP-IDF 5.5.5
- `m5stack-atom` board definition

Install the matching ESPHome CLI in an isolated environment if required:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "esphome==2026.8.1"
```

## Validate and compile

With `secrets.yaml` present:

```sh
esphome version
esphome config saltwatch.yaml
esphome compile saltwatch.yaml
esphome config saltwatch-webinstall.yaml
esphome compile saltwatch-webinstall.yaml
python3 tests/test_logic.py
python3 tests/validate_yaml.py
```

The production build creates:

```text
.esphome/build/saltwatch/build/firmware.factory.bin
.esphome/build/saltwatch/build/firmware.ota.bin
```

Use `firmware.factory.bin` only for USB flashing and `firmware.ota.bin` for the
local web updater.

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

The published browser image is scanned for validation credentials, checked for
the ESP32 image header, and hashed before and after GitHub Pages deployment.

## Current v2.0.0 build results

| Build | RAM | Application flash | Result |
| --- | ---: | ---: | --- |
| Production | 27.5% | 49.2% | Passed |
| Browser installer | 27.6% | 49.7% | Passed |

The v2.0.0 hosted factory image is generated and verified as part of the
release process. Its final size and SHA-256 are recorded below:

```text
Size: 979,280 bytes
SHA-256: b00fbbb1625196d64b62b9fb3094b0b426b3031b8b5d548b04e63d2aaf4ee1ff
```

## Configuration audit expectations

- `api.reboot_timeout: 0s`
- `wifi.reboot_timeout: 0s`
- production API encryption key supplied only through `secrets.yaml`
- no web-server authentication
- no native or web OTA password
- no MQTT
- no fallback access point or captive portal
- no HTTP update checker or automatic remote download
- no tracked `secrets.yaml`, build directory, compiled production firmware, or
  logs
