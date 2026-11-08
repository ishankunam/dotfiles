#!/bin/bash
set -euo pipefail
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$SOURCE_DIR/build"
APP="$BUILD_DIR/SketchyBar Calendar.app"
STAGING="$BUILD_DIR/SketchyBar Calendar staging.app"
mkdir -p "$STAGING/Contents/MacOS" "$BUILD_DIR/module-cache"
CLANG_MODULE_CACHE_PATH="$BUILD_DIR/module-cache" /usr/bin/swiftc -O \
  "$SOURCE_DIR/EventStore.swift" "$SOURCE_DIR/main.swift" \
  -o "$STAGING/Contents/MacOS/SketchyBarCalendar" \
  -framework AppKit -framework EventKit -framework SwiftUI
cat > "$STAGING/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>local.sketchybar.calendar</string>
<key>CFBundleName</key><string>SketchyBar Calendar</string>
<key>CFBundleExecutable</key><string>SketchyBarCalendar</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSUIElement</key><true/>
<key>NSCalendarsFullAccessUsageDescription</key><string>Show events from your synced calendars in the SketchyBar agenda.</string>
<key>NSAppleEventsUsageDescription</key><string>Open the selected event in Apple Calendar.</string>
<key>NSCalendarsUsageDescription</key><string>Show events from your synced calendars in the SketchyBar agenda.</string>
</dict></plist>
PLIST
/usr/bin/codesign --force --sign - "$STAGING"
rm -rf "$APP"
mv "$STAGING" "$APP"
