#!/usr/bin/env bash
# Bootstraps this machine from the dotfiles repo. Safe to re-run.
set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DOTFILES_DIR"

# Packages that mirror $HOME and get symlinked via stow.
# obsidian/ is copied by hand (see obsidian/README.md); macos/ is a plain
# script, not a stow package.
STOW_PACKAGES=(aerospace brew claude ghostty git neovim sketchybar ssh tmux vscode zsh)

echo "==> Homebrew"
if ! command -v brew >/dev/null 2>&1; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

echo "==> brew bundle"
brew bundle --file="$DOTFILES_DIR/brew/.Brewfile"

echo "==> Oh My Zsh"
if [ ! -d "$HOME/.oh-my-zsh" ]; then
  RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
fi

ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"

echo "==> zsh plugins/theme"
[ -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ] || \
  git clone --depth 1 https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
[ -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ] || \
  git clone --depth 1 https://github.com/zsh-users/zsh-syntax-highlighting "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
[ -d "$ZSH_CUSTOM/themes/powerlevel10k" ] || \
  git clone --depth 1 https://github.com/romkatv/powerlevel10k "$ZSH_CUSTOM/themes/powerlevel10k"

echo "==> tmux plugin manager (TPM)"
[ -d "$HOME/.tmux/plugins/tpm" ] || \
  git clone --depth 1 https://github.com/tmux-plugins/tpm "$HOME/.tmux/plugins/tpm"

echo "==> stow"
for pkg in "${STOW_PACKAGES[@]}"; do
  stow -t "$HOME" "$pkg"
done

echo
read -r -p "Apply macOS system preference tweaks (Dock/Finder/Trackpad/dark mode)? [y/N] " apply_macos
if [[ "$apply_macos" =~ ^[Yy]$ ]]; then
  bash "$DOTFILES_DIR/macos/defaults.sh"
fi

cat <<'EOF'

Done. A few things still need doing by hand:
  - obsidian/: see obsidian/README.md (settings are copied into a vault, not stowed)
  - Set zsh as your login shell if it isn't already: chsh -s /bin/zsh
  - Open tmux and press <prefix> + I to install tmux plugins via TPM
  - Restart your terminal so Oh My Zsh / Powerlevel10k / new PATH entries take effect
EOF
