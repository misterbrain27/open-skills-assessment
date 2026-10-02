import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from accounts.tests.factories import OrganizationFactory, UserFactory

pytestmark = pytest.mark.django_db

ME_URL = reverse("me")
USERS_URL = reverse("user-list")


def detail_url(user: User) -> str:
    return reverse("user-detail", args=[user.pk])


def client_for(user: User | None) -> APIClient:
    client = APIClient()
    # force_authenticate : les tests ne dépendent pas de la méthode d'authentification
    # (session aujourd'hui, JWT à l'étape 7).
    if user is not None:
        client.force_authenticate(user=user)
    return client


# Deux organisations, chacune avec un admin et un recruteur.
@pytest.fixture
def org_a():
    return OrganizationFactory(name="Organisation A")


@pytest.fixture
def org_b():
    return OrganizationFactory(name="Organisation B")


@pytest.fixture
def admin_a(org_a):
    return UserFactory(organization=org_a, role=User.Role.ADMIN)


@pytest.fixture
def recruiter_a(org_a):
    return UserFactory(organization=org_a, role=User.Role.RECRUITER)


@pytest.fixture
def admin_b(org_b):
    return UserFactory(organization=org_b, role=User.Role.ADMIN)


@pytest.fixture
def recruiter_b(org_b):
    return UserFactory(organization=org_b, role=User.Role.RECRUITER)


@pytest.fixture
def platform_superuser():
    return User.objects.create_superuser(email="plateforme@example.com", password="x")


# /api/me/


def test_me_returns_current_user_and_organization(recruiter_a, org_a):
    response = client_for(recruiter_a).get(ME_URL)

    assert response.status_code == 200
    assert response.data["email"] == recruiter_a.email
    assert response.data["organization"] == {"id": org_a.pk, "name": org_a.name}
    assert "password" not in response.data


def test_me_requires_authentication():
    # 403 et non 401 tant que la session est la première authentification (401 à l'étape 7).
    assert client_for(None).get(ME_URL).status_code == 403


def test_me_refuses_superuser_without_organization(platform_superuser):
    assert client_for(platform_superuser).get(ME_URL).status_code == 403


# Isolation entre organisations


def test_list_contains_only_own_organization(admin_a, recruiter_a, admin_b, recruiter_b):
    response = client_for(admin_a).get(USERS_URL)

    assert response.status_code == 200
    emails = {user["email"] for user in response.data["results"]}
    assert emails == {admin_a.email, recruiter_a.email}


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_other_organization_user_is_not_found(method, admin_a, recruiter_b):
    response = getattr(client_for(admin_a), method)(
        detail_url(recruiter_b), {"first_name": "Modifié"}, format="json"
    )

    # 404 et non 403 : un 403 confirmerait que l'utilisateur existe chez un autre client.
    assert response.status_code == 404
    recruiter_b.refresh_from_db()  # lève DoesNotExist s'il a été supprimé
    assert recruiter_b.first_name != "Modifié"


def test_create_ignores_organization_from_payload(admin_a, org_a, org_b):
    payload = {"email": "nouveau@example.com", "role": "recruiter", "organization": org_b.pk}

    response = client_for(admin_a).post(USERS_URL, payload, format="json")

    assert response.status_code == 201
    assert response.data["organization"]["id"] == org_a.pk
    created = User.objects.get(email="nouveau@example.com")
    assert created.organization == org_a
    # Créé sans mot de passe : le compte n'est pas utilisable tant qu'il n'en a pas défini un.
    assert not created.has_usable_password()


def test_superuser_without_organization_cannot_list(platform_superuser):
    # Sans IsOrganizationMember, le filtre deviendrait organization=None.
    assert client_for(platform_superuser).get(USERS_URL).status_code == 403


# Rôles


def test_recruiter_can_read_own_organization(recruiter_a, admin_a):
    client = client_for(recruiter_a)

    assert client.get(USERS_URL).status_code == 200
    assert client.get(detail_url(admin_a)).status_code == 200


def test_recruiter_cannot_create(recruiter_a):
    payload = {"email": "nouveau@example.com"}

    response = client_for(recruiter_a).post(USERS_URL, payload, format="json")

    assert response.status_code == 403
    assert not User.objects.filter(email="nouveau@example.com").exists()


@pytest.mark.parametrize("method", ["patch", "delete"])
def test_recruiter_cannot_modify(method, recruiter_a, admin_a):
    response = getattr(client_for(recruiter_a), method)(
        detail_url(admin_a), {"role": "recruiter"}, format="json"
    )

    # 403 : l'utilisateur est bien dans son organisation, c'est son rôle qui l'interdit.
    assert response.status_code == 403
    admin_a.refresh_from_db()
    assert admin_a.is_org_admin


def test_admin_can_update_and_delete_own_organization(admin_a, recruiter_a):
    client = client_for(admin_a)

    response = client.patch(detail_url(recruiter_a), {"role": "admin"}, format="json")
    assert response.status_code == 200
    recruiter_a.refresh_from_db()
    assert recruiter_a.is_org_admin

    assert client.delete(detail_url(recruiter_a)).status_code == 204
    assert not User.objects.filter(pk=recruiter_a.pk).exists()


# Pas de fuite de mot de passe


def test_responses_never_contain_password(admin_a, recruiter_a):
    client = client_for(admin_a)

    list_response = client.get(USERS_URL)
    detail_response = client.get(detail_url(recruiter_a))
    create_response = client.post(USERS_URL, {"email": "nouveau@example.com"}, format="json")

    for user_data in [*list_response.data["results"], detail_response.data, create_response.data]:
        assert "password" not in user_data


# Performance


def test_list_query_count_does_not_grow_with_users(admin_a, django_assert_max_num_queries):
    UserFactory.create_batch(15, organization=admin_a.organization)
    client = client_for(admin_a)

    # COUNT pour la pagination + SELECT avec jointure sur l'organisation, quel que soit
    # le nombre d'utilisateurs. Sans select_related : une requête de plus par utilisateur.
    with django_assert_max_num_queries(2):
        response = client.get(USERS_URL)

    assert response.data["count"] == 16
