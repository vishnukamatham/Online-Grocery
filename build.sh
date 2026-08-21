#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# Install required packages
pip install -r requirements.txt

# Gather all static resources
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate

# Load initial products and categories
python manage.py loaddata products_fixture.json

# Ensure admin and vishnu superusers are created/reset with correct credentials
python create_admin.py

