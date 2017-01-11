#!/bin/bash
current_dir = `pwd`
chdir "$current_dir"
source venv/bin/activate
python manage.py runserver -h 0.0.0.0 -p 5000 >/dev/null 2>&1 &
