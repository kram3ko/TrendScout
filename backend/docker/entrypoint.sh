#!/usr/bin/env bash
# One image, three roles. Migrations run once — in the api role — so the worker
# and scheduler never race each other on the same DDL.
set -euo pipefail

case "${1:-api}" in
  api)
    alembic upgrade head
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
    ;;
  worker)
    exec taskiq worker app.tasks.broker:broker app.tasks.jobs --workers 1
    ;;
  scheduler)
    exec taskiq scheduler app.tasks.broker:scheduler app.tasks.jobs
    ;;
  *)
    exec "$@"
    ;;
esac
