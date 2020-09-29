import os
from flask import Flask
from celery import Celery
from flask_sqlalchemy import SQLAlchemy
#from flask_migrate import Migrate
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

app = Flask(__name__)
app.config.from_object('config')
print(app.config)
db = SQLAlchemy(app)

#Celery('tasks', backend='rpc://', broker='pyamqp://')
#migrate = Migrate(app, db)

def make_celery(app):
    celery = Celery(app.import_name, backend=CELERY_RESULT_BACKEND, broker=CELERY_BROKER_URL)
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

from atlanBackend import routes, models