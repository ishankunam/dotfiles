# SketchyBar browser sandbox

Open `index.html` in a browser. It works as a local file without a server.
Round 2 uses `desktop-preview.html` and `desktop.json` as its editable sources.
The original three-direction comparison remains in `preview.html` and the Round 1 branch.
All preview files belong outside the Stow packages.
Nothing in this folder starts SketchyBar or changes the installed configuration.

Round 1 compares Minimal, Floating, and Grouped with identical sample contents.
Round 2 compares Grouped with the original native configuration.
Space selection and battery details change only the browser preview.
Codex exposes design controls for height, text, spacing, corners, color, and sample states.

To regenerate the standalone page, use the Codex visualization renderer:

```sh
python3 previews/sketchybar/build.py
python3 "$VISUALIZE_SKILL/scripts/render.py" previews/sketchybar/inline.html previews/sketchybar/index.html --force
```

Set `VISUALIZE_SKILL` to the installed visualization skill directory.
The generated `index.html` includes its browser runtime and needs no installed skill to open.

The builder reads the reviewed shell configuration as text. It never executes that file.
It extracts the bar height, font sizes, Spaces, and group corners.
It embeds local assets so the preview needs no network connection.
This parser supports the current configuration format. It fails on an unsupported format.

## Desktop reference

The snapshot records the MSI G273 at 1920×1080 and the rotated DELL S2721QS at 1080×1920.
Both are external screens without a notch. The desktop uses dark appearance.
The observed app was ChatGPT. The battery was charged at 100% on AC power.
Values remain frozen. Volume is a labeled 50% sample.

The selected wallpaper is Monet's *Bassin d'Argenteuil*.
The original local image was missing. The user approved a reproduction from
[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Bassin_d%27Argenteuil_-_Google_Art_Project.jpg).
This asset has a public-domain designation on its source page.
The preview uses a centered cover crop because the desktop capture did not show the wallpaper.
The Hack Nerd Font subset comes from the installed font. Its embedded license is in `assets/HACK-LICENSE.txt`.

Bar detail keeps the items readable and reflows them in narrow browser windows.
Screen proportions uses the monitor's full dimensions and scales the bar with the screen.
The desktop background shows the wallpaper without application windows or the macOS menu bar.

The native candidate retains ten Mission Control Spaces and the existing yabai click command.
AeroSpace currently has four workspaces. Its optional snapshot view changes only the preview.
Connecting the native bar to AeroSpace is a separate setup round.
The battery popover is a browser inspection aid. The native candidate does not add a battery popover.

## Iteration history

Each design round has a branch, atomic commits, and a draft PR.
The first branch is `codex/sketchybar-round-1`, based on `master`.
Each later round starts from the preceding round and targets that branch.
Register the ordered PRs in GitHub's native stack after creating them.

```text
master → round-1 → round-2 → round-3
          PR 1      PR 2      PR 3
```

Only create a branch and PR when the corresponding round has concrete changes.
Keep native configuration candidates in an isolated worktree.
Do not stow, reload, install, or start services during browser design rounds.

Browser rendering checks visual layout and local interactions.
Native font rendering, blur, display positioning, event delivery, and commands require later macOS validation.
