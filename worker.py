from atlanBackend import app
from atlanBackend import db


from celery import current_app
from celery.bin import worker

application = current_app._get_current_object()
worker = worker.worker(app=application)

options = {
    'broker': app.config['CELERY_BROKER_URL'],
    'loglevel': 'INFO',
    'traceback': True,
}

# Starts Celery worker
worker.run(**options)
