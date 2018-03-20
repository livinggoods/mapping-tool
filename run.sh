#!/bin/bash
source venv/bin/activate
gunicorn -b 0.0.0.0:5000 --workers 8 --access-logformat "%(h)s %(r)s %(s)s"  --access-logfile - --error-logfile - wsgi:application
