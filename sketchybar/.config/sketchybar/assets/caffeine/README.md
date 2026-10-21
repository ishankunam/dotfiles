# Raycast mug

`mug.svg` is the unmodified `mug-filled.svg` from Raycast's Coffee extension:
https://github.com/raycast/extensions/blob/main/extensions/coffee/assets/mug-filled.svg

Upstream Git blob: `7e7b766adcd6ba88be36d8708c2139c32e9a2455`.
The upstream MIT license appears in `LICENSE`.

`mug.png` preserves the SVG's 24×24 view box at 36×36 pixels.
It uses a white foreground and transparent background.
SketchyBar displays it at scale `0.5`, matching the selected 18-point preview.
The bar reads this bundled PNG directly.

Regenerate it on macOS from the repository root:

```sh
swift sketchybar/.config/sketchybar/assets/caffeine/render.swift
```
