#!/usr/bin/env python3
"""Bundle ESPHome's offline frontend with SaltWatch's unit-alignment fix."""

import gzip
from importlib.metadata import version
from pathlib import Path
import re

import esphome


def main():
    assert version("esphome") == "2026.9.0", "Use the validated ESPHome version"
    header = Path(esphome.__file__).parent / "components/web_server/server_index_v3.h"
    array = header.read_text().split("constexpr uint8_t INDEX_GZ[] PROGMEM = {", 1)[1].split("};", 1)[0]
    html = gzip.decompress(bytes(int(x, 16) for x in re.findall(r"0x([0-9a-f]{2})", array))).decode()
    script = re.search(r"<script\b[^>]*>(.*?)</script>", html, re.S).group(1)
    web = Path(__file__).resolve().parents[1] / "web"
    marker = "input[type=color]::-webkit-color-swatch-wrapper{padding:0!important}"
    assert script.count(marker) == 1, "Upstream layout changed; review the patch"
    css = (web / "layout.css").read_text()
    assert "`" not in css and "${" not in css
    script = script.replace(marker, marker + "\n" + css)
    target = web / "saltwatch-web.js"
    target.parent.mkdir(exist_ok=True)
    target.write_text("// ESPHome 2026.9.0 offline web UI; see README.md and LICENSE.\n" + script + "\n")
    print(f"Generated {target}")


if __name__ == "__main__":
    main()
