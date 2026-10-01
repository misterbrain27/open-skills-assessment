"""Settings du poste de développement : lit le .env placé à la racine du repo."""

from pathlib import Path

from environ import Env

# Le .env doit être lu AVANT d'importer base.py, qui lit les variables dès son exécution.
# backend/config/settings/dev.py → parents[3] = racine du repo.
Env.read_env(Path(__file__).resolve().parents[3] / ".env")

from .base import *  # noqa: E402
