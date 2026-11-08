#!/bin/sh

# The $NAME variable is passed from sketchybar and holds the name of
# the item invoking this script:
# https://felixkratz.github.io/SketchyBar/config/events#events-and-scripting

case "$SENDER" in
  mouse.entered)
    "${BAR_NAME:-sketchybar}" --set clock_group background.color=0xc0484058
    exec python3 "$CONFIG_DIR/plugins/calendar_popup.py" open
    ;;
  mouse.exited|mouse.exited.global)
    exec "${BAR_NAME:-sketchybar}" --set clock_group background.color=0x99282a36
    ;;
esac

"${BAR_NAME:-sketchybar}" --set "$NAME" label="$(LC_TIME=C date '+%I:%M %p' | sed 's/^0//')"

