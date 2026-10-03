"""Settings communs à tous les environnements.

Tout ce qui varie d'un environnement à l'autre est lu dans des variables d'environnement.
Les valeurs par défaut sont les plus sûres : une variable oubliée fait échouer le démarrage
ou ferme l'accès, elle n'ouvre jamais rien.
"""

from datetime import timedelta
from pathlib import Path

from environ import Env

env = Env()

# backend/config/settings/base.py → backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Pas de valeur par défaut : sans clé, le démarrage échoue (ImproperlyConfigured).
SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env.bool("DJANGO_DEBUG", default=False)

# Liste vide par défaut : hors debug, Django refuse toutes les requêtes.
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "core",
    "accounts",
    "rest_framework_simplejwt.token_blacklist",
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Seul le JWT est accepté (ADR 0003). Sans authentification par session, l'API n'a pas
    # besoin de protection CSRF, et une requête sans token reçoit 401 avec WWW-Authenticate.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # Un endpoint sans permission_classes explicite est fermé, pas ouvert.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Une liste sans limite peut renvoyer des milliers de lignes en une requête.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Sans limite, un attaquant essaie des milliers de mots de passe par minute.
    "DEFAULT_THROTTLE_RATES": {
        "login": "5/min",
    },
    # Nombre de reverse proxys devant l'application. Avec None (défaut de DRF), l'IP du client
    # est lue dans X-Forwarded-For, que le client écrit lui-même : changer sa valeur à chaque
    # essai contourne le throttle. 0 = adresse réelle de la connexion.
    "NUM_PROXIES": env.int("DJANGO_NUM_PROXIES", default=0),
}

SIMPLE_JWT = {
    # Durées de l'ADR 0003. SIGNING_KEY reste par défaut, c'est-à-dire SECRET_KEY.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    # Chaque refresh renvoie un nouveau refresh token et met l'ancien sur liste noire : un
    # refresh token ne sert qu'une fois, et une copie volée réutilisée plus tard est refusée.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Pas de base par défaut : sans DATABASE_URL, le démarrage échoue au lieu de basculer
# silencieusement sur un SQLite perdu au redémarrage du conteneur.
DATABASES = {
    "default": env.db("DATABASE_URL"),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Déclaré avant la toute première migration : le changer ensuite casse l'historique des
# migrations (auth et admin pointent vers cette table) et oblige à recréer la base.
AUTH_USER_MODEL = "accounts.User"

# Logs JSON sur la sortie standard : un outil de collecte peut filtrer sur les champs
# (levelname, name…) sans expression régulière, et Docker récupère stdout tel quel.
LOGGING = {
    "version": 1,
    # False : garder les loggers déjà créés par Django (django.request, django.server…),
    # sinon leurs erreurs disparaissent sans bruit.
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Open Skills Assessment API",
    "DESCRIPTION": "API REST de l'application Open Skills Assessment.",
    "VERSION": "0.1.0",
    # Le schéma ne décrit pas son propre endpoint.
    "SERVE_INCLUDE_SCHEMA": False,
}
