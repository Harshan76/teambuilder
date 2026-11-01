import os

# Railway & Cloud Production Gunicorn Configuration
port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"

# Concurrency & Threads
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
worker_class = "gthread"

# Request timeouts (120s accommodates clustering & data preparation)
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "30"))

# Stream logs directly to stdout/stderr for Railway real-time logging
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")

# Graceful worker restart
max_requests = 1000
max_requests_jitter = 50
