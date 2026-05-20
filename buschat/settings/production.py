from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = [
    '.elasticbeanstalk.com',
    os.environ.get('DOMAIN', ''),
    'localhost',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
