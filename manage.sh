#!/bin/bash

# ASCII Art
echo " __          __        _ _   _     ___  ____  "
echo " \ \        / /       | | | | |   / _ \/ ___| "
echo "  \ \  /\  / /__  __ _| | |_| |__| | | \___ \ "
echo "   \ \/  \/ / _ \/ _\` | | __| '_ \ | | |___) |"
echo "    \  /\  /  __/ (_| | | |_| | | | |_| |___/ "
echo "     \/  \/ \___|\__,_|_|\__|_| |_|\___/____/ "
echo ""

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project root directory so relative paths (like 'data/') work correctly
cd "$DIR"

# Execute the python script
python3 backend/manager.py "$@"
