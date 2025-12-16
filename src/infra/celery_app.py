try:
    from celery import Celery
except ImportError:
    Celery = None


class DummyTask:
    def __init__(self, func):
        self.func = func

    def delay(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class DummyCelery:
    def task(self, *args, **kwargs):
        def decorator(func):
            return DummyTask(func)
        return decorator


if Celery:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    default_broker = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    celery_app = Celery(
        "pharma_agents",
        broker=os.getenv("CELERY_BROKER_URL", default_broker),
        backend=os.getenv("CELERY_BACKEND_URL", os.getenv("REDIS_URL", default_broker)),
    )
else:
    celery_app = DummyCelery()

