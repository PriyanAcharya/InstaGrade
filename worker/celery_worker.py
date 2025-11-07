# worker/celery_worker.py
import os
from app.tasks import celery

if __name__ == "__main__":
    # This file is the worker entrypoint. In Dockerfile or commandline, run:
    # python -m worker.celery_worker
    # or directly start celery: celery -A app.tasks worker --loglevel=info
    print("Worker entrypoint. Use celery CLI to run the worker.")
