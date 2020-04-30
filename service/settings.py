"""
Django settings for service project.

Generated by 'django-admin startproject' using Django 2.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""
from configparser import RawConfigParser
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

config = RawConfigParser()
config.read(BASE_DIR+'/setting.ini')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config.get('MAIN', 'SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config.get('MAIN', 'DEBUG')

ALLOWED_HOSTS = [_.strip() for _ in config.get('MAIN', 'ALLOWED_HOSTS').split(',')]

# Application definition

INSTALLED_APPS = [
    'channels',
    'import_export',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'djoser',
    'corsheaders',
    'chat',
    'ai',
    'dataparser',
    'service',
    'tcpsocket',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

STREAM_API_KEY = '3fmx98fcw2xm'
STREAM_API_SECRET = 'sqgvg59aujuj2arc42tf65w25qxyj7spwurappu9jz8vx2ufwhpp4766h9kw8mu3'
DJOSER = {
    'SERIALIZERS': {
        'token': 'auth.serializers.StreamTokenSerializer',
    }
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]

ROOT_URLCONF = 'service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'service.wsgi.application'
ASGI_APPLICATION = "service.routing.application"
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', config.get('CHANNEL', 'CHANNEL_PORT'))],
        },
        # "ROUTING": "service.routing",
    },
}


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': config.get('DATABASE', 'DATABASE_ENGINE'),
        # 'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        'NAME': config.get('DATABASE', 'DATABASE_NAME'),
        'USER': config.get('DATABASE', 'DATABASE_USER'),
        'PASSWORD': config.get('DATABASE', 'DATABASE_PASSWORD'),
        'HOST': config.get('DATABASE', 'DATABASE_HOST'),
        'PORT': config.get('DATABASE', 'DATABASE_PORT')
    },
    # 'postgresql': {
    #     'ENGINE': 'django.db.backends.postgresql_psycopg2',
    # },
    # 'mysql': {
    #     'ENGINE': 'django.db.backends.mysql',
    # }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = config.get('MAIN', 'TIME_ZONE')

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

CORS_ORIGIN_ALLOW_ALL  = True

IMPORT_EXPORT_USE_TRANSACTIONS = True
IMPORT_EXPORT_IMPORT_PERMISSION_CODE = 'add'
