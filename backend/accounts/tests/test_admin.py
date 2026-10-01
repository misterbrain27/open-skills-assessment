import pytest
from django.urls import reverse

from accounts.models import User
from accounts.tests.factories import OrganizationFactory, UserFactory

pytestmark = pytest.mark.django_db


# Les vérifications de `check` ne couvrent pas le rendu : un fieldset qui citerait encore
# `username` ne casserait qu'à l'affichage de la page.
@pytest.mark.parametrize(
    "url_name",
    [
        "admin:accounts_user_changelist",
        "admin:accounts_user_add",
        "admin:accounts_organization_changelist",
    ],
)
def test_les_pages_d_admin_s_affichent(admin_client, url_name):
    UserFactory()

    response = admin_client.get(reverse(url_name))

    assert response.status_code == 200


def test_la_fiche_d_un_utilisateur_s_affiche(admin_client):
    user = UserFactory()

    response = admin_client.get(reverse("admin:accounts_user_change", args=[user.pk]))

    assert response.status_code == 200


def test_l_admin_cree_un_utilisateur_avec_un_mot_de_passe_hache(admin_client):
    organization = OrganizationFactory()

    response = admin_client.post(
        reverse("admin:accounts_user_add"),
        {
            "email": "eve@example.com",
            "organization": organization.pk,
            "role": User.Role.ADMIN,
            "usable_password": "true",
            "password1": "Un-mot-de-passe-solide-42",
            "password2": "Un-mot-de-passe-solide-42",
        },
    )

    assert response.status_code == 302
    user = User.objects.get(email="eve@example.com")
    assert user.organization == organization
    assert user.check_password("Un-mot-de-passe-solide-42")


def test_l_admin_refuse_un_utilisateur_sans_organisation(admin_client):
    response = admin_client.post(
        reverse("admin:accounts_user_add"),
        {
            "email": "frank@example.com",
            "role": User.Role.RECRUITER,
            "usable_password": "true",
            "password1": "Un-mot-de-passe-solide-42",
            "password2": "Un-mot-de-passe-solide-42",
        },
    )

    # Le formulaire valide les contraintes du modèle : erreur affichée, pas de 500.
    assert response.status_code == 200
    assert "Un utilisateur doit appartenir à une organisation." in response.content.decode()
    assert not User.objects.filter(email="frank@example.com").exists()


def test_l_admin_refuse_de_retirer_superuser_a_un_compte_sans_organisation(admin_client):
    # Ici is_superuser et organization sont dans le formulaire : la CheckConstraint est
    # vérifiée par Django, l'erreur s'affiche au lieu d'une 500.
    other = User.objects.create_superuser("grace@example.com", "mot-de-passe")

    response = admin_client.post(
        reverse("admin:accounts_user_change", args=[other.pk]),
        {
            "email": other.email,
            "role": User.Role.RECRUITER,
            "is_active": "on",
            "is_staff": "on",
            "date_joined_0": "2026-10-01",
            "date_joined_1": "12:00:00",
        },
    )

    assert response.status_code == 200
    assert "Un utilisateur doit appartenir à une organisation." in response.content.decode()
    other.refresh_from_db()
    assert other.is_superuser


def test_un_superuser_se_connecte_a_l_admin_avec_son_email(client):
    User.objects.create_superuser("heidi@example.com", "Un-mot-de-passe-solide-42")

    # Le champ du formulaire de connexion s'appelle toujours « username » : il reçoit
    # la valeur de USERNAME_FIELD, ici l'email.
    response = client.post(
        reverse("admin:login"),
        {"username": "heidi@example.com", "password": "Un-mot-de-passe-solide-42"},
    )

    assert response.status_code == 302
    assert client.get(reverse("admin:index")).status_code == 200
