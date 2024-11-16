from pathlib import Path
from huey import RedisHuey

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

BASE_DIR = Path(__file__).resolve().parent

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",  # Добавяне на папката "static"
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-0gbf8qk)(69!mk&kc-ln^$7p!4yhz#v*z7wrvpw@qw26ku9@^%"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'huey.contrib.djhuey',
    'channels',
    'teams',
    'accounts',
    'game',
    'players',
    'leagues',
    'fixtures',
    'messaging',
    'match',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    'corsheaders.middleware.CorsMiddleware',
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
                'game.navbar_processors.user_team',
            ],
        },
    }, ]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

CORS_ALLOW_ALL_ORIGINS = True

WSGI_APPLICATION = "leadtheleague.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

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

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_USER_MODEL = 'accounts.CustomUser'
AUTH_PASSWORD_VALIDATORS = []

LOGIN_REDIRECT_URL = 'game:home'
LOGOUT_REDIRECT_URL = 'accounts:welcome_page'

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = 'Europe/Sofia'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

ASGI_APPLICATION = 'leadtheleague.asgi.application'

# Настройка за Channels и Redis (необходим за WebSocket комуникация)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],  # Увери се, че Redis работи
        },
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# В settings.py или в друга конфигурация за Huey
HUEY = RedisHuey(
    'leadtheleague',  # Името на проекта
    immediate=False,  # Изключваме immediate режима
    host='localhost',  # Адрес на Redis сървъра
    port=6379,  # Порт на Redis сървъра
)

# Допълнителни настройки за Huey
HUEY.consumer = {
    'workers': 10,  # Задаваме 10 работника
    'worker_type': 'process',  # Работниците ще бъдат процеси (може да е 'thread' или 'greenlet')
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
