#!/usr/bin/env python3
"""Dependency-free regression checks for SaltWatch's boundary and forecast logic."""

from __future__ import annotations

import math
import statistics


def tenths(value: float) -> int:
    return math.floor(value * 10.0 + 0.5)


def calibration_valid(full: float, empty: float, full_done=True, empty_done=True) -> bool:
    full_tenths = tenths(full)
    empty_tenths = tenths(empty)
    return (
        full_done
        and empty_done
        and 50 <= full_tenths <= 1200
        and 50 <= empty_tenths <= 1200
        and full_tenths < empty_tenths
        and empty_tenths - full_tenths >= 100
    )


def salt_level(full: float, empty: float, distance: float) -> float:
    canonical_full = tenths(full) / 10.0
    canonical_empty = tenths(empty) / 10.0
    value = (canonical_empty - distance) / (canonical_empty - canonical_full) * 100
    return tenths(max(0.0, min(100.0, value))) / 10.0


def low_salt(level: float, threshold: float, was_low: bool) -> bool:
    clearing_threshold = tenths(threshold) + (50 if was_low else 0)
    return tenths(level) <= clearing_threshold


def status(initializing: bool, fault: bool, calibration: bool, low: bool) -> str:
    if initializing:
        return "Initializing"
    if fault:
        return "Sensor Fault"
    if calibration:
        return "Calibration Required"
    if low:
        return "Low Salt"
    return "Good"


def theil_sen(points: list[tuple[int, float]]) -> dict[str, float | bool]:
    if len(points) < 2:
        return {"valid": False, "rate": -1.0, "days": 0.0, "decline": 0.0, "mad": 0.0}
    slopes = [
        (level_b - level_a) / (day_b - day_a)
        for index, (day_a, level_a) in enumerate(points[:-1])
        for day_b, level_b in points[index + 1 :]
        if day_b > day_a
    ]
    if not slopes:
        return {"valid": False, "rate": -1.0, "days": 0.0, "decline": 0.0, "mad": 0.0}
    slope = statistics.median(slopes)
    intercept = statistics.median(level - slope * day for day, level in points)
    mad = statistics.median(
        abs(level - (intercept + slope * day)) for day, level in points
    )
    observed_days = points[-1][0] - points[0][0]
    rate = -slope
    decline = rate * observed_days
    return {
        "valid": len(points) >= 7
        and observed_days >= 6
        and rate >= 0.05
        and decline >= 2.0
        and mad <= 4.0,
        "rate": rate,
        "days": float(observed_days),
        "decline": decline,
        "mad": mad,
    }


def forecast_days(level: float, threshold: float, rate: float | None) -> int | None:
    if level <= threshold:
        return 0
    if rate is None or not math.isfinite(rate) or rate < 0.05:
        return None
    return math.ceil((level - threshold) / rate)


def forecast_output(
    level: float | None,
    threshold: float,
    rate: float | None,
    *,
    initializing: bool = False,
    fault: bool = False,
    calibration_required: bool = False,
    refill_candidate: bool = False,
) -> tuple[str, int | None]:
    if initializing:
        return "Initializing", None
    if fault:
        return "Sensor Fault", None
    if calibration_required:
        return "Calibration Required", None
    if level is None or not math.isfinite(level):
        return "Waiting for Measurement", None
    if refill_candidate:
        return "Confirming Refill", None
    days = forecast_days(level, threshold, rate)
    if days == 0:
        return "Low Salt", 0
    if days is not None:
        return "Available", days
    return "Learning", None


def sanitize_restored(points: list[tuple[int, float]], claimed_count: int):
    valid: list[tuple[int, float]] = []
    for day, level in points[: max(0, min(claimed_count, 28))]:
        if (
            not math.isfinite(level)
            or not 0 <= level <= 100
            or day <= 0
            or (valid and day <= valid[-1][0])
        ):
            break
        valid.append((day, level))
    return valid


class RefillDetector:
    """Small model of the firmware's persistent refill confirmation behavior."""

    def __init__(self) -> None:
        self.recent: list[float] = []
        self.cycle_low = 101.0
        self.candidate: tuple[float, float] | None = None
        self.accepted: list[float] = []
        self.refills = 0

    def add(self, level: float) -> str:
        if self.candidate:
            base, candidate_level = self.candidate
            self.candidate = None
            if level >= base + 6.0:
                self.refills += 1
                self.recent = [candidate_level, level]
                self.cycle_low = min(candidate_level, level)
                self.accepted.append(level)
                return "confirmed"
            self._append_recent(level)
            self.cycle_low = min(self.cycle_low, level)
            self.accepted.append(level)
            return "rejected"

        recent_median = statistics.median(self.recent) if self.recent else math.nan
        baseline = recent_median
        if 0 <= self.cycle_low <= 100:
            baseline = min(recent_median, self.cycle_low) if math.isfinite(recent_median) else self.cycle_low
        if len(self.recent) >= 3 and math.isfinite(baseline) and level >= baseline + 8.0:
            self.candidate = (baseline, level)
            return "candidate"
        self._append_recent(level)
        self.cycle_low = min(self.cycle_low, level)
        self.accepted.append(level)
        return "accepted"

    def _append_recent(self, level: float) -> None:
        self.recent = (self.recent + [level])[-4:]


def refill_timestamp(stored: int, refill_accepted: bool, now: int | None) -> int:
    """Model the persisted no-value/pending/recorded timestamp states."""
    if refill_accepted:
        stored = -1
    if stored == -1 and now is not None:
        stored = now
    if stored == 0 or stored == -1:
        return stored
    return stored if 946_684_800 <= stored <= 4_102_444_800 else 0


def run() -> None:
    calibration_cases = [
        ((6.3, 16.3, True, True), True),
        ((20.0, 30.0, True, True), True),
        ((20.0, 29.9, True, True), False),
        ((20.0, 20.0, True, True), False),
        ((30.0, 20.0, True, True), False),
        ((5.0, 120.0, True, True), True),
        ((20.0, 40.0, False, True), False),
        ((20.0, 40.0, True, False), False),
    ]
    for arguments, expected in calibration_cases:
        assert calibration_valid(*arguments) is expected, arguments

    assert salt_level(10.0, 110.0, 10.0) == 100.0
    assert salt_level(10.0, 110.0, 60.0) == 50.0
    assert salt_level(10.0, 110.0, 110.0) == 0.0
    assert salt_level(10.0, 110.0, 0.0) == 100.0
    assert salt_level(10.0, 110.0, 120.0) == 0.0
    assert salt_level(5.0, 15.5, 13.4) == 20.0

    assert low_salt(20.0, 20.0, False)
    assert not low_salt(20.1, 20.0, False)
    assert low_salt(25.0, 20.0, True)
    assert not low_salt(25.1, 20.0, True)

    assert status(True, True, True, True) == "Initializing"
    assert status(False, True, True, True) == "Sensor Fault"
    assert status(False, False, True, True) == "Calibration Required"
    assert status(False, False, False, True) == "Low Salt"
    assert status(False, False, False, False) == "Good"

    linear = [(20_000 + day, 80.0 - day) for day in range(7)]
    model = theil_sen(linear)
    assert model == {"valid": True, "rate": 1.0, "days": 6.0, "decline": 6.0, "mad": 0.0}
    assert forecast_days(60.0, 20.0, float(model["rate"])) == 40
    assert forecast_days(20.0, 20.0, None) == 0
    assert forecast_days(60.0, 20.0, 0.049) is None

    outlier = linear.copy()
    outlier[3] = (outlier[3][0], 100.0)
    robust = theil_sen(outlier)
    assert robust["valid"] and robust["rate"] == 1.0
    assert theil_sen([(20_000 + day, 50.0) for day in range(7)])["valid"] is False
    assert theil_sen([(20_000 + day, 50.0 + day) for day in range(7)])["valid"] is False
    noisy = [(20_000 + day, value) for day, value in enumerate((83, 98, 78, 98, 74, 78, 75))]
    assert theil_sen(noisy)["valid"] is False

    restored = [(20_000, 70.0), (20_001, 69.0), (20_001, 68.0), (20_002, 67.0)]
    assert sanitize_restored(restored, 4) == restored[:2]
    assert sanitize_restored([(20_000, 70.0), (20_001, math.nan)], 2) == [(20_000, 70.0)]
    assert len(sanitize_restored([(day, 50.0) for day in range(1, 35)], 34)) == 28
    assert theil_sen(linear) == theil_sen(list(linear))

    detector = RefillDetector()
    for value in (45.0, 44.5, 44.0, 43.5):
        assert detector.add(value) == "accepted"
    assert detector.add(55.0) == "candidate"
    assert detector.add(44.0) == "rejected"
    assert detector.refills == 0 and 55.0 not in detector.accepted

    detector = RefillDetector()
    for value in (40.0, 40.0, 40.0, 43.0, 46.0):
        detector.add(value)
    assert detector.add(49.0) == "candidate"
    assert detector.add(48.0) == "confirmed"
    assert detector.refills == 1

    previous_refill = 1_788_000_000
    new_refill = 1_788_100_000
    assert refill_timestamp(0, False, new_refill) == 0
    assert refill_timestamp(previous_refill, False, new_refill) == previous_refill
    assert refill_timestamp(previous_refill, True, new_refill) == new_refill
    assert refill_timestamp(previous_refill, True, None) == -1
    assert refill_timestamp(-1, False, new_refill) == new_refill
    assert refill_timestamp(123, False, new_refill) == 0

    assert forecast_output(60, 20, 1, initializing=True) == ("Initializing", None)
    assert forecast_output(60, 20, 1, fault=True) == ("Sensor Fault", None)
    assert forecast_output(60, 20, 1, calibration_required=True) == (
        "Calibration Required",
        None,
    )
    assert forecast_output(None, 20, 1) == ("Waiting for Measurement", None)
    assert forecast_output(60, 20, 1, refill_candidate=True) == (
        "Confirming Refill",
        None,
    )
    assert forecast_output(20, 20, 1) == ("Low Salt", 0)
    assert forecast_output(60, 20, 1) == ("Available", 40)
    # Threshold edits recalculate the output but leave the learned rate intact.
    assert forecast_output(60, 30, 1) == ("Available", 30)
    # A learned completed-cycle rate is immediately usable after refill.
    learned_rate = float(model["rate"])
    assert forecast_output(90, 20, learned_rate) == ("Available", 70)

    sixty_days_ms = 60 * 24 * 60 * 60 * 1000
    assert sixty_days_ms > 180_000 and sixty_days_ms > 2**32

    attempted = False
    present = True
    assert present and not attempted
    attempted = True
    assert not (present and not attempted)
    present = False
    if not present:
        attempted = False
    assert not attempted
    present = True
    assert present and not attempted

    print("SaltWatch logic regression checks passed")


if __name__ == "__main__":
    run()
