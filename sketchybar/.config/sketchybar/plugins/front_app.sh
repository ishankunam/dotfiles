#!/bin/sh

# Some events send additional information specific to the event in the $INFO
# variable. E.g. the front_app_switched event sends the name of the newly
# focused application in the $INFO variable:
# https://felixkratz.github.io/SketchyBar/config/events#events-and-scripting

if [ "$SENDER" = "front_app_switched" ]; then
  "${BAR_NAME:-sketchybar}" --set "$NAME" label="$INFO"
else
  app=$(aerospace list-windows --focused --format '%{app-name}') || exit 1
  [ -n "$app" ] && "${BAR_NAME:-sketchybar}" --set "$NAME" label="$app"
fi
