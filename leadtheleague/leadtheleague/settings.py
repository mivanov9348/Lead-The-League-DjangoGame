import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FERNET_SECRET_KEY = os.getenv("FERNET_SECRET_KEY")
if not FERNET_SECRET_KEY:
    raise ValueError("FERNET_SECRET_KEY is not set in environment variables")

BASE_DIR = Path(__file__).resolve().parent

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

ASGI_APPLICATION = 'leadtheleague.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    }
}


STATIC_ROOT = BASE_DIR / 'staticfiles'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-0gbf8qk)(69!mk&kc-ln^$7p!4yhz#v*z7wrvpw@qw26ku9@^%"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

MEDIA_URL = '/media/'  # URL адрес, използван за медийни файлове
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Application definition
INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django.contrib.humanize',
    'rest_framework',
    "channels",
    'core',
    'teams',
    'accounts',
    'game',
    'players',
    'leagues',
    'fixtures',
    'messaging',
    'match',
    'transfers',
    'finance',
    'staff',
    'stadium',
    'cups',
    'europeancups',
    'vault',
    'ai_engine',
    'chat'
]

SITE_ID = 1

ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "leadtheleague.urls"

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
                'django.template.context_processors.static',
                'leadtheleague.context_processors.team_info',
                'leadtheleague.context_processors.backgrounds'
            ],
        },
    }, ]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

CORS_ALLOW_ALL_ORIGINS = True

# WSGI_APPLICATION = "leadtheleague.wsgi.application"


DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'leadtheleague',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'DESKTOP-NVD5L3R\\SQLEXPRESS',
        'PORT': '',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache'),  # Абсолютен път
    }
}

AUTH_USER_MODEL = 'accounts.CustomUser'
AUTH_PASSWORD_VALIDATORS = []

LOGIN_REDIRECT_URL = 'game:home'
LOGOUT_REDIRECT_URL = 'accounts:welcome'

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = 'Europe/Sofia'

USE_I18N = True

USE_TZ = True

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'leadtheleaguedj@gmail.com'
EMAIL_HOST_PASSWORD = 'CSKA1948aaa!'
DEFAULT_FROM_EMAIL = 'leadtheleaguedj@gmail.com'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGLOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'app.log',  # Името на файла, където ще записваш логовете
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'custom_logger': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
