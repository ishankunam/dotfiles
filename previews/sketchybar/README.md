# SketchyBar browser sandbox

Open `index.html` in a browser. It works as a local file without a server.
The current round uses `desktop-preview.html` and `desktop.json` as its editable sources.
The original three-direction comparison remains in `preview.html` and the Round 1 branch.
All preview files belong outside the Stow packages.
Nothing in this folder starts SketchyBar or changes the installed configuration.

Round 1 compares Minimal, Floating, and Grouped with identical sample contents.
Round 2 compared Grouped with the original native configuration.
Round 3 uses Grouped with AeroSpace workspaces, the enabled Focus, and 12-hour time.
Round 4 removes the clock glyph and uses the configured Focus symbol without its name.
Round 5 selects Dracula Glass and replaces its Fira Code text with IBM Plex Mono Medium at 14 points.
Round 6 validates the native candidate and reads the actual Focus icon through Shortcuts.
The selected design opens first. Earlier directions remain available as references.
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
The Hack Nerd Font and Fira Code subsets come from the installed fonts.
IBM Plex Mono Medium uses the complete, unmodified installed TTF file.
Their licenses are in `assets/HACK-LICENSE.txt`, `assets/FIRA-LICENSE.txt`, and `assets/IBM-PLEX-LICENSE.txt`.
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

The Focus reader runs a read-only shortcut every ten seconds. It does not access the protected Focus database.
Create a shortcut named **SketchyBar Focus** with these two actions:

1. Add **Get Current Focus**.
2. Add **Stop and Output**, with **Current Focus** as its result and **Do Nothing** as its output fallback.

The CLI requests `public.png`, which returns the configured Focus icon.
No output after a successful run means Focus is off. Each read uses a fresh directory to prevent stale icons.
An absent shortcut, timeout, invalid PNG, or renderer failure means the state is unavailable.
The installed helper was created and verified through the Shortcuts editor.
Its export required an iCloud sign-in, which was not available. The two-action recipe is its reproducible source.
The AppKit renderer crops transparent padding, preserves the symbol shape, and tints it white in a cached 36×36 PNG.
It uses the installed Swift toolchain and standard AppKit. It creates no window or native settings.
It displays the logo to the left of the time and hides the item when Focus is off.
If the shortcut is unavailable, it displays a question-mark symbol instead of claiming Focus is off.
It does not substitute another mode's logo.
The reader never sets Focus, writes the Focus database, or changes macOS privacy permissions.
Battery and volume items are absent. The clock uses `h:mm AM/PM` without a date.

## Alternatives from the dotfiles

Dracula Glass is the selected native candidate in the isolated worktree.
It uses IBM Plex Mono Medium for the workspace numbers, application name, and clock.
The candidate has a 38-point bar, 30-point group backgrounds, 8-point corners, and 60% Dracula surfaces.
The application chevron is absent. Selected workspaces use Dracula purple text and a subtle purple background.
Workspace items now move before the application item, which remains present when the chevron is removed.
The installed bar remains unchanged. Earlier directions remain browser references.

| Design | Source | Applied choices |
|---|---|---|
| Dracula Glass | Ghostty, VS Code, and the user's font selection | IBM Plex Mono Medium at 14 points, Dracula purple, 60% surfaces, smaller floating groups. |
| Terminal Line | tmux and reduced chrome in VS Code/Obsidian | One continuous strip, bracketed selection, direct time display, no group boxes. |
| Prompt Segments | Powerlevel10k and Ghostty's Dracula palette | Joined segments, slanted separators, rounded ends, a green app segment. |

The observed sources are `ghostty/.config/ghostty/config`, `tmux/.tmux.conf`, `zsh/.p10k.zsh`,
`vscode/Library/Application Support/Code/User/settings.json`, and `obsidian/.obsidian/appearance.json`.
Neovim currently contains indentation and leader settings, with no additional appearance theme.
macOS defaults select dark appearance and hide the Dock. These choices support the reduced-chrome direction.
These designs interpret the stored preferences. They do not claim to reproduce an Obsidian theme whose CSS is absent.

The browser uses verified `briefcase.fill`, `moon.fill`, and `questionmark.circle` PNG assets generated by `focus_symbol.swift`.
The browser snapshot remains a sample. The native trial reads the actual current Focus icon.
Names remain in accessible labels and tooltips. The bar displays only the logo.

SketchyBar accepts font glyphs through `icon.font` and raster images through `background.image`.
[Item properties](https://felixkratz.github.io/SketchyBar/config/items) document both interfaces.
The [image loader](https://github.com/FelixKratz/SketchyBar/blob/master/src/image.c) loads PNG and JPEG files.
SF Symbol names need rendering through [AppKit](https://developer.apple.com/documentation/appkit/nsimage/init(systemsymbolname:accessibilitydescription:)).
Convert SVG assets to PNG before using this native image interface.

## Iteration history

Each design round has a branch, atomic commits, and a draft PR.
The first branch is `codex/sketchybar-round-1`, based on `master`.
Each later round starts from the preceding round and targets that branch.
Register the ordered PRs in GitHub's native stack after creating them.

```text
master → round-1 → round-2 → round-3 → round-4 → round-5 → round-6
```

Only create a branch and PR when the corresponding round has concrete changes.
Keep native configuration candidates in an isolated worktree.
Do not stow, reload, install, or start services during browser design rounds.
An approved native trial can use a named instance and this candidate through `--config`.
The config and active plugins use `BAR_NAME`, so a named trial never targets the installed instance.
Stop the named process to end the trial. The installed files and Homebrew service remain unchanged.

Browser rendering checks visual layout and local interactions.
Native font rendering, blur, display positioning, event delivery, and commands require later macOS validation.
Run plugin fixture checks with `python3 previews/sketchybar/test_plugins.py`.
These checks intercept commands and never contact the installed bar or change Focus.
