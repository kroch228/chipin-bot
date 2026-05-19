#!/bin/sh
set -e

echo "Running migrations..."
python -m alembic upgrade head

echo "Starting bot..."
exec python -m bot.main
