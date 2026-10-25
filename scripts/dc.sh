#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
exec docker compose -f docker-compose.yml -f compose.monitoring.yml -f compose.logging.yml "$@"
