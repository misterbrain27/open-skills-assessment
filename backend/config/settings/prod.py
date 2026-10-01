"""Settings de production : HTTPS obligatoire, aucun mode debug possible."""

from .base import *

# Forcé ici : une variable DJANGO_DEBUG=True oubliée ne doit pas activer le debug en prod.
DEBUG = False

# HTTPS : toute requête HTTP est redirigée, et les cookies ne circulent que chiffrés.
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS : le navigateur refusera le HTTP pendant cette durée. On commence court (1 h), car
# une valeur longue ne s'annule pas si HTTPS tombe en panne ; on l'augmentera une fois la
# prod stable.
SECURE_HSTS_SECONDS = 3600
# Tous nos sous-domaines sont servis en HTTPS : la règle s'applique aussi à eux.
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# Ajoute seulement la directive `preload` à l'en-tête. L'inscription sur la liste des
# navigateurs reste une démarche manuelle (hstspreload.org), qui exige au moins 1 an.
SECURE_HSTS_PRELOAD = True
