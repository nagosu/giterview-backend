from pathlib import Path
from datetime import timedelta
from common.aws import AWSManager
from dotenv import load_dotenv
import os
import pymysql

pymysql.install_as_MySQLdb()

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/
SECRET_KEY = AWSManager.get_secret("DJANGO")["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

CORS_ALLOW_CREDENTIALS = True
Access_Control_Allow_Credentials = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
CORS_ORIGIN_WHITELIST = [
    "http://localhost:3000",
]
CSRF_TRUSTED_ORIGINS = ["https://giterview.site"]
ALLOWED_HOSTS = ["backend", "localhost", "127.0.0.1", "giterview.site"]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",  # 파일 업로드를 위한 설정
    ),
}

AUTH_USER_MODEL = "users.User"

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

ASGI_APPLICATION = "giterview.asgi.application"
WSGI_APPLICATION = "giterview.wsgi.application"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "gunicorn",
    "drf_yasg",
    "rest_framework",
    "django_celery_beat",
    "django_celery_results",
    "django_prometheus",
    "interviews",
    "resumes",
    "users",
    "corsheaders",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "giterview.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

db_secret = AWSManager.get_secret("MYSQL")

DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DATABASE"),
        "USER": os.getenv("MYSQL_USER"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD"),
        "HOST": os.getenv("MYSQL_HOST"),
        "PORT": os.getenv("MYSQL_PORT"),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = "static/"


# ###AWS#### AWS 액세스 키 설정
# AWS_ACCESS_KEY_ID = os.environ.get("MY_AWS_ACCESS_KEY")
# AWS_SECRET_ACCESS_KEY = os.environ.get("MY_AWS_SECRET_ACCESS_KEY")

# # S3 버킷 및 파일 저장 경로 설정
# AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")

# # S3 파일 URL 설정
# AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
# AWS_S3_OBJECT_PARAMETERS = {
#     "CacheControl": "max-age=86400",
# }

# FILE_URL = "https://" + AWS_S3_CUSTOM_DOMAIN

# # # S3 버킷 및 파일 저장 경로 설정
# # AWS_STORAGE_BUCKET_NAME = "giterview-bucket"
# # # S3 파일 URL 설정
# # AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
# # AWS_S3_OBJECT_PARAMETERS = {
# #     "CacheControl": "max-age=86400",
# # }

# # FILE_URL = "https://" + AWS_S3_CUSTOM_DOMAIN + "/test1/"

# # # 기본 스토리지를 S3 스토리지로 설정
# # DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"


# AWS_REGION = 'ap-northeast-2'
# AWS_STORAGE_BUCKET_NAME = "bucketkubit"
# AWS_ACCESS_KEY_ID = get_secret("aws_access_key_id")
# AWS_SECRET_ACCESS_KEY = get_secret("aws_secret_access_key")
# AWS_S3_CUSTOM_DOMAIN = '%s.s3.%s.amazonaws.com' % (AWS_STORAGE_BUCKET_NAME, AWS_REGION)
# STATIC_URL = "http://%s/static/" % AWS_S3_CUSTOM_DOMAIN
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# MEDIA_URL = "http://%s/media/" % AWS_S3_CUSTOM_DOMAIN

# AWS 접근 설정
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "ap-northeast-2"  # AWS 리전 정보 (예: 'ap-northeast-2'는 서울 리전)

# S3 설정
AWS_STORAGE_BUCKET_NAME = "resume7946"  # 사용할 S3 버킷 이름
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com"
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}
AWS_LOCATION = "pre_image_url/"  # S3 내의 저장할 위치 (폴더 이름)

# Django가 사용할 기본 파일 스토리지 설정
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# from storages.backends.s3boto3 import S3Boto3Storage
#
# class AudioS3Boto3Storage(S3Boto3Storage):
#     location = 'audio/'  # 새로운 위치 설정
