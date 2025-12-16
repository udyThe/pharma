import logging
import sys


def setup_logging():
    """Configure basic JSON-ish structured logging."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '{"level":"%(levelname)s","time":"%(asctime)s","name":"%(name)s","message":"%(message)s"}'
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(logging.INFO)

