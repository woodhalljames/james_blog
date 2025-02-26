#!/usr/bin/env bash
# Exit on error
set -e

# Use python3 instead of python
python3 -m pip install --upgrade pip

# Install requirements
python3 -m pip install -r requirements.txt

# Collect static files
python3 manage.py collectstatic --noinput
