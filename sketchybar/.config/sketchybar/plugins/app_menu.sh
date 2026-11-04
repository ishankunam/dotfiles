#!/bin/bash
set -euo pipefail
PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE="$PLUGIN_DIR/app_menu/main.swift"
APP="$PLUGIN_DIR/app_menu/build/SketchyBar App Menu.app"
BINARY="$APP/Contents/MacOS/AppMenu"
if [[ ! -x "$BINARY" || "$SOURCE" -nt "$BINARY" ]]; then
  echo 'Build the app menu with plugins/app_menu/build.sh first.' >&2
  exit 1
fi
exec /usr/bin/open -g "$APP" --args "$@"
