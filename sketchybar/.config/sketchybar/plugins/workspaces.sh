#!/bin/sh
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
exec python3 "$CONFIG_DIR/plugins/workspaces.py" "$@"
