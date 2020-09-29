import os

ALLOWED_EXTENSIONS = set(['csv'])
UPLOAD_FOLDER = './resources/uploads/'
DOWNLOAD_FOLDER = './files/downloads/'
SECRET_KEY = 'aIHEMFSPJ7H7G4bLwzFLDetrIob9M8tp'
SQLALCHEMY_DATABASE_URI = 'sqlite:///atlan.db'
RABBIT_MQ_URL = 'rpc://'
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or \
    'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or \
    'redis://localhost:6379/0'
REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'