#!/bin/sh

python main.py create-indexes
python main.py create-system-user
python main.py init-vault
python main.py run --gunicorn --swagger

