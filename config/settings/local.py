from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

SECRET_KEY = 'django-insecure-local-dev-only-key'

# SQLite (1주차 개발용 - Docker 세팅 후 PostgreSQL로 전환)
# PostgreSQL 전환 시 아래 주석 해제하고 SQLite 블록 제거
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# PostgreSQL (Docker 세팅 후 사용)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'mini_ad_manager',
#         'USER': 'postgres',
#         'PASSWORD': 'postgres',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

# Redis
REDIS_URL = 'redis://localhost:6379/0'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}

# Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
