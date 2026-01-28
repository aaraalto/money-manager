#!/bin/bash
# mnm - Radiant Money Manager CLI
# A beautiful TUI for managing your finances

cd "$(dirname "$0")"
python3 -m app.cli.main "$@"
