#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Create cache table
python manage.py createcachetable

# Collect static files
python manage.py collectstatic --noinput