#!/usr/bin/env python3
"""Bundle ESPHome's offline frontend with SaltWatch's layout adjustments."""

import gzip
from importlib.metadata import version
from pathlib import Path
import re

import esphome


def replace_once(script, old, new):
    assert script.count(old) == 1, "Upstream frontend changed; review the patch"
    return script.replace(old, new)


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
    script = replace_once(script, marker, marker + "\n" + css)

    # Keep the native multipart upload form owned by esp-app, but project it
    # immediately after the maintenance group through a named slot. Lit retains
    # the form and selected file when sensor readings rerender.
    script = replace_once(
        script,
        '<esp-entity-table .scheme="${this.scheme}"></esp-entity-table>${this.renderOta()}',
        '<esp-entity-table .scheme="${this.scheme}">${this.renderOta()}</esp-entity-table>',
    )
    script = replace_once(
        script,
        '</div>`)}</div>`)} ${this.renderShowAll()}',
        '</div>`)}</div>${e===`Device Maintenance`?D`<slot name="saltwatch-maintenance"></slot>`:k}'
        '`)} ${this.renderShowAll()}',
    )
    script = replace_once(
        script,
        'D`<div class="tab-header">OTA Update</div><form method="POST" '
        'action="${hr()}/update" enctype="multipart/form-data" class="tab-container">'
        '<input class="btn" type="file" name="update" accept="application/octet-stream"> '
        '<input class="btn" type="submit" value="Update"></form>`',
        'D`<div slot="saltwatch-maintenance">'
        '<div class="tab-header">Firmware Upload</div>'
        '<form class="tab-container manual-update" '
        'method="POST" action="${hr()}/update" enctype="multipart/form-data">'
        '<input id="manual-firmware-file" class="btn" type="file" name="update" '
        'aria-label="OTA firmware file (.bin)" accept=".bin,application/octet-stream" required> '
        '<input class="btn" type="submit" value="Update"></form></div>`',
    )
    maintenance_css = (web / "maintenance.css").read_text()
    assert "`" not in maintenance_css and "${" not in maintenance_css
    script = replace_once(script, 'form .btn{margin-right:0}',
                          'form .btn{margin-right:0}\n' + maintenance_css)
    target = web / "saltwatch-web.js"
    target.parent.mkdir(exist_ok=True)
    target.write_text("// ESPHome 2026.9.0 offline web UI; see README.md and LICENSE.\n" + script + "\n")
    print(f"Generated {target}")


if __name__ == "__main__":
    main()
