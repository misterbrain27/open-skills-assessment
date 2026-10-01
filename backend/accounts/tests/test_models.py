import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

from accounts.models import User
from accounts.tests.factories import OrganizationFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_create_user_normalise_l_email_et_hache_le_mot_de_passe():
    user = User.objects.create_user(
        "alice@EXAMPLE.COM", "mot-de-passe", organization=OrganizationFactory()
    )

    assert user.email == "alice@example.com"
    assert user.password != "mot-de-passe"
    assert user.check_password("mot-de-passe")
    assert not user.is_staff
    assert not user.is_superuser
    assert user.role == User.Role.RECRUITER


def test_create_user_sans_email_echoue():
    with pytest.raises(ValueError, match="email"):
        User.objects.create_user("", "mot-de-passe", organization=OrganizationFactory())


def test_create_user_sans_organisation_echoue():
    with pytest.raises(ValueError, match="organisation"):
        User.objects.create_user("bob@example.com", "mot-de-passe")


def test_create_superuser_est_staff_et_superuser_sans_organisation():
    user = User.objects.create_superuser("admin@example.com", "mot-de-passe")

    assert user.is_staff
    assert user.is_superuser
    assert user.organization is None


@pytest.mark.parametrize("drapeau", ["is_staff", "is_superuser"])
def test_create_superuser_refuse_un_drapeau_a_false(drapeau):
    with pytest.raises(ValueError, match=drapeau):
        User.objects.create_superuser("admin@example.com", "mot-de-passe", **{drapeau: False})


def test_la_base_refuse_un_utilisateur_sans_organisation():
    # save() direct, sans le manager : seule la CheckConstraint peut l'arrêter.
    with pytest.raises(IntegrityError, match="organization_required_unless_superuser"):
        User(email="carol@example.com").save()


def test_l_email_est_unique():
    UserFactory(email="dave@example.com")

    with pytest.raises(IntegrityError):
        UserFactory(email="dave@example.com")


def test_supprimer_une_organisation_qui_a_des_utilisateurs_echoue():
    user = UserFactory()

    with pytest.raises(ProtectedError):
        user.organization.delete()
