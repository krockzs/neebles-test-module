#!/bin/bash

set -euo pipefail

MODULE_DIR="$(
    cd -- "$(dirname -- "$0")"
    pwd
)"

run_child() {
    local child_pid=""

    stop_child() {
        if [[ -n "$child_pid" ]]; then
            kill -TERM "$child_pid" 2>/dev/null || true
            wait "$child_pid" 2>/dev/null || true
        fi
    }

    trap stop_child TERM INT EXIT

    "$@" &
    child_pid=$!

    set +e
    wait "$child_pid"
    local status=$?
    set -e

    child_pid=""
    trap - TERM INT EXIT

    return "$status"
}

if [[ "${NEEBLES_CALLER:-}" == "tray-manager" ]]; then
    run_child python3 "$MODULE_DIR/tray/tray-provider.py"
    exit $?
fi

command="${1:-default}"

case "$command" in
    open)
        run_child python3 "$MODULE_DIR/runtime.py"
        exit $?
        ;;

    default)
        python3 - "$MODULE_DIR/manifest.json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    manifest = json.load(handle)

print(f"N.E.E.B.L.E.S. Test Module {manifest['version']}")
print("Use: neebles test-module open")
PY
        ;;

    *)
        echo "Unknown legacy module command: $command" >&2
        echo "Open the module first, then use the dynamic contract commands." >&2
        exit 2
        ;;
esac
