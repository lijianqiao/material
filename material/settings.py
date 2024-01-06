import os
from pathlib import Path
from .simpleui_conf import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8060')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-f=kc6k4q2+^c7g02*q649yvb@(0g!z7lnd+d7kv%w0z#byc58i"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'simpleui',     # 修改默认后台模板为simpleui
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",      # 解决跨域
    "import_export",    # 文件导入导出
    # "mater",
    "mater.apps.MaterConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'corsheaders.middleware.CorsMiddleware',    # 解决跨域问题
]

ROOT_URLCONF = "material.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = "material.wsgi.application"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'material',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
    }
}

# 降低创建账户时候密码要求，现在要求至少3位，可以全部数字
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 3,
        }
    },
]

# 解决django4.0 跨域报 Cross-Origin Opener Policy错误
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'None'
CSRF_TRUSTED_ORIGINS = ['http://localhost:8060']

#  django的admin后台名称
ADMIN_SITE_HEADER = "成都物料管理平台"
# 设置会话过期时间为1小时
SESSION_EXPIRE_SECONDS = 60 * 60  # 1小时
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_TIMEOUT_REDIRECT = f'{BASE_URL}/admin/login/?next=/admin/'

LANGUAGE_CODE = "zh-hans"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_TZ = False

# 配置媒体文件路径
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
