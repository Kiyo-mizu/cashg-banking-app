#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Make migrations (in case they don't exist)
python manage.py makemigrations

# Run database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput