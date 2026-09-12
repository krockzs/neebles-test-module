#!/bin/bash

set -e

MODULE_DIR="$(
    cd "$(dirname "$0")"
    pwd
)"

case "${1:-default}" in
    open)
        exec python3 \
            "$MODULE_DIR/test-module-gui.py"
        ;;
    *)
        echo "N.E.E.B.L.E.S. Test Module 1.0.0"
        ;;
esac
