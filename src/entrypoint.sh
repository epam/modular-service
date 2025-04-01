#!/bin/sh

set -e


log() { echo "[INFO] $(date) $1" >&2; }

start_server() {
  log "Syncing MongoDB indexes"
  python main.py create-indexes

  log "Creating a system user"
  python main.py create-system-user

  log "Initializing vault"
  python main.py init-vault

  log "Activating regions"
  python main.py activate-regions

  log "Starting Gunicorn server"
  exec python main.py run --gunicorn
}

start_server
