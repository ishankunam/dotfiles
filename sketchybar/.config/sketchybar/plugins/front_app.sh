#!/bin/sh

# Some events send additional information specific to the event in the $INFO
# variable. E.g. the front_app_switched event sends the name of the newly
# focused application in the $INFO variable:
# https://felixkratz.github.io/SketchyBar/config/events#events-and-scripting

if [ "$SENDER" = "mouse.entered" ]; then
  exec "$(dirname "$0")/app_menu.sh" --hover
fi

if [ "$SENDER" = "front_app_switched" ]; then
  [ "$INFO" = "SketchyBar App Menu" ] && exit 0
  "${BAR_NAME:-sketchybar}" --set "$NAME" label="$INFO"
else
  app=$(aerospace list-windows --focused --format '%{app-name}') || exit 1
  [ -n "$app" ] && "${BAR_NAME:-sketchybar}" --set "$NAME" label="$app"
fi
