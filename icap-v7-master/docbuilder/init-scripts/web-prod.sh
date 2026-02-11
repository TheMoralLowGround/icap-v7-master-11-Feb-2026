#!/bin/bash
set -e

gunicorn --bind 0.0.0.0:5000 --workers 4 --pythonpath '/' --timeout 7200 manage:app
