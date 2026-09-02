# Salt forecast

[← Back to SaltWatch](../README.md)

SaltWatch estimates when the tank will reach its configured **Low Salt
Threshold**. The predictor runs on the ATOM Lite and appears in Home Assistant
automatically—there is no package to copy, helper to create, or Home Assistant
restart to perform.

## What you will see

- **Estimated Days Until Low Salt** — the rounded number of days until the
  warning threshold, or unavailable when a responsible estimate cannot be made.
- **Forecast Status** — explains whether the forecast is learning, available,
  confirming a refill, or blocked by measurement/calibration.
- **Record Salt Refill** — tells the predictor about a small or unusual refill
  that automatic detection may not recognize.
- **Last Recorded Refill** — remembers the latest automatically confirmed or
  manually recorded refill.
- **Forecast Confidence** — an optional diagnostic entity, disabled by default.

The forecast targets the warning threshold, not physical empty. If Salt Level
is already at or below the threshold, the estimate is `0 days`.

## No setup is required

Complete normal SaltWatch calibration and leave the device connected to Home
Assistant. Home Assistant supplies the clock, but does not calculate or store
the model. After the first successful clock synchronization, temporary Home
Assistant or network outages do not stop measurement; a learned forecast also
survives device restarts.

**Forecast Status** initially shows `Learning`. A first estimate needs at least
seven trustworthy daily values spanning six days, at least two percentage
points of modeled decline, and a sufficiently consistent trend. Slow salt use
can therefore take longer than one week. This is intentional: displaying no
estimate is safer than turning a nearly flat signal into a dramatic date.

## How the model works

1. SaltWatch samples only a fresh, valid Salt Level every five minutes.
2. A six-hour value is accepted only if at least half its expected samples were
   valid. Faults, restarts, and long gaps cannot masquerade as consumption.
3. A daily value requires at least two accepted six-hour periods.
4. The device retains at most 28 daily aggregates—not raw distance history.
5. A robust Theil–Sen trend reduces the influence of a shifted lid, uneven salt
   surface, or isolated bad daily value.
6. A median-residual quality check suppresses forecasts from excessively noisy
   history.
7. After completed usage cycles exist, their learned rates are blended with the
   current cycle. Recent evidence gradually receives more weight.

Calibration and the sensor-fault pipeline remain independent of forecasting.
Forecast code cannot make a failed measurement look healthy or keep Salt Level
available during a fault.

## Refill behavior

SaltWatch treats a sustained rise of roughly eight percentage points as a
possible refill. It waits for the next valid six-hour value before confirming
the event. The first raised value is excluded from the downward trend while
confirmation is pending:

- if the rise remains at least six points above the prior level, the refill is
  confirmed and a new usage cycle starts;
- if it falls back, the candidate is discarded as a temporary surface change;
- gradual refills are compared with the lowest accepted level in the current
  cycle, so several smaller rises can still be recognized.
- a candidate expires once its accepted confirmation bucket would be more than
  one calendar day later, rather than remaining in `Confirming Refill`
  indefinitely.

Only a confirmed candidate updates **Last Recorded Refill**. The initial rise,
an expired candidate, or a rise rejected as temporary surface movement leaves
the previous timestamp untouched. The recorded time is the confirmation time,
because that is when SaltWatch has enough evidence to classify the change as a
refill.

When the previous cycle contained a trustworthy trend, SaltWatch learns that
rate before resetting the current cycle. The post-refill forecast can therefore
resume immediately from learned past consumption instead of disappearing for
another week. As the new cycle develops, its evidence is blended in.

Automatic recognition cannot distinguish every physical event. A persistent
salt bridge, moving the sensor, or changing the lid position can resemble a
refill, while a very small top-up may stay below the detection threshold. After
adding a small amount of salt, wait for Salt Level to settle and press **Record
Salt Refill**. The button preserves any trustworthy completed-cycle rate and
starts clean current-cycle learning. It refuses the action unless the current
Salt Level, sensor health, and calibration are all valid.

An accepted manual action also updates **Last Recorded Refill**. If Home
Assistant has not yet supplied a valid clock, recording the refill and starting
the new forecast cycle still succeed. The timestamp remains unavailable until
the next successful clock synchronization and is then set to that synchronization
time. Rejected button actions do not change the timestamp.

The timestamp is stored across normal restarts and firmware updates. It is not
cleared by calibration or low-threshold changes because it describes a recorded
physical event rather than forecast training data. It does not participate in
refill detection, trend learning, confidence, or the estimated-days calculation.

## Forecast Status reference

| State | Meaning | Forecast Details example |
| --- | --- | --- |
| `Initializing` | SaltWatch is still waiting for its first valid measurement. | `Starting forecast` |
| `Sensor Fault` | Forecast is unavailable because measurement is not trustworthy. | `Waiting for valid readings` |
| `Calibration Required` | Complete or correct calibration first. | `Calibration required` |
| `Waiting for Measurement` | A current valid Salt Level is not available. | `Waiting for first reading` |
| `Waiting for Time` | Home Assistant has not yet supplied a valid clock and no learned model can be used. | `Waiting for date and time` |
| `Learning` | More trustworthy daily evidence is required. | `4 of 7 days collected` |
| `Insufficient Change` | Enough time exists, but the decline is too small or inconsistent to forecast responsibly. | `Not enough salt usage yet` or `Readings are too inconsistent` |
| `Confirming Refill` | A possible refill is awaiting a second six-hour value. | `Checking possible refill` |
| `Available` | Estimated Days Until Low Salt is published. | `Based on 18 days of data` or `Based on previous refill cycle` |
| `Low Salt` | The threshold has been reached; the estimate is 0 days. | `Low threshold reached` |

**Forecast Details** adds a short explanation for the current state. During
learning it reports progress such as `4 of 7 days collected`; it also
distinguishes insufficient salt usage from readings that are too inconsistent.
SaltWatch Card displays this explanation only while the numeric forecast is
unavailable, keeping the normal available state uncluttered.

Any sensor fault, invalid calibration, missing current level, or pending refill
confirmation makes the numeric estimate unavailable. Changing Full Distance or
Empty Distance clears learned forecast data because old percentages are no
longer comparable. Changing only Low Salt Threshold recalculates the estimate
immediately without discarding the learned consumption rate.

## Confidence and limitations

Enable **Forecast Confidence** from the SaltWatch device page if you want the
diagnostic. `Low`, `Medium`, and `High` describe evidence quality, not a
guaranteed date. High confidence requires a long, smooth current trend plus
substantial within-cycle change or a completed learned cycle.

The estimate assumes recent consumption is informative. Guests, travel,
regeneration settings, tank shape, bridging, and optical surface changes can
all alter the real date. Use the forecast to plan a check or purchase—not as a
substitute for inspecting the tank before it reaches the warning threshold.
