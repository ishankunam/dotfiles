#!/bin/sh

# The $NAME variable is passed from sketchybar and holds the name of
# the item invoking this script:
# https://felixkratz.github.io/SketchyBar/config/events#events-and-scripting

if [ "$SENDER" = "mouse.entered" ]; then
  exec python3 "$CONFIG_DIR/plugins/calendar_popup.py" open
fi

"${BAR_NAME:-sketchybar}" --set "$NAME" label="$(LC_TIME=C date '+%I:%M %p' | sed 's/^0//')"

