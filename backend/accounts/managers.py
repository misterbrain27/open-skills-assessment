from typing import Any

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Manager du User sans username : l'email sert d'identifiant."""

    # Rend le manager disponible dans les migrations de données (RunPython).
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields: Any):
        if not email:
            raise ValueError("L'email est obligatoire.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        # set_password hache le mot de passe ; un mot de passe None devient inutilisable.
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any):
        # Les valeurs par défaut sont posées AVANT de construire l'objet : posées après,
        # elles n'auraient aucun effet (bug de l'ancien projet).
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        # Même règle que la CheckConstraint du modèle, mais avec un message clair.
        if not extra_fields["is_superuser"] and extra_fields.get("organization") is None:
            raise ValueError("Un utilisateur doit appartenir à une organisation.")
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields: Any):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields["is_staff"] is not True:
            raise ValueError("Un superuser doit avoir is_staff=True.")
        if extra_fields["is_superuser"] is not True:
            raise ValueError("Un superuser doit avoir is_superuser=True.")
        return self._create_user(email, password, **extra_fields)
