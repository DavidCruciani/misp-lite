#!/bin/bash
set -e

# run migrations
poetry run alembic upgrade head

# pull submodules
git submodule update --init --recursive

# start API
poetry run python -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 80
