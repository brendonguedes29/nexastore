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
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key")
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
    "plataforma.middleware.LojaMiddleware",
]

# =========================================
# URLS
# =========================================
ROOT_URLCONF = "plataforma.urls"
CSRF_FAILURE_VIEW = "lojas.views.csrf_erro"

# =========================================
# TEMPLATES
# =========================================
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
# BANCO DE DADOS
# =========================================
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    DATABASE_URL = str(DATABASE_URL).strip().replace("b'", "").replace("'", "")

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=False,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# =========================================
# SENHA
# =========================================
AUTH_PASSWORD_VALIDATORS = []

# =========================================
# IDIOMA
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

# =========================================
# CLOUDINARY (IMAGENS)
# =========================================
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

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =========================================
# EMAIL
# =========================================
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "bsg181818@gmail.com")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "").strip()