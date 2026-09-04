#!/usr/bin/env python3
"""Parse optional Home Assistant YAML and verify release metadata consistency."""

from __future__ import annotations

import hashlib
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
    blueprint_sections = blueprint["blueprint"]["input"]
    assert set(blueprint_sections) == {
        "required",
        "notification_options",
        "advanced",
    }
    assert blueprint_sections["advanced"]["collapsed"] is True
    for input_value in blueprint_sections["advanced"]["input"].values():
        assert "default" in input_value

    blueprint_inputs = blueprint_sections["required"]["input"]
    required_entities = {
        "salt_status_entity": ("sensor", None),
        "salt_level_entity": ("sensor", None),
        "calibration_details_entity": ("sensor", None),
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
        "salt_status_entity_for_trigger": {"!input": "salt_status_entity"},
        "salt_level_entity_for_trigger": {"!input": "salt_level_entity"},
    }
    status_triggers = {
        item["id"]: item
        for item in blueprint["triggers"]
        if item.get("id") in {
            "sensor_fault",
            "calibration_required",
            "low_salt",
            "recovered",
            "low_salt_reminder",
        }
    }
    assert status_triggers["sensor_fault"]["to"] == "Sensor Fault"
    assert status_triggers["calibration_required"]["to"] == (
        "Calibration Required"
    )
    assert status_triggers["low_salt"]["to"] == "Low Salt"
    assert status_triggers["recovered"]["to"] == "Good"
    assert status_triggers["low_salt_reminder"]["to"] == "Low Salt"
    assert status_triggers["low_salt_reminder"]["enabled"] == {
        "!input": "send_low_salt_reminder"
    }
    assert status_triggers["low_salt_reminder"]["for"] == {
        "!input": "low_salt_reminder_delay"
    }
    forecast_trigger = next(
        item for item in blueprint["triggers"] if item.get("id") == "forecast"
    )
    assert forecast_trigger["trigger"] == "template"
    assert forecast_trigger["enabled"] == {"!input": "send_forecast_notifications"}
    assert forecast_trigger["for"] == {"!input": "problem_delay"}
    assert "is_number(days)" in forecast_trigger["value_template"]
    assert "days | float > 0" in forecast_trigger["value_template"]
    assert "days | float <= forecast_notice_days_for_trigger | float" in (
        forecast_trigger["value_template"]
    )
    assert "is_state(salt_status_entity_for_trigger, 'Good')" in (
        forecast_trigger["value_template"]
    )
    assert "is_number(states(salt_level_entity_for_trigger))" in (
        forecast_trigger["value_template"]
    )

    blueprint_text = Path(
        "home-assistant/blueprints/saltwatch-notifications.yaml"
    ).read_text()
    assert "is_state(salt_status_entity, 'Good')" in blueprint_text
    assert "is_state(salt_status_entity, 'Low Salt')" in blueprint_text
    assert "is_number(states(salt_level_entity))" in blueprint_text
    assert "is_number(states(forecast_entity))" in blueprint_text
    assert "device_attr(selected_device, 'name_by_user')" in blueprint_text
    assert "trigger.from_state.state == 'Low Salt'" in blueprint_text
    assert "trigger.from_state.state == 'Sensor Fault'" in blueprint_text
    assert "trigger.from_state.state == 'Calibration Required'" in blueprint_text
    for removed_input in (
        "low_salt_entity",
        "sensor_fault_entity",
        "calibration_required_entity",
    ):
        assert removed_input not in blueprint_text

    core = load_yaml("saltwatch-core.yaml")
    assert core["esphome"]["name_add_mac_suffix"] is True
    assert core["esp32"]["board"] == "m5stack-atom"
    assert core["esp32"]["framework"]["type"] == "esp-idf"
    assert core["i2c"] == {"sda": "GPIO26", "scl": "GPIO32", "scan": True}
    assert core["wifi"]["reboot_timeout"] == "0s"
    assert core["api"]["reboot_timeout"] == "0s"
    assert "auth" not in core["web_server"]
    assert all("password" not in item for item in core["ota"])
    assert [item["platform"] for item in core["ota"]] == [
        "esphome",
        "web_server",
        "http_request",
    ]
    assert core["http_request"]["verify_ssl"] is True
    assert core["http_request"]["timeout"] == "10s"
    assert core["update"] == [
        {
            "platform": "http_request",
            "id": "saltwatch_firmware_update",
            "name": "SaltWatch Firmware Update",
            "icon": "mdi:update",
            "device_class": "firmware",
            "source": "https://thomasgregg.github.io/saltwatch/manifest.json",
            "update_interval": "6h",
            "web_server": {
                "sorting_group_id": "sorting_group_maintenance",
                "sorting_weight": 10,
            },
        }
    ]
    assert core["time"][0]["platform"] == "homeassistant"

    emulator = load_yaml("saltwatch-emulator.yaml")
    assert emulator["esphome"]["project"] == {
        "name": "saltwatch.salt-monitor",
        "version": "emulator",
    }
    assert emulator["host"]["mac_address"] == "06:53:41:4c:54:01"
    assert emulator["api"]["reboot_timeout"] == "0s"
    emulator_entities = {
        item["name"]
        for domain in ("number", "sensor", "text_sensor")
        for item in emulator[domain]
    }
    assert {
        "Salt Level",
        "Salt Status",
        "Low Salt Threshold",
        "Estimated Days Until Low Salt",
        "Forecast Status",
        "Forecast Details",
    } <= emulator_entities
    emulator_controls = {
        item["name"]
        for domain in ("number", "select")
        for item in emulator[domain]
    }
    assert {
        "Simulated Salt Level",
        "Simulated Salt Status",
        "Simulated Forecast Days",
        "Simulated Forecast Status",
        "Simulated Forecast Details",
    } <= emulator_controls

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
    assert sensors["Last Recorded Refill"] == {
        "platform": "template",
        "name": "Last Recorded Refill",
        "id": "last_recorded_refill",
        "web_server": {
            "sorting_group_id": "sorting_group_forecast",
            "sorting_weight": 50,
        },
        "icon": "mdi:calendar-refresh",
        "device_class": "timestamp",
        "accuracy_decimals": 0,
        "update_interval": "never",
    }
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
        "last_recorded_refill_timestamp",
    ):
        assert globals_by_id[persistent_id]["restore_value"] is True
    assert globals_by_id["forecast_bucket_sum"]["restore_value"] is False
    assert globals_by_id["forecast_bucket_sample_count"]["restore_value"] is False

    core_text = Path("saltwatch-core.yaml").read_text()
    assert core["esp32"]["framework"]["advanced"]["sram1_as_iram"] is True
    assert core["web_server"]["version"] == 3
    assert [group["name"] for group in core["web_server"]["sorting_groups"]] == [
        "Status",
        "Calibration",
        "Forecast and Refill",
        "Device Maintenance",
        "Diagnostics",
    ]
    expected_web_groups = {
        "sorting_group_status": {
            "Salt Status",
            "Salt Level",
            "Low Salt",
            "Calibration Required",
            "Sensor Fault",
        },
        "sorting_group_calibration": {
            "Distance to Salt",
            "Full Distance",
            "Set Current Distance as Full",
            "Empty Distance",
            "Set Current Distance as Empty",
            "Calibration Details",
        },
        "sorting_group_forecast": {
            "Estimated Days Until Low Salt",
            "Forecast Status",
            "Low Salt Threshold",
            "Record Salt Refill",
            "Last Recorded Refill",
            "Forecast Confidence",
            "Forecast Details",
        },
        "sorting_group_diagnostics": {
            "Last Valid Measurement Age",
            "WiFi Signal",
        },
        "sorting_group_maintenance": {
            "SaltWatch Firmware Update",
        },
    }
    actual_web_groups = {group_id: set() for group_id in expected_web_groups}
    for domain in (
        "number",
        "button",
        "sensor",
        "binary_sensor",
        "text_sensor",
        "update",
    ):
        for entity in core[domain]:
            if entity.get("name") and not entity.get("internal"):
                group_id = entity["web_server"]["sorting_group_id"]
                actual_web_groups[group_id].add(entity["name"])
    assert actual_web_groups == expected_web_groups
    expected_icons = {
        "SaltWatch Firmware Update": "mdi:update",
        "Full Distance": "mdi:arrow-up",
        "Empty Distance": "mdi:arrow-down",
        "Low Salt Threshold": "mdi:gauge",
        "Set Current Distance as Full": "mdi:target",
        "Set Current Distance as Empty": "mdi:target",
        "Record Salt Refill": "mdi:refresh",
        "Distance to Salt": "mdi:ruler",
        "Salt Level": "mdi:percent",
        "Estimated Days Until Low Salt": "mdi:calendar-clock",
        "Last Recorded Refill": "mdi:calendar-refresh",
        "WiFi Signal": "mdi:wifi",
        "Last Valid Measurement Age": "mdi:timer-outline",
        "Low Salt": "mdi:alert-outline",
        "Sensor Fault": "mdi:alert-octagon-outline",
        "Calibration Required": "mdi:tune",
        "Salt Status": "mdi:information-outline",
        "Calibration Details": "mdi:information-outline",
        "Forecast Status": "mdi:chart-timeline-variant",
        "Forecast Details": "mdi:information-outline",
        "Forecast Confidence": "mdi:chart-bell-curve-cumulative",
    }
    actual_icons = {}
    for domain in (
        "number",
        "button",
        "sensor",
        "binary_sensor",
        "text_sensor",
        "update",
    ):
        for entity in core[domain]:
            if entity.get("name") and not entity.get("internal"):
                actual_icons[entity["name"]] = entity.get("icon")
    assert actual_icons == expected_icons
    assert "forecast_bucket_sample_count) < 36" in core_text
    assert "forecast_daily_history_size: \"28\"" in core_text
    assert "forecast_minimum_decline_percent: \"2.0\"" in core_text
    assert "Discarded inconsistent restored forecast samples" in core_text
    assert "Discarded invalid restored refill timestamp" in core_text
    assert core_text.count("id(last_recorded_refill_timestamp) = -1;") == 2
    assert "on_time_sync" in core["time"][0]
    assert "Last Recorded Refill" in readme
    assert "Last Recorded Refill" in Path("docs/forecast.md").read_text()
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
    factory_path = Path("docs", manifest["builds"][0]["parts"][0]["path"])
    assert factory_path.exists()
    ota = manifest["builds"][0]["ota"]
    assert ota["path"] == f"saltwatch-{version}.ota.bin"
    ota_path = Path("docs", ota["path"])
    assert ota_path.exists()
    assert len(ota["md5"]) == 32
    assert ota["md5"] == hashlib.md5(ota_path.read_bytes()).hexdigest()
    assert ota["release_url"].endswith(f"/releases/tag/v{version}")
    assert ota["summary"]
    factory_bytes = factory_path.read_bytes()
    ota_bytes = ota_path.read_bytes()
    assert factory_bytes[0x1000] == 0xE9
    assert ota_bytes[0] == 0xE9
    assert len(ota_bytes) < 0x1C0000
    assert version.encode() in factory_bytes
    assert version.encode() in ota_bytes
    for forbidden in (
        b"VALIDATION_ONLY",
        b"validation-only-password",
        b"MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
    ):
        assert forbidden not in factory_bytes
        assert forbidden not in ota_bytes
    assert f"| Release | {version} |" in Path(
        "docs/technical-reference.md"
    ).read_text()
    assert f"Installer firmware {version}" in installer_html

    print("SaltWatch YAML and release metadata checks passed")


if __name__ == "__main__":
    run()
