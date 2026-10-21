#!/bin/sh
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if [ "$SENDER" = mouse.exited.global ]; then
  exec python3 "$CONFIG_DIR/plugins/focus_menu.py" close
fi
exec python3 "$CONFIG_DIR/plugins/focus.py"
