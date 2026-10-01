import factory

from accounts.models import Organization, User


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Organisation {n}")


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"utilisateur{n}@example.com")
    organization = factory.SubFactory(OrganizationFactory)
    # Hache le mot de passe comme set_password : user.check_password(...) fonctionne.
    password = factory.django.Password("mot-de-passe-de-test")
