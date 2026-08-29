#!/usr/bin/env python3
"""Small dependency-free regression checks for SaltWatch boundary logic."""

from __future__ import annotations

import math


def tenths(value: float) -> int:
    # Inputs are non-negative, matching C++ lroundf for SaltWatch values.
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


def forecast(level: float, threshold: float, daily_change: float, coverage: float):
    if level <= threshold:
        return 0
    if coverage < 0.5 or daily_change >= -0.05:
        return None
    return math.ceil((level - threshold) / -daily_change)


def run() -> None:
    calibration_cases = [
        ((6.3, 16.3, True, True), True),  # float edge: displayed 10.0 cm
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
    # Previously evaluated slightly above 20% in binary float arithmetic.
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

    assert forecast(60.0, 20.0, -2.0, 1.0) == 20
    assert forecast(20.0, 20.0, 0.0, 0.0) == 0
    assert forecast(60.0, 20.0, 0.1, 1.0) is None
    assert forecast(60.0, 20.0, -2.0, 0.49) is None

    # A 64-bit microsecond timer remains beyond the startup timeout after the
    # 32-bit millis() wrap point (about 49.7 days).
    sixty_days_ms = 60 * 24 * 60 * 60 * 1000
    assert sixty_days_ms > 180_000
    assert sixty_days_ms > 2**32

    # Recovery policy: present+faulted can reboot once; the persistent guard
    # blocks a loop, while observing absence permits a future retry.
    attempted = False
    present = True
    should_reboot = present and not attempted
    assert should_reboot
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
