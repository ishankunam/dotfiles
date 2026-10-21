# SketchyBar browser sandbox

Open `index.html` in a browser. It works as a local file without a server.
The current round uses `desktop-preview.html` and `desktop.json` as its editable sources.
All preview files belong outside the Stow packages.
Nothing in this folder starts SketchyBar or changes the installed configuration.

The preview shows the selected Dracula Glass design. Earlier rounds explored other directions. See the merged `codex/sketchybar-round-*` PRs.
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
macOS denied access to the enabled Focus. The Work logo is a labeled design sample.
The design controls can show Focus off, Do Not Disturb, or an unavailable reading.

The selected wallpaper is Monet's *Bassin d'Argenteuil*.
The original local image was missing. The user approved a reproduction from
[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Bassin_d%27Argenteuil_-_Google_Art_Project.jpg).
This asset has a public-domain designation on its source page.
The preview uses a centered cover crop because the desktop capture did not show the wallpaper.
IBM Plex Mono Medium uses the complete, unmodified installed TTF file.
Its license is in `assets/IBM-PLEX-LICENSE.txt`.
The [IBM Plex license](https://github.com/IBM/plex/blob/master/LICENSE.txt) accompanies the font asset.

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

The Focus item subscribes to `focus_changed` and has `update_freq=0`.
It reads `~/Library/Caches/sketchybar-focus/state.json` at startup, after waking, and when that event arrives.
The bar never launches Shortcuts. It does not access the protected Focus database.
The shared **SketchyBar Focus** shortcut publishes the state when any configured Focus turns on or off.
This recipe is its reproducible source. Shortcuts export requires an unavailable iCloud sign-in on this machine.

In Shortcuts settings, enable **Advanced → Allow Running Scripts**.
This permits scripting actions across Shortcuts. The user approved this setting for this integration.
Create or edit **SketchyBar Focus** with the following actions:

1. Add **Get Current Focus**.
2. Add **If Current Focus has any value**.
3. Inside the If branch, add **Convert Image**. Select **Current Focus**, then its **Icon** property, and choose **PNG** as the format.
4. Add **Run Shell Script** after conversion. Use **Converted Image** as input, **to stdin**, and leave **Run as Administrator** off.

```sh
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
python3 "$HOME/.config/sketchybar/plugins/focus.py" --stdin
```

5. Inside **Otherwise**, add **Run Shell Script** with no input and **Run as Administrator** off:

```sh
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
python3 "$HOME/.config/sketchybar/plugins/focus.py" --off
```

6. End the If block. Do not add **Stop and Output**, **Show Result**, or a notification action.
7. Add a Focus automation trigger for each mode. Choose **Is Turned On or Off**, enable **Automation**, and disable **Notify**.

The installed editor supports multiple triggers on this one shortcut, joined by **or**.
The current modes are **Do Not Disturb**, **silence**, **in class**, **work**, and **sleep**.
Add another trigger when adding a new Focus mode.
Apple documents [Mac automations](https://support.apple.com/guide/shortcuts-mac/apdfbdbd7123/mac).
SketchyBar documents [custom events](https://felixkratz.github.io/SketchyBar/config/events).

The publisher saves the icon and state before sending `sketchybar --trigger focus_changed`.
It receives PNG bytes through standard input. It does not assume image arguments are file paths.
It emits no shell output. If the bar is stopped, the saved state remains available for its next startup.
A successful off branch clears the active image reference. Old cached icons cannot become the current state.
Missing or invalid state and invalid PNG input display a question mark instead of claiming Focus is off.
An unavailable publication includes a short error reason in `state.json` for diagnosis.
The state survives bar restarts. Deleting the cache requires running the shortcut again to initialize it.
Startup and wake refresh the saved state without executing a shortcut.
If macOS misses an automation, the bar retains the last published state until another trigger or manual shortcut run.
The shortcut reads the current Focus on both transitions, so an old mode's off event can show the newly enabled mode.
The AppKit renderer crops transparent padding, preserves the symbol shape, and tints it white in a cached 36×36 PNG.
It uses the installed Swift toolchain and standard AppKit. It creates no window or native settings.
It displays the logo to the left of the time and hides the item when Focus is off.
It does not substitute another mode's logo.
The reader never sets Focus, writes the Focus database, or changes macOS privacy permissions.
Battery and volume items are absent. The clock uses `h:mm AM/PM` without a date.

## Caffeine indicator

The native bar shows a white outline mug left of the Focus icon and clock while any `caffeinate` process runs.
This includes sessions started by Raycast's Coffee extension and sessions started in a terminal.
The item hides when the last session exits. Overlapping sessions keep it visible.
The browser snapshot does not include this live indicator.

```text
caffeinate starts → macOS power event → pmset terminal stream ┐
                                                             ├→ read processes → update mug
caffeinate exits → kqueue process notification ────────────────┘
```

The item uses `update_freq=0`. It reads the state at startup and after `system_woke`.
One Python listener per bar reads `pmset -g assertionslog` through a pseudo-terminal.
The pseudo-terminal prevents pipe buffering. macOS wakes the listener when a power event or watched process exit occurs.
The listener uses a blocking kqueue without a timeout. It has no polling timer.
Process-exit notifications cover manual stops and timer expiry, including exits immediately after assertion release.
The initial event-stream marker forces another snapshot to close the subscription/startup race.

The listener holds a file lock to prevent duplicates across wake events and config reloads.
It watches the bar process and closes its event stream when that process exits.
Temporary read or item-update failures preserve the last state and leave the listener running.
If the power-event stream itself stops, the listener logs the error and exits.
A config reload or wake starts it again. There is no periodic recovery timer.
Diagnostics appear under `~/Library/Caches/sketchybar-caffeine/<bar-key>/listener.log`.

The item uses Raycast Coffee's outline mug, bundled as a white 36×36 transparent PNG.
It displays the image at 18 points. Caffeine startup loads the bundled image without compiling a renderer.
The status order is Caffeine, Focus, then the clock. The current mug and moon have about 11-point visible gaps.
The mug background has a 1-point optical adjustment to align it with the text.
The original SVG, MIT license, and regeneration instructions live in `sketchybar/.config/sketchybar/assets/caffeine/`.
No Raycast extension files, hotkeys, or power settings change.
Raycast's [Coffee implementation](https://github.com/raycast/extensions/blob/main/extensions/coffee/src/utils.ts)
starts `/usr/bin/caffeinate`. Apple's [pmset implementation](https://github.com/apple-oss-distributions/PowerManagement/blob/main/pmset/pmset.m)
subscribes to power-assertion change notifications.

## Selected design

Dracula Glass uses IBM Plex Mono Medium for the workspace numbers, application name, and clock.
It has a 38-point bar, 30-point group backgrounds, 8-point corners, and 60% Dracula surfaces.
The workspace and application glass brackets have a 7-point gap.
The application chevron is absent. Selected workspaces use Dracula purple text and a subtle purple background.
Workspace highlights are 24×24 points, with 3-point outer insets and centered numbers.
Four-point padding on adjacent items gives an 8-point gap between highlight tiles.
Workspace items move before the 7-point application spacer. The approved bar runs at login.

The choices follow `ghostty/.config/ghostty/config`, `vscode/Library/Application Support/Code/User/settings.json`,
and the Dracula palette used across the dotfiles.

The browser uses verified `briefcase.fill`, `moon.fill`, and `questionmark.circle` PNG assets generated by `focus_symbol.swift`.
The browser snapshot remains a sample. The native trial reads the actual current Focus icon.
Names remain in accessible labels and tooltips. The bar displays only the logo.

SketchyBar accepts font glyphs through `icon.font` and raster images through `background.image`.
[Item properties](https://felixkratz.github.io/SketchyBar/config/items) document both interfaces.
The [image loader](https://github.com/FelixKratz/SketchyBar/blob/master/src/image.c) loads PNG and JPEG files.
SF Symbol names need rendering through [AppKit](https://developer.apple.com/documentation/appkit/nsimage/init(systemsymbolname:accessibilitydescription:)).
Convert SVG assets to PNG before using this native image interface.

## Workflow

Each design round gets a branch and a draft PR. Only create them when the round has concrete changes.
Rounds 1 to 7 are merged into `master`.

Keep native configuration candidates in an isolated worktree.
Do not stow, reload, install, or start services during browser design rounds.
An approved native trial can use a named instance and this candidate through `--config`.
The config and active plugins use `BAR_NAME`, so a named trial never targets the installed instance.
Stop the named process to end the trial. The installed files and Homebrew service remain unchanged.

Browser rendering checks visual layout and local interactions.
Native font rendering, blur, display positioning, event delivery, and commands require later macOS validation.
Run plugin fixture checks with `python3 previews/sketchybar/test_plugins.py`.
These checks intercept commands and never contact the installed bar or change Focus.
