# SketchyBar browser sandbox

Open `index.html` in a browser. It works as a local file without a server.
The source is `preview.html`. Both files belong outside the Stow packages.
Nothing in this folder starts SketchyBar or changes the installed configuration.

Round 1 compares Minimal, Floating, and Grouped with identical sample contents.
Space selection and battery details change only the browser preview.
Codex exposes design controls for height, text, spacing, corners, color, and sample states.

To regenerate the standalone page, use the Codex visualization renderer:

```sh
python3 "$VISUALIZE_SKILL/scripts/render.py" previews/sketchybar/preview.html previews/sketchybar/index.html --force
```

Set `VISUALIZE_SKILL` to the installed visualization skill directory.
The generated `index.html` includes its browser runtime and needs no installed skill to open.

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
