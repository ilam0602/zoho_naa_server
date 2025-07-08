#!/bin/bash

gunicorn --bind 0.0.0.0:8080 --timeout 20  --preload --max-requests 70 --max-requests-jitter=20 --workers=3 --log-level=debug wsgi:app

echo "Server is running..."