#!/bin/bash
set -e
echo "=== Smart Conference Assistant Setup ==="

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python manage.py migrate
python manage.py seed_papers

echo ""
echo "=== Creating admin user ==="
python manage.py createsuperuser --username admin --email admin@example.com

echo ""
echo "=== Setup complete! Run: python manage.py runserver ==="
