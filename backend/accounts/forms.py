from django.contrib.auth.forms import AdminUserCreationForm
from django.core.exceptions import ValidationError

from .models import Organization, User


class UserCreationForm(AdminUserCreationForm):
    class Meta(AdminUserCreationForm.Meta):
        model = User
        fields = ("email", "organization", "role")

    def clean_organization(self) -> Organization:
        # Le formulaire n'a pas de champ is_superuser : Django ne vérifie donc pas la
        # CheckConstraint, et l'oubli finirait en IntegrityError (500) à l'enregistrement.
        # Ce formulaire ne crée jamais de superuser : l'organisation est obligatoire.
        organization = self.cleaned_data.get("organization")
        if organization is None:
            raise ValidationError("Un utilisateur doit appartenir à une organisation.")
        return organization
