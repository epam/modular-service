#!/bin/sh

set -e

python main.py create-indexes
python main.py create-system-user
python main.py init-vault
python main.py activate-regions
python main.py run --gunicorn

