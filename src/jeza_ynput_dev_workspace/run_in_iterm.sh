#!/bin/bash

# Check if a command was provided
if [ -z "$1" ]; then
    echo "Usage: ./run_in_iterm.sh 'command_to_run'"
    exit 1
fi

# also pass all env vars
export $(printenv | sed 's/^/export /')

# The command to execute
CMD="$1"

# Use osascript to talk to iTerm2
osascript <<EOF
tell application "iTerm"
    activate
    set newWindow to (create window with default profile)
    tell current session of newWindow
        write text "$CMD"
    end tell
end tell
EOF
