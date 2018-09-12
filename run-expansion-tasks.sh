#!/bin/bash
source venv/bin/activate
rq worker expansion-tasks
