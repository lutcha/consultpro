#!/bin/sh
set -e
echo "Creating logs directory..."
mkdir -p /app/logs
exec "$@"
