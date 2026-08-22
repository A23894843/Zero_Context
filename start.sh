#!/bin/bash

# Force the use of the virtual environment's Python and Uvicorn
VENV_PYTHON="./.venv/bin/python"
VENV_UVICORN="./.venv/bin/uvicorn"

# Start the Core Engine silently
nohup $VENV_PYTHON main.py > /dev/null 2>&1 &

# Start the Dashboard silently
nohup $VENV_UVICORN dashboard:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &