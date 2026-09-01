#!/usr/bin/env python3
"""Parse optional Home Assistant YAML and verify release metadata consistency."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


class TaggedSafeLoader(yaml.SafeLoader):
    pass


def tagged_value(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return {f"!{tag_suffix}": loader.construct_scalar(node)}
    if isinstance(node, yaml.SequenceNode):
        return {f"!{tag_suffix}": loader.construct_sequence(node)}
    return {f"!{tag_suffix}": loader.construct_mapping(node)}


TaggedSafeLoader.add_multi_constructor("!", tagged_value)


def load_yaml(path: str):
    return yaml.load(Path(path).read_text(), Loader=TaggedSafeLoader)


def run() -> None:
    installer_html = Path("docs/index.html").read_text()
    assert '<link rel="icon" type="image/svg+xml" href="favicon.svg">' in (
        installer_html
    )
    assert Path("docs/favicon.svg").exists()

    readme = Path("README.md").read_text()
    assert Path("docs/images/saltwatch-card.png").exists()
    assert 'src="docs/images/saltwatch-card.png"' in readme
    assert "https://github.com/thomasgregg/saltwatch-card" in readme

    # Forecasting is device-native; end users must not need a legacy package.
    assert not Path("home-assistant/saltwatch-prediction.yaml").exists()
    assert not Path("docs/home-assistant.md").exists()
    assert Path("docs/forecast.md").exists()
    assert Path("docs/notifications.md").exists()

    blueprint = load_yaml("home-assistant/blueprints/saltwatch-notifications.yaml")
    assert blueprint["blueprint"]["domain"] == "automation"
    assert blueprint["triggers"]
    assert blueprint["actions"]
    blueprint_inputs = blueprint["blueprint"]["input"]
    required_entities = {
        "low_salt_entity": ("binary_sensor", "problem"),
        "sensor_fault_entity": ("binary_sensor", "problem"),
        "calibration_required_entity": ("binary_sensor", "problem"),
        "salt_level_entity": ("sensor", None),
        "calibration_details_entity": ("text_sensor", None),
        "forecast_entity": ("sensor", None),
    }
    for input_name, (domain, device_class) in required_entities.items():
        entity_input = blueprint_inputs[input_name]
        assert "default" not in entity_input
        entity_filter = entity_input["selector"]["entity"]["filter"]
        assert entity_filter["integration"] == "esphome"
        assert entity_filter["domain"] == domain
        if device_class is not None:
            assert entity_filter["device_class"] == device_class
    assert blueprint["trigger_variables"] == {
        "forecast_entity_for_trigger": {"!input": "forecast_entity"},
        "forecast_notice_days_for_trigger": {"!input": "forecast_notice_days"},
        "low_salt_entity_for_trigger": {"!input": "low_salt_entity"},
        "sensor_fault_entity_for_trigger": {"!input": "sensor_fault_entity"},
        "calibration_required_entity_for_trigger": {
            "!input": "calibration_required_entity"
        },
        "salt_level_entity_for_trigger": {"!input": "salt_level_entity"},
    }
    forecast_trigger = next(
        item for item in blueprint["triggers"] if item.get("id") == "forecast"
    )
    assert forecast_trigger["trigger"] == "template"
    assert forecast_trigger["for"] == {"!input": "problem_delay"}
    assert "is_number(days)" in forecast_trigger["value_template"]
    assert "days | float > 0" in forecast_trigger["value_template"]
    assert "days | float <= forecast_notice_days_for_trigger | float" in (
        forecast_trigger["value_template"]
    )
    assert "is_state(low_salt_entity_for_trigger, 'off')" in (
        forecast_trigger["value_template"]
    )
    assert "is_state(sensor_fault_entity_for_trigger, 'off')" in (
        forecast_trigger["value_template"]
    )
    assert "is_state(calibration_required_entity_for_trigger, 'off')" in (
        forecast_trigger["value_template"]
    )
    assert "is_number(states(salt_level_entity_for_trigger))" in (
        forecast_trigger["value_template"]
    )

    blueprint_text = Path(
        "home-assistant/blueprints/saltwatch-notifications.yaml"
    ).read_text()
    assert "is_state(low_salt_entity, 'off')" in blueprint_text
    assert "is_state(sensor_fault_entity, 'off')" in blueprint_text
    assert "is_state(calibration_required_entity, 'off')" in blueprint_text
    assert "is_number(states(salt_level_entity))" in blueprint_text
    assert "is_number(states(forecast_entity))" in blueprint_text

    core = load_yaml("saltwatch-core.yaml")
    assert core["esphome"]["name_add_mac_suffix"] is True
    assert core["esp32"]["board"] == "m5stack-atom"
    assert core["esp32"]["framework"]["type"] == "esp-idf"
    assert core["i2c"] == {"sda": "GPIO26", "scl": "GPIO32", "scan": True}
    assert core["wifi"]["reboot_timeout"] == "0s"
    assert core["api"]["reboot_timeout"] == "0s"
    assert "auth" not in core["web_server"]
    assert all("password" not in item for item in core["ota"])
    assert core["time"][0]["platform"] == "homeassistant"

    tof = next(item for item in core["sensor"] if item.get("platform") == "vl53l0x")
    assert tof["address"] == 0x29
    assert tof["long_range"] is True
    assert tof["update_interval"] == "30s"
    filters = tof["filters"]
    assert [next(iter(item)) for item in filters] == [
        "multiply",
        "lambda",
        "median",
        "timeout",
    ]
    assert filters[2]["median"] == {
        "window_size": 5,
        "send_every": 1,
        "send_first_at": 1,
    }
    assert filters[3]["timeout"]["value"] == {"!lambda": "return NAN;"}

    script_ids = {item["id"] for item in core["script"]}
    assert {
        "forecast_reset_learning",
        "forecast_recalculate_model",
        "forecast_evaluate",
        "forecast_finalize_bucket",
        "forecast_record_refill",
    } <= script_ids

    sensors = {item.get("name"): item for item in core["sensor"]}
    assert sensors["Estimated Days Until Low Salt"]["update_interval"] == "never"
    text_sensors = {item.get("name"): item for item in core["text_sensor"]}
    assert text_sensors["Forecast Status"]["update_interval"] == "never"
    assert text_sensors["Forecast Details"]["update_interval"] == "never"
    assert text_sensors["Forecast Details"]["entity_category"] == "diagnostic"
    assert text_sensors["Forecast Confidence"]["disabled_by_default"] is True
    buttons = {item.get("name"): item for item in core["button"]}
    assert "Record Salt Refill" in buttons

    globals_by_id = {item["id"]: item for item in core["globals"]}
    for persistent_id in (
        "forecast_daily_levels",
        "forecast_daily_days",
        "forecast_daily_count",
        "forecast_historical_rate",
        "forecast_historical_variance",
        "forecast_completed_cycles",
        "forecast_refill_candidate",
        "forecast_cycle_low_level",
    ):
        assert globals_by_id[persistent_id]["restore_value"] is True
    assert globals_by_id["forecast_bucket_sum"]["restore_value"] is False
    assert globals_by_id["forecast_bucket_sample_count"]["restore_value"] is False

    core_text = Path("saltwatch-core.yaml").read_text()
    assert "forecast_bucket_sample_count) < 36" in core_text
    assert "forecast_daily_history_size: \"28\"" in core_text
    assert "forecast_minimum_decline_percent: \"2.0\"" in core_text
    assert "Discarded inconsistent restored forecast samples" in core_text
    for detail in (
        "Starting forecast",
        "Waiting for valid readings",
        "Waiting for first reading",
        "Waiting for date and time",
        "days collected",
        "Not enough salt usage yet",
        "Readings are too inconsistent",
        "Checking possible refill",
    ):
        assert detail in core_text
    assert "now.timezone_offset()" in core_text

    version = str(core["substitutions"]["project_version"])
    manifest = json.loads(Path("docs/manifest.json").read_text())
    assert manifest["version"] == version
    assert manifest["builds"][0]["parts"][0]["path"] == (
        f"saltwatch-{version}.factory.bin"
    )
    assert f"| Release | {version} |" in Path(
        "docs/technical-reference.md"
    ).read_text()
    assert f"Installer firmware {version}" in installer_html

    print("SaltWatch YAML and release metadata checks passed")


if __name__ == "__main__":
    run()
