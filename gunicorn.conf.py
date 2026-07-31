import os

bind = "0.0.0.0:" + os.environ.get("PORT", "8080")
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
timeout = int(os.environ.get("APP_GUNICORN_TIMEOUT", "120"))
accesslog = "-"
errorlog = "-"
loglevel = "info"
