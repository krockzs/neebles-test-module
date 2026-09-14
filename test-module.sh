#!/bin/bash

set -euo pipefail

MODULE_DIR="$(
    cd -- "$(dirname -- "$0")"
    pwd
)"

command="${1:-default}"

case "$command" in
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

        set +e
        wait "$child_pid"
        status=$?
        set -e

        child_pid=""

        exit "$status"
        ;;

    notify)
        notification_json="$(
            python3 \
                "$MODULE_DIR/test-module-gui.py" \
                --notification-text
        )"

        title="$(
            python3 -c \
                'import json,sys; print(json.load(sys.stdin)["title"])' \
                <<< "$notification_json"
        )"

        message="$(
            python3 -c \
                'import json,sys; print(json.load(sys.stdin)["message"])' \
                <<< "$notification_json"
        )"

        exec neebles \
            notify \
            success \
            "$title" \
            "$message"
        ;;

    default)
        exec python3 \
            "$MODULE_DIR/test-module-gui.py" \
            --print-info
        ;;

    *)
        echo "Unknown module command: $command" >&2
        exit 2
        ;;
esac
