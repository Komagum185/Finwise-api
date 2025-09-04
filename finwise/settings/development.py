"""
Development specific settings.
"""
from .base import *

# Debug settings
DEBUG = True

# Allow all hosts for development
ALLOWED_HOSTS = ['*']

# CORS for development
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3001',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# Less restrictive for development
CORS_ALLOW_ALL_ORIGINS = True

# Database - can use SQLite for development if needed
DATABASES['default'].update({
    'OPTIONS': {
        'sslmode': 'disable',  # SSL not needed locally
    }
})

# Disable security features for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_HSTS_SECONDS = 0

# Enable browsable API
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append(
    'rest_framework.renderers.BrowsableAPIRenderer'
)

# Logging for development
LOGGING['root']['level'] = 'DEBUG'