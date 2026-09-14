#!/bin/bash

set -e

MODULE_DIR="$(
    cd "$(dirname "$0")"
    pwd
)"

case "${1:-default}" in
    open)
        child_pid=""

        stop_child() {
            if [[ -n "$child_pid" ]]; then
                kill -TERM "$child_pid" 2>/dev/null || true
                wait "$child_pid" 2>/dev/null || true
            fi
        }

        trap stop_child TERM INT

        python3 \
            "$MODULE_DIR/test-module-gui.py" &

        child_pid=$!

        wait "$child_pid"
        status=$?

        child_pid=""

        exit "$status"
        ;;

    *)
        exec python3 \
            "$MODULE_DIR/test-module-gui.py" \
            --print-info
        ;;
esac
