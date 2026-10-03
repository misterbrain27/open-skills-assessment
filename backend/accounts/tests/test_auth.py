import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.cookies import REFRESH_COOKIE_NAME
from accounts.models import User
from accounts.tests.factories import OrganizationFactory, UserFactory

pytestmark = pytest.mark.django_db

LOGIN_URL = reverse("login")
REFRESH_URL = reverse("token_refresh")
LOGOUT_URL = reverse("logout")
ME_URL = reverse("me")

# Mot de passe posé par UserFactory.
PASSWORD = "mot-de-passe-de-test"


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def api_client():
    # Comme un navigateur, APIClient garde les cookies reçus et les renvoie ensuite.
    return APIClient()


def login(client: APIClient, email: str, password: str = PASSWORD):
    return client.post(LOGIN_URL, {"email": email, "password": password}, format="json")


def bearer(client: APIClient, access: str) -> APIClient:
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client


# Login


def test_login_returns_access_in_body_and_refresh_only_in_cookie(api_client, user):
    response = login(api_client, user.email)

    assert response.status_code == 200
    assert set(response.data) == {"access"}
    assert response.cookies[REFRESH_COOKIE_NAME].value


def test_login_cookie_attributes(api_client, user):
    cookie = login(api_client, user.email).cookies[REFRESH_COOKIE_NAME]

    assert cookie["httponly"] is True
    assert cookie["secure"] is True
    assert cookie["samesite"] == "Strict"
    assert cookie["path"] == "/api/auth/"
    assert cookie["max-age"] == 24 * 60 * 60


def test_login_same_error_for_wrong_password_and_unknown_email(api_client, user):
    wrong_password = login(api_client, user.email, "pas-le-bon")
    unknown_email = login(api_client, "inconnu@example.com")

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    # Un message différent révélerait quels emails ont un compte.
    assert wrong_password.data == unknown_email.data
    assert REFRESH_COOKIE_NAME not in wrong_password.cookies


def test_login_refuses_account_without_usable_password(api_client):
    # Comme un compte créé par POST /api/users/ (étape 6) : pas de mot de passe utilisable.
    user = User.objects.create_user(
        email="sans-mdp@example.com", organization=OrganizationFactory()
    )

    assert login(api_client, user.email, "").status_code == 400
    assert login(api_client, user.email, "nimporte-quoi").status_code == 401


def test_login_rejects_form_data(api_client, user):
    # Un formulaire HTML d'un autre site ne peut pas envoyer de JSON : login CSRF bloqué.
    response = api_client.post(
        LOGIN_URL, {"email": user.email, "password": PASSWORD}, format="multipart"
    )

    assert response.status_code == 415
    assert REFRESH_COOKIE_NAME not in response.cookies


# Accès avec l'access token


def test_access_token_gives_access_to_api(api_client, user):
    access = login(api_client, user.email).data["access"]

    response = bearer(api_client, access).get(ME_URL)

    assert response.status_code == 200
    assert response.data["email"] == user.email


def test_no_token_returns_401_with_www_authenticate(api_client):
    response = api_client.get(ME_URL)

    assert response.status_code == 401
    assert response["WWW-Authenticate"] == 'Bearer realm="api"'


def test_tampered_token_returns_401(api_client, user):
    access = login(api_client, user.email).data["access"]
    # On remplace la signature : le contenu ne correspond plus à ce que le serveur a signé.
    header, payload, _signature = access.split(".")
    tampered = f"{header}.{payload}.signature-inventee"

    assert bearer(api_client, tampered).get(ME_URL).status_code == 401


def test_inactive_user_refused_even_with_valid_access(api_client, user):
    access = login(api_client, user.email).data["access"]
    user.is_active = False
    user.save()

    # simplejwt recharge l'utilisateur à chaque requête : le token seul ne suffit pas.
    assert bearer(api_client, access).get(ME_URL).status_code == 401


# Refresh


def test_refresh_rotates_cookie_and_returns_new_access(api_client, user):
    first = login(api_client, user.email)
    old_refresh = first.cookies[REFRESH_COOKIE_NAME].value

    response = api_client.post(REFRESH_URL)

    assert response.status_code == 200
    assert set(response.data) == {"access"}
    assert response.data["access"] != first.data["access"]
    new_refresh = response.cookies[REFRESH_COOKIE_NAME].value
    assert new_refresh
    assert new_refresh != old_refresh


def test_refresh_without_cookie_returns_401(api_client):
    assert api_client.post(REFRESH_URL).status_code == 401


def test_old_refresh_refused_after_rotation(api_client, user):
    old_refresh = login(api_client, user.email).cookies[REFRESH_COOKIE_NAME].value
    api_client.post(REFRESH_URL)

    # Un attaquant qui aurait copié l'ancien cookie le rejoue.
    api_client.cookies[REFRESH_COOKIE_NAME] = old_refresh

    assert api_client.post(REFRESH_URL).status_code == 401


def test_refresh_refused_for_inactive_user(api_client, user):
    login(api_client, user.email)
    user.is_active = False
    user.save()

    assert api_client.post(REFRESH_URL).status_code == 401


def test_refresh_refused_for_deleted_user(api_client, user):
    login(api_client, user.email)
    user.delete()

    # Sans traitement dans RefreshView, le serializer de simplejwt répondrait 500.
    assert api_client.post(REFRESH_URL).status_code == 401


# Logout


def test_logout_deletes_cookie(api_client, user):
    login(api_client, user.email)

    response = api_client.post(LOGOUT_URL)

    assert response.status_code == 204
    cookie = response.cookies[REFRESH_COOKIE_NAME]
    assert cookie.value == ""
    assert cookie["max-age"] == 0
    assert cookie["path"] == "/api/auth/"


def test_refresh_refused_after_logout(api_client, user):
    refresh = login(api_client, user.email).cookies[REFRESH_COOKIE_NAME].value
    api_client.post(LOGOUT_URL)

    # Le cookie est supprimé, mais une copie du token ne doit plus rien valoir.
    api_client.cookies[REFRESH_COOKIE_NAME] = refresh

    assert api_client.post(REFRESH_URL).status_code == 401


def test_logout_is_idempotent(api_client, user):
    refresh = login(api_client, user.email).cookies[REFRESH_COOKIE_NAME].value
    api_client.post(LOGOUT_URL)

    # Second logout avec le token déjà sur liste noire, puis sans cookie du tout.
    api_client.cookies[REFRESH_COOKIE_NAME] = refresh
    assert api_client.post(LOGOUT_URL).status_code == 204
    assert APIClient().post(LOGOUT_URL).status_code == 204


# Throttle


def test_login_throttled_after_five_attempts(api_client, user):
    statuses = [login(api_client, user.email, "pas-le-bon").status_code for _ in range(6)]

    assert statuses == [401, 401, 401, 401, 401, 429]


def test_throttle_ignores_spoofed_x_forwarded_for(api_client, user):
    # Avec NUM_PROXIES à None, chaque fausse IP aurait son propre compteur.
    statuses = [
        api_client.post(
            LOGIN_URL,
            {"email": user.email, "password": "pas-le-bon"},
            format="json",
            HTTP_X_FORWARDED_FOR=f"10.0.0.{i}",
        ).status_code
        for i in range(6)
    ]

    assert statuses == [401, 401, 401, 401, 401, 429]
