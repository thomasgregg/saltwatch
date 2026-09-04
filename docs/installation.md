# Installation and updates

[← Back to SaltWatch](../README.md)

The browser installer is the recommended path. It installs a ready-to-provision
factory image over USB, collects Wi-Fi credentials, and makes SaltWatch
available for adoption in ESPHome Device Builder.

## Browser installation

### What you need

- M5Stack ATOM Lite C008
- USB **data** cable: USB-C for the ATOM Lite, with USB-C or USB-A to match the
  computer
- desktop Chrome or Microsoft Edge
- 2.4 GHz Wi-Fi credentials
- ESPHome Device Builder in Home Assistant for encrypted API adoption and later
  managed updates

### Install SaltWatch

1. Close M5Burner, serial monitors, ESPHome upload sessions, and any other
   application that may be using the serial port.
2. Open the [SaltWatch web installer](https://thomasgregg.github.io/saltwatch/).
3. Connect the ATOM Lite directly to the computer using the USB data cable.
   The C008 normally enters download/programming mode automatically; no button
   combination is normally required.
4. Select **Connect and install SaltWatch**.
5. Choose the port named **M5Stack**, **USB Serial**, or similar.
6. Approve erasing the device and wait for installation to finish.
7. Enter the 2.4 GHz Wi-Fi network and password when prompted.

After provisioning, the installer reports the device address. The local
interface is available immediately at that address without a login.

### If no serial port appears

1. Confirm the cable supports data; some USB cables supply power only.
2. Disconnect and reconnect the ATOM Lite.
3. Use a direct computer USB port instead of a hub.
4. Close any software that may have claimed the serial port.
5. Reload the installer in desktop Chrome or Microsoft Edge.
6. If the device still does not appear, install the FTDI VCP driver from
   [M5Stack's ATOM Lite programming instructions](https://docs.m5stack.com/en/uiflow2/atomlite/program).

## Adopt in ESPHome Device Builder

Adoption turns the public bootstrap into a configuration owned by your Home
Assistant installation and adds an encrypted native API key.

1. When the browser installer reports that the device is connected, select
   **Add to Home Assistant**. This provisions and stores the unique encrypted
   API key on the device.
2. Open **ESPHome Device Builder** in Home Assistant.
3. Find the discovered SaltWatch device and select **Adopt** or **Take Control**.
4. Keep the generated API encryption configuration.
5. Select **Install → Wirelessly** to install the adopted configuration.

If SaltWatch was added directly under **Settings → Devices & services**, that is
equivalent to the first step. Enter the generated API key if prompted.

The web UI and all OTA components are part of the shared SaltWatch package, so
adoption does not require extra OTA/web secrets or copied YAML blocks.

SaltWatch always uses a MAC-suffixed hostname such as
`saltwatch-a1b2c3.local`. Use the hostname shown by ESPHome when opening the
local interface.

## Managed firmware updates

SaltWatch checks its official GitHub Pages release manifest every six hours. A
**Firmware Update** entity appears in Home Assistant and under **Device
Maintenance** in the local interface. When a newer version is available, review
the release information and explicitly approve the installation. SaltWatch does
not install updates automatically.

The managed updater installs the canonical SaltWatch firmware and preserves
Wi-Fi credentials, API encryption, calibration, and forecast data. If you have
added custom YAML overrides, continue using Device Builder so those changes are
included in the compiled firmware.

The first release containing managed updates must still be installed through
Device Builder or a manual OTA upload. Later releases will be detected by the
Firmware Update entity.

## Updates through Device Builder

For normal updates:

1. Open SaltWatch in ESPHome Device Builder.
2. Select **Install → Wirelessly**.
3. Wait for compilation, upload, and reboot to complete.

ESPHome's native OTA path is passwordless in SaltWatch. The encrypted native
API is separate and remains protected after adoption.

## Updates through the local web interface

1. In Device Builder, select **Install → Manual download** and obtain the OTA
   image, normally `firmware.bin` or `firmware.ota.bin`.
2. Open the MAC-suffixed address shown by ESPHome, such as
   `http://saltwatch-a1b2c3.local/`, or use the device IP.
3. Find **OTA Update**.
4. Select the OTA image and start the upload.
5. Keep power connected until SaltWatch reboots.

Never upload `firmware.factory.bin` through the local web updater. A factory
image is a merged USB-flashing image; the web updater requires an OTA image.

## Manual source installation in Device Builder

Use this path only if you do not want the hosted installer.

1. Download or clone the repository.
2. Copy `saltwatch.yaml` and `saltwatch-core.yaml` into the same Device Builder
   configuration directory.
3. Copy `secrets.yaml.example` to `secrets.yaml` and set:

   ```yaml
   wifi_ssid: "YOUR_WIFI_NAME"
   wifi_password: "YOUR_WIFI_PASSWORD"
   api_encryption_key: "YOUR_32_BYTE_BASE64_KEY"
   ```

4. Generate the API key with Device Builder or:

   ```sh
   openssl rand -base64 32
   ```

5. Open `saltwatch.yaml`, select **Install**, and choose the USB option offered
   for your computer or Home Assistant host.
6. Select the ATOM Lite serial port and complete the flash.

Do not commit `secrets.yaml`.

## Command-line installation

With ESPHome 2026.8.2 installed and `secrets.yaml` present:

```sh
esphome config saltwatch.yaml
esphome run saltwatch.yaml --device /dev/ttyUSB0
```

On macOS, the serial port commonly resembles `/dev/cu.usbserial-*`. After the
first flash, use the MAC-suffixed hostname shown by ESPHome for a wireless
update:

```sh
esphome run saltwatch.yaml --device saltwatch-a1b2c3.local
```

Replace `a1b2c3` with the suffix assigned to your device.

## Network access warning

The local HTTP interface, its controls, web OTA, and native ESPHome OTA have no
authentication. Anyone with network access to SaltWatch can change calibration,
press exposed buttons, or replace the firmware. Keep the device on a trusted,
preferably isolated IoT network, never expose its ports to the internet, and
restrict access with firewall rules where possible.
