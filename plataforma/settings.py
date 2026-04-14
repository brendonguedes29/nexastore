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
    "COLE_AQUI_SUA_SECRET_KEY_LOCAL"
)

DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "www.nexastoreofficial.com.br",
    "nexastoreofficial.com.br",
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    "https://www.nexastoreofficial.com.br",
    "https://nexastoreofficial.com.br",
]

if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =========================================
# URL BASE DA PLATAFORMA
# =========================================
PLATFORM_BASE_URL = os.environ.get(
    "PLATFORM_BASE_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

MERCADOPAGO_WEBHOOK_URL = f"{PLATFORM_BASE_URL}/webhooks/mercadopago/"
MERCADOPAGO_REDIRECT_URI = f"{PLATFORM_BASE_URL}/painel/pagamentos/callback/"

# =========================================
# MERCADO PAGO
# =========================================
MERCADOPAGO_PUBLIC_KEY = os.environ.get(
    "MERCADOPAGO_PUBLIC_KEY",
    "COLE_AQUI_SUA_PUBLIC_KEY"
)
MERCADOPAGO_ACCESS_TOKEN = os.environ.get(
    "MERCADOPAGO_ACCESS_TOKEN",
    "COLE_AQUI_SEU_ACCESS_TOKEN"
)
MERCADOPAGO_CLIENT_ID = os.environ.get(
    "MERCADOPAGO_CLIENT_ID",
    "COLE_AQUI_SEU_CLIENT_ID"
)
MERCADOPAGO_CLIENT_SECRET = os.environ.get(
    "MERCADOPAGO_CLIENT_SECRET",
    "COLE_AQUI_SEU_CLIENT_SECRET"
)

# =========================================
# LOGIN / LOGOUT
# =========================================
LOGIN_URL = "/entrar/"
LOGIN_REDIRECT_URL = "/painel/"
LOGOUT_REDIRECT_URL = "/"

# =========================================
# APLICAÇÕES
# =========================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "produtos",
    "lojas",
]

# =========================================
# MIDDLEWARES
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
# URLS / TEMPLATES
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
# BANCO DE DADOS
# =========================================
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.strip('"').strip("'")

    if DATABASE_URL.startswith("b'") and DATABASE_URL.endswith("'"):
        DATABASE_URL = DATABASE_URL[2:-1]
    elif DATABASE_URL.startswith('b"') and DATABASE_URL.endswith('"'):
        DATABASE_URL = DATABASE_URL[2:-1]

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
# ARQUIVOS ESTÁTICOS / MÍDIA
# =========================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =========================================
# E-MAIL
# =========================================
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "COLE_AQUI_SEU_EMAIL_REMETENTE"
)

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend"
)

EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "COLE_AQUI_SEU_EMAIL")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "COLE_AQUI_SUA_SENHA_OU_APP_PASSWORD")