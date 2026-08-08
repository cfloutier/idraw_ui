#!/usr/bin/env bash
set -e
source .venv/bin/activate
PYTHONPATH=src python -m idraw_ui.app
