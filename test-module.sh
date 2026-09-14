#!/bin/bash

set -e

MODULE_DIR="$(
    cd "$(dirname "$0")"
    pwd
)"

case "${1:-default}" in
    open)
        python3 \
            "$MODULE_DIR/test-module-gui.py"
        ;;

    *)
        exec python3 \
            "$MODULE_DIR/test-module-gui.py" \
            --print-info
        ;;
esac
