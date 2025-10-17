#!/usr/bin/env bash
set -e
PYTHON=${PYTHON:-python3}
VENV=".venv"
if [ ! -d "$VENV" ]; then
  $PYTHON -m venv $VENV
fi
source $VENV/bin/activate
pip install -U pip
pip install -r requirements.txt
export PYTHONPATH=.
CMD="${1:-all}"
if [ "$CMD" = "reset" ]; then
  rm -f app/app.db
  echo "Database reset."
  exit 0
fi
if [ "$CMD" = "test" ] || [ "$CMD" = "all" ]; then
  export TESTING=1
  pytest -q
fi
if [ "$CMD" = "run" ] || [ "$CMD" = "all" ]; then
  unset TESTING
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
