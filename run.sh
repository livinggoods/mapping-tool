#!/bin/bash
source venv/bin/activate
gunicorn -b 0.0.0.0:5000 --workers 8 --access-logformat "Remote client - %({X-Forwarded-For}i)s Webserver - %(h)s %(r)s %(s)s"  --access-logfile logs/expansion.log --error-logfile logs/expansion.err.log wsgi:application
