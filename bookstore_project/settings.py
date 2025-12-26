"""
Django settings for bookstore_project project.
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Site URL for payment callbacks and absolute URLs
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    'crispy_forms',
    'crispy_bootstrap5',
    'ckeditor',
    'ckeditor_uploader',
    'django_filters',
    
    # Local apps
    'accounts',
    'books',
    'orders',
    'payments',
    'admin_panel',
    'rentals',
    'support',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'bookstore_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'books.context_processors.cart_context',
                'books.context_processors.categories_context',
                'books.context_processors.language_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'bookstore_project.wsgi.application'

# Database
# MySQL Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='bookstore_db'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES', character_set_connection=utf8mb4, collation_connection=utf8mb4_unicode_ci",
            'charset': 'utf8mb4',
        },
    }
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English'),
    ('bn', 'বাংলা'),
]

TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Locale paths for translation files
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Default charset for MySQL
DATABASE_CHARSET = 'utf8mb4'
DATABASE_COLLATION = 'utf8mb4_unicode_ci'

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# CKEditor
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%',
    },
}

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Redis Cache Configuration
# Set USE_REDIS=False in .env to use local memory cache (when Redis is not available)
USE_REDIS = config('USE_REDIS', default=True, cast=bool)

if USE_REDIS:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f"redis://{config('REDIS_HOST', default='localhost')}:{config('REDIS_PORT', default='6379')}/1",
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'bookstore',
            'TIMEOUT': 300,
        }
    }
else:
    # Fallback to local memory cache when Redis is not available
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'bookstore-cache',
            'TIMEOUT': 300,
        }
    }

# Session Settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 1 day
SESSION_COOKIE_SAMESITE = 'Lax'  # Allow cookies on redirects from payment gateways
SESSION_SAVE_EVERY_REQUEST = True  # Ensure session is saved on every request

# Email Configuration
# You can switch between console (for testing) and SMTP (for real emails)
# Set USE_CONSOLE_EMAIL=True in .env to see emails in terminal
# Set USE_CONSOLE_EMAIL=False in .env to send real emails via SMTP
USE_CONSOLE_EMAIL = config('USE_CONSOLE_EMAIL', default=True, cast=bool)

if USE_CONSOLE_EMAIL:
    # Console backend - emails printed in terminal (good for development/testing)
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@bookstore.com'
else:
    # SMTP backend - real emails sent via Gmail or other SMTP server
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='uzzalbhuiyan905@gmail.com')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='aawx flgg besg rmxe')
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
    
    # Additional SMTP settings for better reliability
    EMAIL_USE_SSL = False  # Use TLS instead of SSL
    EMAIL_TIMEOUT = 30  # Timeout in seconds

# Payment Gateway Settings
PAYMENT_GATEWAYS = {
    'bkash': {
        'app_key': config('BKASH_APP_KEY', default=''),
        'app_secret': config('BKASH_APP_SECRET', default=''),
        'username': config('BKASH_USERNAME', default=''),
        'password': config('BKASH_PASSWORD', default=''),
        'base_url': config('BKASH_BASE_URL', default='https://tokenized.sandbox.bka.sh/v1.2.0-beta'),
    },
    'nagad': {
        'merchant_id': config('NAGAD_MERCHANT_ID', default=''),
        'merchant_number': config('NAGAD_MERCHANT_NUMBER', default=''),
        'public_key': config('NAGAD_PUBLIC_KEY', default=''),
        'private_key': config('NAGAD_PRIVATE_KEY', default=''),
        'base_url': config('NAGAD_BASE_URL', default='http://sandbox.mynagad.com:10080/remote-payment-gateway-1.0'),
    },
    'sslcommerz': {
        'store_id': config('SSLCOMMERZ_STORE_ID', default=''),
        'store_password': config('SSLCOMMERZ_STORE_PASSWORD', default=''),
        'is_sandbox': config('SSLCOMMERZ_IS_SANDBOX', default=True, cast=bool),
    }
}

# SSLCommerz Settings (direct access for payment module)
SSLCOMMERZ_STORE_ID = config('SSLCOMMERZ_STORE_ID', default='')
SSLCOMMERZ_STORE_PASSWORD = config('SSLCOMMERZ_STORE_PASSWORD', default='')
SSLCOMMERZ_IS_SANDBOX = config('SSLCOMMERZ_IS_SANDBOX', default=True, cast=bool)

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG

# Login Settings
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'books:home'
LOGOUT_REDIRECT_URL = 'books:home'

# Celery Configuration
# Celery will only work if Redis is enabled
if USE_REDIS:
    CELERY_BROKER_URL = f"redis://{config('REDIS_HOST', default='localhost')}:{config('REDIS_PORT', default='6379')}/0"
    CELERY_RESULT_BACKEND = f"redis://{config('REDIS_HOST', default='localhost')}:{config('REDIS_PORT', default='6379')}/0"
else:
    # Disable Celery when Redis is not available (tasks will run synchronously)
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat Schedule for Periodic Tasks
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Daily rental reminders and late fee calculations (9 AM every day)
    'send-daily-rental-reminders': {
        'task': 'rentals.tasks.send_daily_rental_reminders',
        'schedule': crontab(hour=9, minute=0),  # 9:00 AM daily
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not executed
        },
    },
    # Update overdue rental status (every hour)
    'update-overdue-status': {
        'task': 'rentals.tasks.update_overdue_status',
        'schedule': crontab(minute=0),  # Every hour at :00
        'options': {
            'expires': 1800,  # Task expires after 30 minutes if not executed
        },
    },
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'bookstore.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)
