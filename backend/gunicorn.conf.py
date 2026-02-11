"""Gunicorn configuration. Used by: gunicorn -c gunicorn.conf.py app.main:app"""

import multiprocessing
import os

# Server Socket
bind = os.getenv("BIND", "0.0.0.0:8000")

# Worker Configuration
worker_class = "uvicorn.workers.UvicornWorker"
workers = min(2 * multiprocessing.cpu_count() + 1, int(os.getenv("WEB_CONCURRENCY", "4")))
max_requests = 1000
max_requests_jitter = 100

# Timeouts
timeout = 180
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sμs'

# Process Management
preload_app = True
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Server Hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    pass


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")


def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    worker.log.info("worker received INT or QUIT signal")


def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal (timeout)."""
    worker.log.info("worker received SIGABRT signal")
