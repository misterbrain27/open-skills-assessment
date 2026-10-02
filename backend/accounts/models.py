from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models import TimeStampedModel

from .managers import UserManager


class Organization(TimeStampedModel):
    """Entreprise cliente : toutes les données d'API seront filtrées par organisation."""

    name = models.CharField("nom", max_length=150, unique=True)

    class Meta:
        verbose_name = "organisation"

    def __str__(self) -> str:
        return self.name


class User(AbstractUser, TimeStampedModel):
    """Utilisateur identifié par son email et rattaché à une organisation."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Administrateur"
        RECRUITER = "recruiter", "Recruteur"

    username = None
    email = models.EmailField("adresse email", unique=True)
    # Moindre privilège : un oubli donne le rôle le plus restreint, pas le plus large.
    role = models.CharField("rôle", max_length=20, choices=Role, default=Role.RECRUITER)
    # Vide autorisé pour le seul superuser (compte de plateforme, voir la contrainte).
    # PROTECT : supprimer une organisation ne doit pas effacer ses utilisateurs en cascade.
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="organisation",
    )

    USERNAME_FIELD = "email"
    # createsuperuser demande déjà USERNAME_FIELD et le mot de passe.
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "utilisateur"
        constraints = [
            # Garantie en base, quel que soit le chemin de création (admin, script, save()).
            models.CheckConstraint(
                condition=models.Q(is_superuser=True) | models.Q(organization__isnull=False),
                name="accounts_user_organization_required_unless_superuser",
                violation_error_message="Un utilisateur doit appartenir à une organisation.",
            ),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def is_org_admin(self) -> bool:
        # Seul endroit où le rôle est comparé : le reste du code appelle cette propriété.
        return self.role == self.Role.ADMIN
