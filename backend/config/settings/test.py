"""Settings de pytest : rapides et indépendants du .env du poste."""

import os

# base.py exige ces variables : on fournit des valeurs de test avant de l'importer.
# setdefault laisse la CI les surcharger (DATABASE_URL vers PostgreSQL à partir de l'étape 4).
os.environ.setdefault("DJANGO_SECRET_KEY", "cle-de-test-uniquement")
os.environ.setdefault("DATABASE_URL", "sqlite://:memory:")

from .base import *  # noqa: E402

ALLOWED_HOSTS = ["testserver"]

# Le hacheur par défaut (PBKDF2) est lent exprès ; MD5 suffit pour des mots de passe de test.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
