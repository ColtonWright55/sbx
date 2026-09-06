#!/bin/bash
# Watches this folder and rsyncs it to the Pi on every change.
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE="cjw@pi1.lan:~/rpimonitor"

sync() {
    rsync -avz --delete --exclude '.git' --exclude '__pycache__' --exclude 'logs' --exclude 'debug' --exclude '.venv' "$DIR/" "$REMOTE/"
}

echo "Initial sync to $REMOTE ..."
sync

echo "Watching $DIR for changes (Ctrl+C to stop)..."
while inotifywait -rq -e modify,create,delete,move "$DIR"; do
    sync
done
