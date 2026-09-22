# Offline device web interface

`saltwatch-web.js` is the offline ESPHome v3 frontend bundled with ESPHome
2026.9.0, with the CSS corrections in `layout.css`: centered unit labels,
unbroken number inputs, and a narrow-screen layout that puts number controls
below their full labels.

The native OTA upload form is placed in a collapsed **Manual update** row in
**Device Maintenance**, below the version and official release updater.
`maintenance.css` styles this row. A named slot keeps the form owned by the
original component, preserving its selected file and expanded state when live
readings refresh. Uploads still use ESPHome's native multipart POST endpoint,
including when the interface is served under a URL prefix. The row is shown
only when web OTA is enabled.

The firmware embeds this script through `web_server.js_include` and serves it
locally at `/0.js`. The external script URL is disabled, so viewing the device
interface does not require internet access. ESPHome's `local` option is false
because its stock all-in-one page bypasses custom script includes.

Regenerate using the validated ESPHome environment:

```sh
python tools/build_web_ui.py
```

After changing the ESPHome version, review the patch and verify the slider,
unit labels, number inputs, switches, and the manual upload at desktop and
narrow widths. The generator fails if an upstream patch location changes.

Upstream: <https://github.com/esphome/esphome-webserver> (MIT; see `LICENSE`).
Third-party license notices are retained in the generated script.
