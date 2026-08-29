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
    prediction = load_yaml("home-assistant/saltwatch-prediction.yaml")
    assert isinstance(prediction["sensor"], list)
    assert isinstance(prediction["template"], list)

    blueprint = load_yaml("home-assistant/blueprints/saltwatch-notifications.yaml")
    assert blueprint["blueprint"]["domain"] == "automation"
    assert blueprint["triggers"]
    assert blueprint["actions"]

    core = load_yaml("saltwatch-core.yaml")
    assert core["esp32"]["board"] == "m5stack-atom"
    assert core["esp32"]["framework"]["type"] == "esp-idf"
    assert core["i2c"] == {"sda": "GPIO26", "scl": "GPIO32", "scan": True}
    assert core["wifi"]["reboot_timeout"] == "0s"
    assert core["api"]["reboot_timeout"] == "0s"
    assert "auth" not in core["web_server"]
    assert all("password" not in item for item in core["ota"])

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

    version = str(core["substitutions"]["project_version"])
    manifest = json.loads(Path("docs/manifest.json").read_text())
    assert manifest["version"] == version
    assert manifest["builds"][0]["parts"][0]["path"] == (
        f"saltwatch-{version}.factory.bin"
    )

    print("SaltWatch YAML and release metadata checks passed")


if __name__ == "__main__":
    run()
