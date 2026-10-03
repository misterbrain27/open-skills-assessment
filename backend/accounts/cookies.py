"""Cookie du refresh token (ADR 0003).

Seul endroit où ses attributs sont écrits : la pose et la suppression doivent utiliser le
même nom et le même chemin, sinon le navigateur garde l'ancien cookie.
"""

from rest_framework.response import Response
from rest_framework_simplejwt.settings import api_settings

REFRESH_COOKIE_NAME = "refresh_token"
# Le navigateur n'envoie le cookie qu'au refresh et au logout, pas à chaque requête de l'API.
REFRESH_COOKIE_PATH = "/api/auth/"


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        token,
        # Expire avec le refresh token ; sans Max-Age, il disparaîtrait à la fermeture du
        # navigateur.
        max_age=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
        path=REFRESH_COOKIE_PATH,
        # Illisible par JavaScript : une XSS ne peut pas l'emporter.
        httponly=True,
        # HTTPS seulement, partout : les navigateurs font une exception pour http://localhost.
        secure=True,
        # Jamais envoyé depuis un autre site : pas de refresh ni de logout par CSRF.
        samesite="Strict",
    )


def delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH, samesite="Strict")
