# Native validation

Validated on 2026-10-12 with SketchyBar 2.24.1, using an independent named instance.
The MSI G273 and rotated DELL S2721QS both rendered the candidate.
The user confirmed that the font, glass groups, and Focus icon looked right on both monitors.

- Native queries confirmed IBM Plex Mono Medium at 14 points and a text-only 12-hour clock.
- The application label initialized as ChatGPT at startup.
- All three groups used 60% Dracula backgrounds, 8-point corners, and 30-point heights.
- Item rectangles did not overlap on either display. Focus appeared to the left of the clock.
- The configured Focus icon came from the two-action read-only shortcut. Its name was absent from the bar.
- A controlled off fixture hid the native item without changing macOS Focus. The live icon was restored afterward.
- A temporary workspace appeared and gained the selected highlight. It disappeared after returning to the original workspace.
- The first removal check exceeded its eight-second deadline. A later AeroSpace query confirmed the original four-workspace list.
- Ten fixture checks passed, including stale output prevention, failure handling, image normalization, and caching.

The native trial did not change installed configuration files or start a Homebrew service.
The installed configuration's SHA-256 remained `c0e77c9cc4a79393eb6e6bd3475dbd237feab2711c4e5ad77c7d4f388220bda2` throughout the trial.

The initial Focus-name probe could not establish the original mode.
The Focus restoration attempt enabled `in class`, which the user then observed.
The final reader uses the actual icon directly and never changes Focus.
Further Focus changes require the user's explicit choice. The current mode remains `in class`.

Shortcuts export required an unavailable iCloud sign-in. The helper's source is the two-action recipe in README.md.
No privacy permissions were expanded.

## Focus picker validation, 2026-10-21

The approved picker is installed in the live bar. Five one-action Shortcuts toggle the configured modes.
The native test used each popup row's `NAME` environment and verified all five resulting Focus glyphs.
Each selected row used its native colored badge and retained a transparent row background.
Live `mouse.entered` and `mouse.exited` handler calls enabled and cleared the purple highlight.
These calls verified native properties, rather than physical pointer movement.
The original Focus state was off. The test restored it and confirmed that the icon was hidden and the popup was closed.
Twenty-six fixture checks passed, including the actual popup-row environment, failure refresh, unknown-mode handling, and native badge rendering.
The background SketchyBar process was unavailable as a computer-use app surface. Popup placement and physical mouse interaction on both monitors remain visually unverified.
