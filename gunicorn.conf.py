import os

bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
accesslog = "-"
errorlog = "-"
worker_tmp_dir = "/tmp"
graceful_timeout = 20
timeout = 30
control_socket_disable = True
