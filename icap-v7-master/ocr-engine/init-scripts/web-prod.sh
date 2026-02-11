#!/bin/bash
set -e

gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 1800 --pythonpath '/' --reload manage:app
