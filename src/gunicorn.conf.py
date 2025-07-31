import os

bind = "0.0.0.0:8040"
workers = int(os.environ.get('MODULAR_SERVICE_GUNICORN_WORKERS', '2'))
worker_class = 'sync'
wsgi_app = 'onprem.app:make_app()'
timeout = 30
max_requests = 512
max_requests_jitter = 64
