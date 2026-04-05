## --- METADATA ---
# Filename: src/queue_config.py
# Version: 1.0.0
# ------------------
#
# --- CHANGELOG ---
# v1.0.0: INIT: Created a centralized module for Redis and RQ connection configuration to break a circular dependency between the CLI and task modules.
# ------------------

# --- INTEGRITY ---
# Previous Character Count: 0
# Current Character Count: 332
# Syntax Check: PASS
# Logic Validation: The file correctly defines and initializes the Redis connection and the default RQ queue.
# Reason for Change: To implement a robust, scalable project structure by centralizing queue configuration and breaking import cycles.
# ------------------
from redis import Redis
from rq import Queue

# --- Redis Queue Connection ---
# Assumes Redis is running on localhost:6379
# This connection is used by both the client (vda_cli.py) and workers.
redis_conn = Redis()
q = Queue(connection=redis_conn)
