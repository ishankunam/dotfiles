# SketchyBar browser sandbox

Open `index.html` in a browser. It works as a local file without a server.
The current round uses `desktop-preview.html` and `desktop.json` as its editable sources.
The original three-direction comparison remains in `preview.html` and the Round 1 branch.
All preview files belong outside the Stow packages.
Nothing in this folder starts SketchyBar or changes the installed configuration.

Round 1 compares Minimal, Floating, and Grouped with identical sample contents.
Round 2 compared Grouped with the original native configuration.
Round 3 uses Grouped with AeroSpace workspaces, the enabled Focus, and 12-hour time.
Workspace selection and sample states change only the browser preview.
Codex exposes design controls for height, text, spacing, corners, color, and sample states.

To regenerate the standalone page, use the Codex visualization renderer:

```sh
python3 previews/sketchybar/build.py
python3 "$VISUALIZE_SKILL/scripts/render.py" previews/sketchybar/inline.html previews/sketchybar/index.html --force
```

Set `VISUALIZE_SKILL` to the installed visualization skill directory.
The generated `index.html` includes its browser runtime and needs no installed skill to open.

The builder reads the reviewed shell configuration as text. It never executes that file.
It extracts the bar height, font sizes, and group corners.
The desktop snapshot supplies workspace names. The native candidate queries AeroSpace.
It embeds local assets so the preview needs no network connection.
This parser supports the current configuration format. It fails on an unsupported format.

## Desktop reference

The snapshot records the MSI G273 at 1920×1080 and the rotated DELL S2721QS at 1080×1920.
Both are external screens without a notch. The desktop uses dark appearance.
The observed app was ChatGPT. AeroSpace reported workspaces 1, 2, 3, and 4.
Values remain frozen. The snapshot time appears as `9:12 PM` without a date.
macOS denied access to the enabled Focus. `Work` is a labeled design sample.
The design controls can show Focus off, Do Not Disturb, or an unavailable reading.

The selected wallpaper is Monet's *Bassin d'Argenteuil*.
The original local image was missing. The user approved a reproduction from
[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Bassin_d%27Argenteuil_-_Google_Art_Project.jpg).
This asset has a public-domain designation on its source page.
The preview uses a centered cover crop because the desktop capture did not show the wallpaper.
The Hack Nerd Font subset comes from the installed font. Its embedded license is in `assets/HACK-LICENSE.txt`.

Bar detail keeps the items readable and reflows them in narrow browser windows.
Screen proportions uses the monitor's full dimensions and scales the bar with the screen.
The desktop background shows the wallpaper without application windows or the macOS menu bar.

The native candidate lists only workspaces returned by `aerospace list-workspaces --all`.
This includes existing persistent workspaces, even when they have no windows.
It adds and removes items as that list changes. Clicks use `aerospace workspace`.
The candidate AeroSpace hook refreshes the bar after a workspace switch.
A two-second fallback catches workspace creation and deletion. A lock prevents overlapping refreshes.
If AeroSpace cannot be read, the bar retains its last workspace list.
The candidate uses Python 3, already available on this machine, with standard-library modules only.

The Focus reader polls the local database every ten seconds.
It uses a [private schema](https://github.com/eugenehp/macos-focus/blob/main/src/macos/database.rs), which Apple can change.
It displays the configured name to the left of the time and hides the label when Focus is off.
If the database is unreadable, it displays `Focus unavailable` instead of claiming Focus is off.
It never writes the Focus database or changes macOS privacy permissions.
Battery and volume items are absent. The clock uses `h:mm AM/PM` without a date.

## Iteration history

Each design round has a branch, atomic commits, and a draft PR.
The first branch is `codex/sketchybar-round-1`, based on `master`.
Each later round starts from the preceding round and targets that branch.
Register the ordered PRs in GitHub's native stack after creating them.

```text
master → round-1 → round-2 → round-3
```

Only create a branch and PR when the corresponding round has concrete changes.
Keep native configuration candidates in an isolated worktree.
Do not stow, reload, install, or start services during browser design rounds.

Browser rendering checks visual layout and local interactions.
Native font rendering, blur, display positioning, event delivery, and commands require later macOS validation.
Run plugin fixture checks with `python3 previews/sketchybar/test_plugins.py`.
These checks intercept commands and never contact the installed bar or change Focus.
