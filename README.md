# SaltWatch

SaltWatch is a small ESPHome project for reliable salt-level monitoring in a
water-softener brine tank. It reports lid-to-salt distance, an estimate from
0–100%, low-salt state, calibration health, and sensor health to Home Assistant.

Version: **1.2.0**

ESPHome project identifier: **`saltwatch.salt-monitor`**

ESPHome node: **`saltwatch`**

## Scope assessment

Version 1 includes only the measurement and safety path needed for dependable
monitoring:

| Included | Reason |
| --- | --- |
| VL53L0X measurement every 30 seconds in long-range mode | Matches the ordered sensor and avoids unnecessary fast polling. |
| 5–120 cm raw validation before a five-value median | Keeps impossible values out of the smoothing window while handling an uneven tablet surface. |
| Independent initial/normal watchdogs and explicit `NaN` publication | Prevents Home Assistant from retaining a stale valid distance after failure. |
| Full/empty calibration values, persistent completion flags, and capture buttons | Makes calibration easy without treating placeholder numbers as real calibration. |
| Calibration validation and clamped percentage calculation | Prevents reversed, too-small, out-of-range, or zero spans from producing a plausible but wrong level. |
| Low threshold with five-percentage-point hysteresis | Equality is consistently low and the warning does not chatter around the threshold. |
| Fault, calibration, low-salt, and priority status entities | Makes every unavailable or invalid state explicit. |
| Wi-Fi, encrypted native API, protected native OTA, and basic logging | Supports secure Home Assistant operation and troubleshooting without a cloud dependency. |
| Authenticated local web UI and manual web OTA | Provides browser visibility and firmware upload without automatic downloads or an unauthenticated update endpoint. |
| Optional USB web installer | Makes the first flash and Wi-Fi setup easier without embedding credentials. |

The reviewed reference project at commit
`734488f147f760a33626fafc236bbdc0187b28dd` was used only to understand the
hardware and failure modes. Its implementation was not copied. The public
distance in SaltWatch is separate from the raw/filter path: rejected values
increment health counters, and the last filter in the valid path is a timeout
that emits `NaN`. A separate boot watchdog covers the case where the timeout
filter never receives its first value.

## Deliberately excluded from version 1

These are possible later enhancements, not version 1 features: automatic
regeneration detection, last regeneration, overdue warnings, salt-consumption
history, historical buffers, remaining-days prediction, usage trends, fast
polling, MQTT, automatic HTTP update checks, automatic remote firmware
downloads, cloud services, RGB status behavior, a custom Home Assistant
dashboard, notification automations, tank-height configuration, and extra
configuration or diagnostic entities. They were excluded to keep firmware,
state, flash use, security exposure, and failure behavior easy to understand.

## Hardware and verified electrical configuration

- M5Stack ATOM Lite, model/SKU **C008**
- M5Stack ToF Unit, model/SKU **U010**, containing a **VL53L0X**
- Included HY2.0-4P Grove cable
- USB-A-to-USB-C **data** cable for the first flash
- 5 V USB power supply for permanent operation
- 3M Dual Lock SJ3550 for removable mounting
- Rubber cable grommet sized for the tank-lid opening

The official M5Stack ATOM Lite documentation identifies the Grove connector as
GND, 5 V, GPIO26, and GPIO32. The official ToF Unit documentation identifies
the Grove signals as GND, 5 V, SDA, and SCL and the VL53L0X I²C address as
`0x29`. SaltWatch therefore uses SDA **GPIO26**, SCL **GPIO32**, address
**`0x29`**, the PlatformIO board definition **`m5stack-atom`**, and ESP-IDF.

Official sources:

- [M5Stack ATOM Lite C008](https://docs.m5stack.com/en/core/ATOM%20Lite)
- [M5Stack ToF Unit U010](https://docs.m5stack.com/en/unit/TOF)
- [ESPHome VL53L0X component](https://esphome.io/components/sensor/vl53l0x/)
- [ESPHome sensor timeout filter](https://esphome.io/components/sensor/filter/timeout/)
- [ESPHome native API](https://esphome.io/components/api/)
- [ESPHome OTA](https://esphome.io/components/ota/esphome/)
- [ESPHome web server](https://esphome.io/components/web_server/)
- [ESPHome web-server OTA](https://esphome.io/components/ota/web_server/)

The U010 is not waterproof. Its official headline range is wider, but M5Stack
notes that normal conditions are approximately 120 cm unless long-range mode
and favorable optical conditions are used. SaltWatch deliberately accepts only
5–120 cm for predictable installed behavior.

## Repository files

- `saltwatch.yaml` — production entry point with encrypted API and protected OTA
- `saltwatch-core.yaml` — shared, secret-free device and monitoring configuration
- `saltwatch-webinstall.yaml` — public bootstrap build configuration
- `docs/` — static ESP Web Tools installer, manifest, and versioned factory image
- `.github/workflows/esphome.yml` — pinned configuration and compile checks
- `secrets.yaml.example` — required secret names, with no real credentials
- `.gitignore` — excludes secrets, local builds, logs, and editor files; only the
  versioned installer factory image is deliberately tracked
- `README.md` — installation, calibration, behavior, and acceptance tests
- `CHANGELOG.md` — release history
- `LICENSE` — MIT license

The split between the small production/bootstrap entry points and
`saltwatch-core.yaml` keeps both builds on exactly the same measurement and
calibration logic.

## Web installer

For the easiest first flash, use the hosted installer:

**[Install SaltWatch](https://thomasgregg.github.io/saltwatch/)**

Requirements: a desktop version of Chrome or Microsoft Edge, the ATOM Lite,
and a USB-A-to-USB-C **data** cable. Safari and Firefox do not currently expose
the required Web Serial interface.

1. Close serial monitors, ESPHome upload sessions, M5Burner, and any other
   program that may be using the serial port.
2. Connect the ATOM Lite directly to the computer with the USB data cable. The
   C008 automatically enters download/programming mode when connected over
   USB; no button combination is normally required.
3. If the browser shows no serial port, unplug and reconnect the ATOM Lite, try
   another known-good data cable or direct USB port, and reload the page. If it
   is still absent, install the FTDI VCP driver from M5Stack's
   [official ATOM Lite programming instructions](https://docs.m5stack.com/en/uiflow2/atomlite/program).
4. Open the installer link, select **Connect and install**, and choose the ATOM
   Lite serial port.
5. Approve erasing the device when prompted, then install SaltWatch.
6. Enter the 2.4 GHz Wi-Fi credentials in the provisioning dialog. The ATOM
   Lite cannot join a 5 GHz-only network.
7. Open ESPHome Device Builder in Home Assistant. SaltWatch should appear as
   available to **Adopt** because the bootstrap advertises the official project
   configuration. Adopt it. Device Builder generates a unique API encryption
   key in the adopted YAML.
8. Before the first wireless update, add `ota_password`,
   `web_server_username`, and `web_server_password` to the Device Builder
   `secrets.yaml`, then add these blocks to the adopted SaltWatch YAML:

   ```yaml
   web_server:
     port: 80
     version: 2
     local: true
     compression: gzip
     log: false
     auth:
       type: digest
       username: !secret web_server_username
       password: !secret web_server_password

   ota:
     - platform: esphome
       id: saltwatch_ota
       password: !secret ota_password
     - platform: web_server
       id: saltwatch_web_ota
   ```

9. Confirm the adopted YAML contains `api:` → `encryption:` → `key:`. Choose
   **Install → Wirelessly**. This replaces the bootstrap with the adopted,
   encrypted configuration and enables both protected update methods.
10. Add the discovered SaltWatch ESPHome device under **Settings → Devices &
   services** in Home Assistant, using the API encryption key if prompted.
11. Open `http://<device-name>.local/` or the device IP address and sign in with
   the web username and password from `secrets.yaml`.

The public bootstrap image contains no Wi-Fi password, API encryption key, or
OTA password. It advertises encryption support, but communication is not
encrypted until Device Builder installs the generated key; OTA is initially
passwordless so that first adopted build can be installed. Perform the setup on
a trusted local network, adopt it immediately, and complete step 9. The
bootstrap intentionally has no on-device web UI because a public factory image
cannot contain private login credentials. The protected UI appears after the
adopted production configuration is installed. The hosted installer itself is
only a static page that writes firmware over the local USB connection.

## Create `secrets.yaml`

Copy the example next to `saltwatch.yaml`:

```sh
cp secrets.yaml.example secrets.yaml
```

Replace every placeholder. Generate the required 32-byte Base64 API key with:

```sh
openssl rand -base64 32
```

Generate a separate strong password for OTA, for example:

```sh
openssl rand -base64 24
```

Generate another independent password for the web interface, and choose a
non-default web username. Do not reuse either credential. Do not commit
`secrets.yaml`. SaltWatch does not enable a fallback access point or captive
portal.

## Manual first installation

1. Install or open **ESPHome Device Builder** in Home Assistant.
2. In the Device Builder configuration directory (normally `/config/esphome`),
   create a `saltwatch` directory and copy `saltwatch.yaml`,
   `saltwatch-core.yaml`, and `secrets.yaml` into it. The complete path is normally
   `/config/esphome/saltwatch/saltwatch.yaml`.
3. Edit `secrets.yaml` as described above. The API encryption key must be the
   output of `openssl rand -base64 32` or the key generator in ESPHome Device
   Builder.
4. Connect the ATOM Lite to the computer or Home Assistant host with a USB-A to
   USB-C **data cable**. A charge-only cable will not work.
5. In ESPHome Device Builder, open `saltwatch.yaml`, choose **Install**, then
   **Plug into this computer** (or the serial/USB option shown for your setup).
   Select the ATOM Lite serial port and complete the initial USB flash.
6. Power the ATOM Lite from the 5 V supply. Home Assistant should discover
   `SaltWatch`; go to **Settings → Devices & services**, open the discovered
   ESPHome device, and add it. Enter the API encryption key from `secrets.yaml`
   if Home Assistant asks for it.
7. Future firmware changes can be installed from ESPHome Device Builder over
   the network using **Install → Wirelessly**. The OTA password remains in
   `secrets.yaml`. The authenticated local web updater described below is also
   available; no automatic remote-download mechanism is enabled.

Command-line equivalents, run from the directory containing the YAML, are:

```sh
esphome config saltwatch.yaml
esphome run saltwatch.yaml --device /dev/ttyUSB0
```

On macOS the device often appears as `/dev/cu.usbserial-*`; select the actual
port reported by your system rather than using `/dev/ttyUSB0` literally.

## Local web interface and firmware updater

After the production configuration is installed, browse to
`http://saltwatch.local/` or the device's IP address and authenticate with
`web_server_username` and `web_server_password`. If Device Builder adopted the
bootstrap with a MAC suffix, use the adopted device name shown in Device Builder
instead of `saltwatch`.

The self-contained interface shows the public SaltWatch entities and permits
the same number/button changes exposed to Home Assistant. Browser log streaming
is disabled. To update manually:

1. Compile the new production configuration in ESPHome Device Builder.
2. Download the OTA firmware image, normally named `firmware.bin` or
   `firmware.ota.bin`.
3. Sign in to the SaltWatch web interface and find **OTA Update**.
4. Select the OTA image and start the update.
5. Keep power connected until the upload finishes and SaltWatch reboots.

Never upload `firmware.factory.bin` through the device web page; factory images
are only for USB flashing. The web interface uses HTTP Digest authentication,
which keeps the password itself off the network, but the page and entity data
are still not encrypted. Keep SaltWatch on a trusted, preferably segmented LAN
and never expose port 80 to the internet. Native ESPHome OTA remains the
preferred command-line/Device Builder update path.

## Home Assistant entities

Entity IDs are generated from the stable node and entity names below. Do not
rename the node or entities in future releases if you want Home Assistant to
retain the same entity registry entries.

| Entity | Type | Behavior |
| --- | --- | --- |
| Distance to Salt | Sensor, cm | One-decimal, five-valid-sample moving median; larger means less salt; becomes unavailable on fault/timeout. |
| Salt Level | Sensor, % | Clamped 0–100%; unavailable on fault, incomplete/invalid calibration, or unavailable distance. |
| Full Distance | Number, cm | Persistent 5–120 cm value; manual edits complete full calibration. |
| Empty Distance | Number, cm | Persistent 5–120 cm value; manual edits complete empty calibration. |
| Low Salt Threshold | Number, % | Persistent 5–50% threshold; default 20%. |
| Set Current Distance as Full | Button | Captures the current valid filtered distance. |
| Set Current Distance as Empty | Button | Captures the current valid filtered distance. |
| Low Salt | Problem binary sensor | On at or below threshold; clears only above threshold + 5 points. |
| Sensor Fault | Problem binary sensor | Detects startup timeout, no valid readings, repeated invalid values, range failures, and measurement timeout. |
| Calibration Required | Problem binary sensor | On until both persistent flags and all range/order/span checks pass. |
| Salt Status | Text sensor | `Initializing`, `Sensor Fault`, `Calibration Required`, `Low Salt`, or `Good`, in that exact priority. |
| WiFi Signal | Diagnostic sensor, dBm | Standard ESPHome Wi-Fi signal diagnostic. |

On a first flash, Full Distance and Empty Distance contain placeholders (20.0
and 100.0 cm), but their completion flags are false. Therefore Calibration
Required is on, Salt Level is unavailable, and Low Salt is off. A placeholder
never counts as calibration.

## Physical installation

1. Disconnect power before drilling, mounting, connecting cables, or pouring salt.
2. Mount the ToF Unit inside the tank lid, pointing vertically down at the salt.
3. Do not place it directly above the normal salt-pouring location.
4. Keep the optical opening completely uncovered.
5. Mount the ATOM Lite outside the tank.
6. Connect the ToF Unit to the ATOM Lite through the included Grove cable.
7. Protect the cable opening with a rubber grommet; remove sharp edges first.
8. Use removable 3M Dual Lock SJ3550 so the sensor can be removed for cleaning.
9. Clean and dry both mounting surfaces before applying the adhesive and follow
   the adhesive manufacturer's cure instructions.
10. Route and strain-relieve the cable so opening the lid cannot pull a connector.
11. Remember that the ToF Unit is **not waterproof**. Do not immerse or wash it.
12. Regularly inspect the optical window for salt dust and the lid for condensation.
13. Ensure the lid returns to exactly the same position after every opening.

Power should remain disconnected while salt is poured. Close the lid normally,
then reconnect power. Changing the lid angle or resting position changes every
distance and invalidates the physical meaning of the calibration.

## Calibration

The filtered value starts with the first valid reading, then fills a five-value
window. After moving the lid, changing a target, or refilling, wait approximately
two to three minutes for the displayed median to settle fully.

### Full calibration

1. Fill the tank to its normal desired full level.
2. Close the lid in its normal position.
3. Wait until **Distance to Salt** is stable.
4. Press **Set Current Distance as Full**.
5. Confirm **Full Distance** changed to the current filtered distance.

### Empty calibration

1. Wait until the tank reaches the lowest useful salt level, or place a flat,
   representative target at that level.
2. Close the lid in its normal position.
3. Wait until **Distance to Salt** is stable.
4. Press **Set Current Distance as Empty**.
5. Confirm **Empty Distance** changed.
6. Confirm **Calibration Required** turns off.
7. Confirm **Salt Level** becomes available.

Empty Distance means the lowest **useful and reliably measurable** level, not
necessarily the physical bottom. The sensor must still see a repeatable target,
and the value must be no more than 120 cm.

### Manual calibration

If you do not want to wait for the tank to empty, measure or determine both
values independently and edit **Full Distance** and **Empty Distance** in Home
Assistant. Each manual edit sets its own persistent completion flag. Both must
be edited at least once. The rules are:

- both values must be between 5.0 and 120.0 cm;
- Full Distance must be strictly less than Empty Distance; and
- Empty Distance minus Full Distance must be at least 10.0 cm.

SaltWatch never swaps incorrect values silently. Invalid calibration keeps
Calibration Required on and Salt Level unavailable until corrected.

The percentage is:

```text
(Empty Distance - Current Distance) / (Empty Distance - Full Distance) × 100
```

The result is clamped to 0–100%. Full equals 100%, empty equals 0%, and the
midpoint equals 50%. A zero or invalid span is never divided.

## Failure behavior and recovery

Only finite readings from 5–120 cm enter the median. Three consecutive invalid
readings activate Sensor Fault; a 180-second last-valid watchdog catches missing
updates. The post-median ESPHome timeout is the final filter, so its `NaN` cannot
be swallowed. A separate 180-second startup watchdog handles a sensor that has
never produced a valid value, because ESPHome's standard timeout begins only
after its first input.

When a fault activates, Distance to Salt and Salt Level publish `NaN`, Low Salt
turns off, and Salt Status becomes Sensor Fault. A new valid reading clears the
fault automatically. If the Grove cable was physically absent and address
`0x29` later reappears, SaltWatch performs one safe reboot to reinitialize the
VL53L0X driver; calibration persists across that reboot.

The API and Wi-Fi reboot timeouts are both disabled. Home Assistant or Wi-Fi can
remain offline without clearing calibration or causing periodic 15-minute
restarts; measurement continues locally.

## Hardware acceptance checklist

Do not rely on alerts until this checklist passes:

1. Verify that Distance to Salt appears.
2. Observe the stationary measurement for at least one hour.
3. Confirm the median-filtered value is reasonably stable.
4. Cover the sensor.
5. Confirm Distance to Salt becomes unavailable within the timeout.
6. Confirm Sensor Fault turns on.
7. Confirm Salt Level becomes unavailable.
8. Uncover the sensor and confirm recovery.
9. Disconnect the Grove cable after a valid reading.
10. Confirm the stale value disappears.
11. Reconnect and confirm recovery (one automatic recovery reboot is expected).
12. Perform full calibration.
13. Perform empty calibration or enter the value manually.
14. Confirm Calibration Required turns off.
15. Check 100%, 50%, and 0% using known distances if practical.
16. Test Low Salt at exactly the threshold.
17. Test hysteresis when the level rises again; it must clear only above threshold + 5 percentage points.
18. Restart SaltWatch and confirm calibration survives.
19. Turn Home Assistant off for at least 30 minutes.
20. Confirm SaltWatch does not repeatedly restart.
21. Open the local web interface and confirm incorrect credentials are rejected.
22. Confirm the authenticated web interface shows the SaltWatch entities.
23. Test one web update with a valid `firmware.bin` or `firmware.ota.bin` image.
24. Observe the installed system for several days before relying on alerts.

## Validation

With `secrets.yaml` present, run:

```sh
esphome version
esphome config saltwatch.yaml
esphome compile saltwatch.yaml
esphome config saltwatch-webinstall.yaml
esphome compile saltwatch-webinstall.yaml
git status --short
git check-ignore secrets.yaml .esphome/build/saltwatch
rg -n "web_server|reboot_timeout|api:|ota:|password:" \
  saltwatch.yaml saltwatch-webinstall.yaml saltwatch-core.yaml
```

Both release configurations were configuration-validated and compiled for
`m5stack-atom` with ESPHome 2026.8.1 and ESP-IDF 5.5.5. The web manifest uses
the ESP32 merged factory image at flash offset 0, as required by ESP Web Tools.

## Remaining limitations

- The VL53L0X is optical: dust, condensation, direct infrared interference,
  dark/angled surfaces, and salt geometry can reduce range or stability.
- The estimate assumes a linear relationship between measured height and the
  chosen full/empty points. Tank shape and brine voids can make the percentage
  an approximation rather than a mass measurement.
- The moving median contains up to five valid readings, so it intentionally
  takes roughly two to three minutes to represent a completely changed surface.
- Removing sensor power mid-transaction requires the documented one-time reboot
  after the device reappears; calibration survives it.
- Low Salt is a Home Assistant entity, but version 1 intentionally supplies no
  notification automation or dashboard.
- The one-click installer is a bootstrap. Its short unencrypted adoption window
  is closed only after the production configuration is installed.
- The local web UI uses HTTP rather than HTTPS. Digest authentication keeps the
  password itself off the network, but does not encrypt entity data on the LAN.
