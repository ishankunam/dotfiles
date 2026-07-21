# dotfiles

My personal macOS setup — shell, terminal, editor, window management, and
tooling — kept in one place so I can rebuild this machine from scratch or
hand it to someone else.

## What's in here

Managed with [GNU Stow](https://www.gnu.org/software/stow/): each top-level
directory mirrors the exact path it should occupy under `$HOME`, and
`stow -t "$HOME" <package>` symlinks it into place.

| Package | What it covers |
|---|---|
| `zsh/` | `.zshrc`, `.zprofile`, Powerlevel10k config (Oh My Zsh, `zsh-autosuggestions`, `zsh-syntax-highlighting`) |
| `git/` | `.gitconfig` |
| `ssh/` | `~/.ssh/config` (host aliases only — no keys, see below) |
| `brew/` | `.Brewfile` — every formula, cask, and VS Code extension |
| `ghostty/` | Terminal config + Dracula theme |
| `tmux/` | `.tmux.conf` (TPM, `tmux-resurrect`, `tmux-continuum`) |
| `aerospace/` | AeroSpace tiling window manager config |
| `sketchybar/` | Menu bar replacement config |
| `neovim/` | `init.lua` |
| `vscode/` | VS Code `settings.json` / `keybindings.json` |
| `claude/` | Claude Code `settings.json`, plus `instructions.md` kept as reference (not wired to a live path) |
| `macos/` | `defaults.sh` — Dock/Finder/Trackpad/appearance tweaks (not a stow package, just a script) |
| `obsidian/` | Vault settings snapshot — copied by hand, see [`obsidian/README.md`](obsidian/README.md) |

## Setup on a new machine

```sh
git clone git@github.com:ishankunam/dotfiles.git ~/dotfiles
cd ~/dotfiles
./bootstrap.sh
```

`bootstrap.sh` installs Homebrew if needed, runs `brew bundle`, installs Oh
My Zsh + its plugins/theme, installs TPM, symlinks every package above into
`$HOME` via `stow`, and offers to apply the macOS tweaks in
`macos/defaults.sh`. It's safe to re-run.

Two things it doesn't do, on purpose:
- **`obsidian/`** isn't stowed — Obsidian settings are copied (not
  symlinked) into a vault's `.obsidian/` folder. Follow
  [`obsidian/README.md`](obsidian/README.md).
- **SSH keys** aren't here at all. `ssh/.ssh/config` only has host aliases;
  generate/copy your own keys and point `IdentityFile` at them.

## Prerequisites

- macOS
- [Homebrew](https://brew.sh) (installed automatically by `bootstrap.sh` if missing)
- Xcode Command Line Tools (`xcode-select --install`)
