#!/usr/bin/env bash
# macOS system preference tweaks. Safe to re-run.
set -euo pipefail

echo "Applying macOS defaults..."

# Dock
defaults write com.apple.dock autohide -bool true
defaults write com.apple.dock autohide-time-modifier -float 0
defaults write com.apple.dock orientation -string "right"
defaults write com.apple.dock tilesize -int 46
defaults write com.apple.dock largesize -int 16
defaults write com.apple.dock magnification -bool false
defaults write com.apple.dock minimize-to-application -bool true
defaults write com.apple.dock show-recents -bool false

# Finder
defaults write com.apple.finder AppleShowAllFiles -bool true
defaults write NSGlobalDomain AppleShowAllExtensions -bool true
defaults write com.apple.finder ShowPathbar -bool true
defaults write com.apple.finder ShowStatusBar -bool true

# Trackpad
defaults write com.apple.AppleMultitouchTrackpad Clicking -bool true
defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

# Screenshots
defaults write com.apple.screencapture location -string "${HOME}/Documents"

# Appearance
defaults write NSGlobalDomain AppleInterfaceStyle -string "Dark"

echo "Restarting affected apps..."
killall Dock Finder SystemUIServer >/dev/null 2>&1 || true

echo "Done."
