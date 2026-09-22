# Offline device web interface

`saltwatch-web.js` is the offline ESPHome v3 frontend bundled with ESPHome
2026.9.0, with the CSS corrections in `layout.css`: centered unit labels,
unbroken number inputs, and a narrow-screen layout that puts number controls
below their full labels. No controls or device behavior are changed.

The firmware embeds this script through `web_server.js_include` and serves it
locally at `/0.js`. The external script URL is disabled, so viewing the device
interface does not require internet access. ESPHome's `local` option is false
because its stock all-in-one page bypasses custom script includes.

Regenerate using the validated ESPHome environment:

```sh
python tools/build_web_ui.py
```

After changing the ESPHome version, review the patch and verify the slider,
unit labels, number inputs, and switches at desktop and narrow widths.

Upstream: <https://github.com/esphome/esphome-webserver> (MIT; see `LICENSE`).
Third-party license notices are retained in the generated script.
