# Home Assistant forecast and notifications

[← Back to SaltWatch](../README.md)

SaltWatch's essential distance, percentage, calibration, and fault behavior
runs on the device. The additions on this page are optional Home Assistant
features: SaltWatch keeps measuring normally if they are not installed or if
Home Assistant is offline.

## Estimated Days Until Low Salt

The optional package creates **SaltWatch Estimated Days Until Low Salt**. It
answers the practical question “approximately when should I expect to refill?”
using the current Salt Level, configured Low Salt Threshold, and recent rate of
decrease.

It intentionally predicts the warning threshold rather than physical empty.
SaltWatch's 0% point means the lowest useful and reliably measurable calibrated
level, which may not be the bottom of the tank.

The package:

- smooths Salt Level over six hours;
- retains one representative value per hour;
- measures the change across a rolling 14-day window;
- requires at least seven days of covered history;
- reports 0 days when Salt Level has already reached the threshold; and
- becomes unavailable during a sensor fault, invalid calibration, insufficient
  history, or a flat/rising trend.

Home Assistant's [Statistics integration](https://www.home-assistant.io/integrations/statistics/)
reloads recent samples from Recorder after a restart. No history is written to
the ATOM Lite. The smoothing and hourly sampling use the standard
[Filter integration](https://www.home-assistant.io/integrations/filter/).

### Install the prediction package

1. In Home Assistant, install or open **File editor** or **Studio Code Server**.
2. If packages are not already enabled, add this once to `/config/configuration.yaml`:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

   If a `homeassistant:` section already exists, add only the `packages:` line
   beneath it; do not create a second section.

3. Create `/config/packages` if it does not exist.
4. Copy
   [`home-assistant/saltwatch-prediction.yaml`](../home-assistant/saltwatch-prediction.yaml)
   into `/config/packages/saltwatch_prediction.yaml`.
5. Open **Settings → System → Repairs → three-dot menu → Check configuration**.
6. Correct any reported entity IDs before continuing. The package expects:

   ```text
   sensor.saltwatch_salt_level
   number.saltwatch_low_salt_threshold
   binary_sensor.saltwatch_sensor_fault
   binary_sensor.saltwatch_calibration_required
   ```

7. Restart Home Assistant.
8. Confirm **SaltWatch Forecast Level**, **SaltWatch 14-Day Level Change Per
   Second**, and **SaltWatch Estimated Days Until Low Salt** appear.

The estimate normally remains unavailable for the first seven days. That is a
safety behavior, not a fault.

### Interpreting the estimate

The result is a trend estimate, not a promise. Water consumption, tank shape,
salt bridging, refills, and changes to calibration can all change the slope.
After a refill the 14-day trend may be flat or rising, so the estimate normally
disappears until a meaningful downward trend develops again. Always inspect the
tank before relying on the predicted date.

## Notification blueprint

The blueprint can send notifications for:

- Low Salt after a short confirmation delay;
- Sensor Fault after a short confirmation delay;
- Calibration Required after a short confirmation delay;
- the forecast crossing a configurable number of days; and
- optional recovery messages when a problem clears.

### Import and configure the blueprint

1. Open the
   [SaltWatch blueprint import page](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fthomasgregg%2Fsaltwatch%2Fblob%2Fmain%2Fhome-assistant%2Fblueprints%2Fsaltwatch-notifications.yaml).
2. Select **Open link** and then **Preview Blueprint**.
3. Select **Import Blueprint**.
4. Select **Create automation**.
5. Choose the phone or other `notify` entity that should receive messages.
6. Verify the SaltWatch entities. The defaults work when Home Assistant kept
   the standard ESPHome entity IDs.
7. Set the desired forecast warning, confirmation time, and recovery-message
   preference.
8. Save the automation.

If direct import is unavailable, copy
[`home-assistant/blueprints/saltwatch-notifications.yaml`](../home-assistant/blueprints/saltwatch-notifications.yaml)
to `/config/blueprints/automation/saltwatch/notifications.yaml`, then open
**Settings → Automations & scenes → Blueprints** and reload automations.

The forecast trigger is harmless when the prediction package is not installed;
the three core problem notifications continue to work.

The blueprint targets a Home Assistant `notify` entity through the standard
[`notify.send_message` action](https://www.home-assistant.io/integrations/notify/).
