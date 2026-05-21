from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = [
    '.elasticbeanstalk.com',
    os.environ.get('DOMAIN', ''),
    'localhost',
]

# Allow CSRF for both HTTP and HTTPS EB domains (Django 4.0+ requirement)
CSRF_TRUSTED_ORIGINS = [
    'https://*.elasticbeanstalk.com',
    'http://*.elasticbeanstalk.com',
    'http://localhost:8000',
    'https://localhost:8000',
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
