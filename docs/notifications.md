# Home Assistant notifications

[← Back to SaltWatch](../README.md)

Notifications are optional and separate from the device-native measurement and
forecast logic. SaltWatch continues to measure, detect faults, and forecast
normally without this automation.

The supplied Home Assistant blueprint can notify a phone or another `notify`
entity about:

- confirmed Low Salt;
- Sensor Fault;
- Calibration Required;
- Estimated Days Until Low Salt crossing a chosen advance-warning value;
- optional recovery messages; and
- one optional reminder when Low Salt remains active continuously.

Notification titles automatically use the selected device's Home Assistant
name. This makes alerts distinguishable when multiple SaltWatch devices are
installed.

## Prioritized status alerts

The blueprint follows **Salt Status**, the same canonical priority state used by
the firmware and SaltWatch Card. Only the most useful active condition is
announced:

| Salt Status transition | Result |
| --- | --- |
| Any state → `Sensor Fault` | Sensor fault notification after the confirmation time. |
| Any state → `Calibration Required` | Calibration notification after the confirmation time. |
| Any state → `Low Salt` | Refill notification after the confirmation time. |
| `Low Salt` → `Good` | Optional low-salt recovery notification. |
| `Sensor Fault` → `Good` | Optional sensor recovery notification. |
| `Calibration Required` → `Good` | Optional calibration recovery notification. |
| Any state → `Initializing` | No notification. |

This prevents overlapping binary conditions from generating competing fault,
calibration, and low-salt messages. For example, recovery from Sensor Fault
directly into Low Salt produces the actionable refill message rather than a
generic recovery message.

## Import and configure the blueprint

1. Open the
   [SaltWatch blueprint import page](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fthomasgregg%2Fsaltwatch%2Fblob%2Fmain%2Fhome-assistant%2Fblueprints%2Fsaltwatch-notifications.yaml).
2. Select **Open link**, **Preview Blueprint**, then **Import Blueprint**.
3. Select **Create automation**.
4. Under **Required setup**, choose the notification target and these four
   entities from the same SaltWatch device:
   - Salt Status;
   - Salt Level;
   - Calibration Details; and
   - Estimated Days Until Low Salt.
5. Under **Notification options**, choose whether to send forecast warnings,
   recovery notifications, and one persistent-low reminder.
6. If forecast warnings are enabled, choose the advance-warning value.
7. If the reminder is enabled, choose how long Low Salt must remain active.
8. Save the automation.

No YAML editing, Home Assistant package, or restart is required. SaltWatch 2.2.0
uses a new blueprint input model and does not retain the obsolete individual
problem-entity inputs. Automations created from an earlier SaltWatch alerts
blueprint must be recreated with the four current SaltWatch entities.

The advance warning is sent after the confirmation time when **Estimated Days
Until Low Salt** first becomes available inside the chosen window or crosses
into it from above. It is sent only while Salt Status is `Good` and the current
Salt Level is numeric. Repeated forecast updates inside the window do not
produce duplicate warnings. A return from unavailable inside the warning
window can notify again so an outage cannot silently hide a current refill
warning.

The optional low-salt reminder is intentionally one-time, not recurring. It is
sent only if Salt Status remains continuously `Low Salt` for the configured
duration. Leaving Low Salt cancels the pending reminder; a later new Low Salt
event starts a fresh reminder period.

Home Assistant keeps `for` timers in memory. Restarting Home Assistant or
reloading automations while a confirmation or reminder timer is running resets
that timer. This affects only optional notification delivery, not SaltWatch
measurement, fault handling, or device-native forecasting.

If direct import is unavailable, copy
[`home-assistant/blueprints/saltwatch-notifications.yaml`](../home-assistant/blueprints/saltwatch-notifications.yaml)
to `/config/blueprints/automation/saltwatch/notifications.yaml`, then reload
automations from **Settings → Automations & scenes → Blueprints**.

## Test safely

After saving, use Home Assistant's **Run actions** command to confirm the chosen
notification target works. This tests delivery only; it does not simulate each
trigger. The SaltWatch emulator can exercise every Salt Status and forecast
combination without physical hardware.

Keep the default two-minute confirmation time or increase it if brief
maintenance states should not notify you. For quick emulator testing, shorten
both the confirmation time and low-salt reminder delay temporarily.

The blueprint uses Home Assistant's standard `notify.send_message` action.
Choose any phone, browser, speaker, or notification service that Home Assistant
exposes as a `notify` entity.
