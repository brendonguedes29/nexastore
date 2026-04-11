"""
Django settings for plataforma project.
"""

from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================
# SEGURANÇA
# =========================================
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-dev-key"
)

DEBUG = False

ALLOWED_HOSTS = [
    "nexastore-xw5y.onrender.com",
    "nexastoreofficial.com.br",
    "www.nexastoreofficial.com.br",
    "127.0.0.1",
    "localhost",
]

CSRF_TRUSTED_ORIGINS = [
    "https://nexastore-xw5y.onrender.com",
    "https://nexastoreofficial.com.br",
    "https://www.nexastoreofficial.com.br",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =========================================
# URL BASE
# =========================================
PLATFORM_BASE_URL = os.environ.get(
    "PLATFORM_BASE_URL",
    "https://nexastoreofficial.com.br"
)

MERCADOPAGO_WEBHOOK_URL = f"{PLATFORM_BASE_URL}/webhooks/mercadopago/"
MERCADOPAGO_REDIRECT_URI = f"{PLATFORM_BASE_URL}/painel/pagamentos/callback/"

# =========================================
# MERCADO PAGO
# =========================================
MERCADOPAGO_PUBLIC_KEY = os.environ.get("MERCADOPAGO_PUBLIC_KEY", "")
MERCADOPAGO_ACCESS_TOKEN = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")
MERCADOPAGO_CLIENT_ID = os.environ.get("MERCADOPAGO_CLIENT_ID", "")
MERCADOPAGO_CLIENT_SECRET = os.environ.get("MERCADOPAGO_CLIENT_SECRET", "")

# =========================================
# LOGIN
# =========================================
LOGIN_URL = "/entrar/"
LOGIN_REDIRECT_URL = "/painel/"
LOGOUT_REDIRECT_URL = "/"

# =========================================
# APPS
# =========================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "cloudinary",
    "cloudinary_storage",

    "produtos",
    "lojas",
]

# =========================================
# MIDDLEWARE
# =========================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =========================================
# URLS / TEMPLATE
# =========================================
ROOT_URLCONF = "plataforma.urls"

CSRF_FAILURE_VIEW = "lojas.views.csrf_erro"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "plataforma.wsgi.application"

# =========================================
# BANCO DE DADOS (CORREÇÃO AQUI)
# =========================================
DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL")
    )
}

# =========================================
# SENHAS
# =========================================
AUTH_PASSWORD_VALIDATORS = []

# =========================================
# INTERNACIONALIZAÇÃO
# =========================================
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# =========================================
# STATIC / MEDIA
# =========================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
    "API_KEY": os.environ.get("CLOUDINARY_API_KEY", ""),
    "API_SECRET": os.environ.get("CLOUDINARY_API_SECRET", ""),
}

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# =========================================
# DEFAULT
# =========================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =========================================
# EMAIL
# =========================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = "bsg181818@gmail.com"
EMAIL_HOST_PASSWORD = "rxcazwgnbnynphzv"

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER