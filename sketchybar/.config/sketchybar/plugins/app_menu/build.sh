#!/bin/bash
set -euo pipefail
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$SOURCE_DIR/build/SketchyBar App Menu.app"
mkdir -p "$APP/Contents/MacOS"
/usr/bin/swiftc -O "$SOURCE_DIR/main.swift" -o "$APP/Contents/MacOS/AppMenu" -framework AppKit -framework ApplicationServices
cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>local.sketchybar.app-menu</string>
<key>CFBundleName</key><string>SketchyBar App Menu</string>
<key>CFBundleExecutable</key><string>AppMenu</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSUIElement</key><true/>
</dict></plist>
PLIST
/usr/bin/codesign --force --sign - "$APP"
