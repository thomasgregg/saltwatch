# Hardware installation and acceptance

[← Back to SaltWatch](../README.md)

## Hardware list

- M5Stack ATOM Lite, model/SKU **C008**
- M5Stack ToF Unit, model/SKU **U010**, containing a VL53L0X
- Included HY2.0-4P Grove cable
- USB-A-to-USB-C **data** cable
- 5 V USB power supply
- 3M Dual Lock SJ3550 for removable mounting
- Rubber cable grommet sized for the lid opening

## Electrical configuration

| Connection | Value |
| --- | --- |
| ESPHome board | `m5stack-atom` |
| Framework | ESP-IDF |
| Grove SDA | GPIO26 |
| Grove SCL | GPIO32 |
| VL53L0X address | `0x29` |
| Sensor mode | Long range |
| Accepted installed range | 5–120 cm |

Official sources:

- [M5Stack ATOM Lite C008](https://docs.m5stack.com/en/core/ATOM%20Lite)
- [M5Stack ATOM Lite programming](https://docs.m5stack.com/en/uiflow2/atomlite/program)
- [M5Stack ToF Unit U010](https://docs.m5stack.com/en/unit/TOF)
- [ESPHome VL53L0X component](https://esphome.io/components/sensor/vl53l0x/)

## Physical installation

1. Disconnect power before drilling, mounting, connecting cables, or pouring
   salt.
2. Mount the ToF Unit inside the lid, pointing vertically down at the salt.
3. Do not place it directly above the normal salt-pouring location.
4. Keep the optical opening completely uncovered.
5. Mount the ATOM Lite outside the tank.
6. Connect the ToF Unit to the ATOM Lite through the included Grove cable.
7. Protect the cable opening with a rubber grommet and remove sharp edges first.
8. Use removable 3M Dual Lock SJ3550 so the sensor can be removed for cleaning.
9. Clean and dry both mounting surfaces before applying adhesive, then follow
   the adhesive manufacturer's cure instructions.
10. Route and strain-relieve the cable so opening the lid cannot pull either
    connector.
11. Do not immerse or wash the ToF Unit; it is not waterproof.
12. Check the optical window for salt dust and the lid for condensation.
13. Ensure the lid returns to exactly the same position after every opening.

Changing the lid angle or resting position changes every distance and therefore
changes the physical meaning of the calibration.

## Hardware acceptance checklist

Do not rely on low-salt alerts until this checklist passes.

### Measurement stability

1. Verify **Distance to Salt** appears.
2. Observe a stationary target for at least one hour.
3. Confirm the median-filtered value is reasonably stable.

### Blocked-sensor behavior

4. Cover the sensor.
5. Confirm Distance to Salt becomes unavailable within three minutes.
6. Confirm **Sensor Fault** turns on.
7. Confirm **Salt Level** becomes unavailable.
8. Uncover the sensor and confirm automatic recovery.

### Disconnection behavior

9. Disconnect the Grove cable after a valid reading.
10. Confirm the stale distance disappears within three minutes.
11. Reconnect the cable and confirm recovery. One automatic recovery reboot is
    expected when the I²C device reappears.

### Calibration and level behavior

12. Perform full calibration.
13. Perform empty calibration or enter the value manually.
14. Confirm **Calibration Required** turns off.
15. Check 100%, 50%, and 0% using known distances if practical.
16. Test **Low Salt** at exactly the configured threshold.
17. Raise the simulated level and confirm Low Salt clears only above threshold
    plus five percentage points.

### Persistence and resilience

18. Restart SaltWatch and confirm calibration survives.
19. Turn Home Assistant off for at least 30 minutes.
20. Confirm SaltWatch continues measuring and does not repeatedly restart.

### Local interface and updates

21. Open the local web interface without credentials and confirm the SaltWatch
    entities are visible.
22. Confirm the device is reachable only from the intended trusted network.
23. Test one web update using `firmware.bin` or `firmware.ota.bin`.
24. Observe the installed system for several days before relying on alerts.

