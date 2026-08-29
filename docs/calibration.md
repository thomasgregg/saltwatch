# Calibration and operation

[← Back to SaltWatch](../README.md)

SaltWatch uses two measured distances: the normal full salt level and the
lowest useful salt level. Calibration is explicit so placeholder values can
never appear as a trustworthy percentage.

## Before calibration

- Finish the physical installation first.
- Return the lid to exactly the same resting position every time.
- Keep the ToF optical opening clean and uncovered.
- After moving the lid, refilling, or positioning a target, wait approximately
  two to three minutes for the five-value median to settle fully.
- Confirm **Sensor Fault** is off and **Distance to Salt** is available.

## Full calibration

1. Fill the tank to the normal desired full level.
2. Close the lid in its normal position.
3. Wait until **Distance to Salt** is stable.
4. Press **Set Current Distance as Full** in Home Assistant or the local web UI.
5. Confirm **Full Distance** changed to the displayed filtered distance.

The button refuses the capture if there is no valid filtered measurement or a
sensor fault is active.

## Empty calibration

1. Wait until the tank reaches the lowest useful salt level, or place a flat,
   representative target at that level.
2. Close the lid in its normal position.
3. Wait until **Distance to Salt** is stable.
4. Press **Set Current Distance as Empty**.
5. Confirm **Empty Distance** changed.
6. Confirm **Calibration Required** turns off.
7. Confirm **Salt Level** becomes available.

Empty Distance is the lowest **useful and reliably measurable** salt level. It
does not need to be the physical bottom of the tank.

## Manual calibration

You do not have to wait for the tank to become empty. Measure or determine the
two reference distances and edit **Full Distance** and **Empty Distance** in
Home Assistant or the local web interface.

Each number must be edited at least once because SaltWatch stores a separate
persistent completion flag for each calibration point. Numeric placeholders do
not count as completed calibration.

Changing either calibration distance after forecast learning has begun clears
the learned forecast. Old percentages are not comparable with percentages from
the new calibration. Changing only **Low Salt Threshold** keeps the learned
consumption rate and recalculates the predicted days immediately.

Valid calibration requires:

- Full Distance between 5.0 and 120.0 cm;
- Empty Distance between 5.0 and 120.0 cm;
- Full Distance strictly less than Empty Distance; and
- at least 10.0 cm between the two points.

SaltWatch never silently swaps reversed values. Invalid values keep
**Calibration Required** on and **Salt Level** unavailable until corrected.

## Percentage calculation

```text
Salt Level = (Empty Distance - Current Distance)
             / (Empty Distance - Full Distance) × 100
```

The result is clamped to 0–100%:

- Current Distance = Full Distance → 100%
- Current Distance = Empty Distance → 0%
- Current Distance halfway between them → 50%

Invalid or zero spans are rejected before calculation.

## Low-salt threshold

**Low Salt Threshold** defaults to 20% and can be adjusted from 5–50%.

- Low Salt turns on when Salt Level is less than or equal to the threshold.
- Equality counts as low.
- Once active, it clears only when Salt Level rises more than five percentage
  points above the threshold.
- Low Salt is always off when measurement, calibration, or Salt Level is
  unavailable.

For example, with a 20% threshold, Low Salt activates at 20% or below and clears
only above 25%.

## Understanding Salt Status

Salt Status summarizes the underlying entities in this priority order:

1. **Initializing** — waiting for the first valid measurements.
2. **Sensor Fault** — the sensor failed, timed out, or is out of range.
3. **Calibration Required** — measurement works, but calibration is incomplete
   or invalid.
4. **Low Salt** — measurement and calibration are valid and the level is low.
5. **Good** — measurement and calibration are valid and salt is above the
   threshold.

The status has no independent state machine, so it cannot contradict the
underlying fault, calibration, and low-salt entities.

## Routine care

- Disconnect power before pouring salt.
- Return the lid to the calibrated position before reconnecting power.
- Check the optical window for salt dust and condensation.
- Do not immerse or wash the ToF Unit; it is not waterproof.
- After a refill, allow two to three minutes for the displayed median to settle.

## After adding salt

A normal refill is detected automatically from a sustained rise in Salt Level.
**Forecast Status** may show `Confirming Refill` until the next valid six-hour
period. If SaltWatch learned a trustworthy earlier cycle, the estimate resumes
from that rate immediately after confirmation while the new cycle starts.

For a small top-up that does not raise Salt Level by roughly eight percentage
points, wait for the measurement to settle and press **Record Salt Refill**.
Do not press it when no salt was added: it deliberately closes the current
forecast cycle. See the [forecast guide](forecast.md) for full behavior.
