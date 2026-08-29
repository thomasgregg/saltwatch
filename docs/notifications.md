# Home Assistant notifications

[← Back to SaltWatch](../README.md)

Notifications are optional and separate from the device-native forecast.
SaltWatch measures and predicts normally without this automation.

The supplied Home Assistant blueprint can notify a phone or another `notify`
entity about:

- confirmed Low Salt;
- Sensor Fault;
- Calibration Required;
- Estimated Days Until Low Salt crossing a chosen advance-warning value; and
- optional recovery messages.

## Import the blueprint

1. Open the
   [SaltWatch blueprint import page](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fthomasgregg%2Fsaltwatch%2Fblob%2Fmain%2Fhome-assistant%2Fblueprints%2Fsaltwatch-notifications.yaml).
2. Select **Open link**, **Preview Blueprint**, then **Import Blueprint**.
3. Select **Create automation**.
4. Choose the phone or other notification target.
5. Verify the SaltWatch entities. The defaults match standard ESPHome entity
   IDs.
6. Choose the forecast warning, problem-confirmation delay, and whether recovery
   messages should be sent.
7. Save the automation.

No YAML editing, Home Assistant package, or restart is required. The advance
warning is sent after the confirmation delay when **Estimated Days Until Low
Salt** first becomes available inside the chosen window or crosses into it from
above. The blueprint verifies that measurement and calibration are healthy
before sending it. Repeated sensor updates inside the window do not produce
duplicate forecast notices. A return from `unavailable` inside the warning
window can notify again; this is intentional so a sensor outage cannot silently
hide a still-current refill warning.

Home Assistant keeps the confirmation timer in memory. Restarting Home
Assistant or reloading automations while that short timer is running cancels
it; the notification then waits for the condition to leave and enter its
trigger state again. This affects only optional notification delivery, not
SaltWatch measurement, fault handling, or device-native forecasting.

If direct import is unavailable, copy
[`home-assistant/blueprints/saltwatch-notifications.yaml`](../home-assistant/blueprints/saltwatch-notifications.yaml)
to `/config/blueprints/automation/saltwatch/notifications.yaml`, then reload
automations from **Settings → Automations & scenes → Blueprints**.

## Test safely

After saving, use Home Assistant's **Run actions** command to confirm the chosen
notification target works. This tests delivery only; it does not simulate each
trigger. Keep the default confirmation delay or increase it if temporary
maintenance states should not notify you.

The blueprint uses Home Assistant's standard `notify.send_message` action.
Choose any phone, browser, speaker, or notification service that Home Assistant
exposes as a `notify` entity.
