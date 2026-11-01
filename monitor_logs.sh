#!/bin/bash

export TZ=Asia/Seoul
cd "$(dirname "$0")" || exit 1
mkdir -p log_history || exit 1
cd log_history || exit 1

PID=
LINES=0

cleanup() {
    if [ -n "$PID" ]; then
        kill "$PID" 2>/dev/null
        wait "$PID" 2>/dev/null
    fi
}
trap 'exit 0' INT TERM
trap cleanup EXIT

while true; do
    FILE="$(date +%F).out"

    if [ ! -f "$FILE" ]; then
        sleep 1
        continue
    fi

    echo "=== Monitoring $FILE ==="
    tail -n "$LINES" -F "$FILE" &
    PID=$!

    while [ "$(date +%F).out" = "$FILE" ]; do
        sleep 1
    done

    cleanup
    PID=
    LINES=+1
done
