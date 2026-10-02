from rest_framework.permissions import BasePermission


class IsOrganizationMember(BasePermission):
    """Utilisateur authentifié et rattaché à une organisation.

    Le superuser de plateforme, sans organisation, est refusé : il passe par l'admin Django.
    Sans cette règle, le filtre par organisation deviendrait `organization=None`.
    """

    def has_permission(self, request, view) -> bool:
        # is_authenticated d'abord : un AnonymousUser n'a pas d'attribut organization_id.
        # organization_id plutôt qu'organization : la colonne est déjà chargée, pas de requête.
        return bool(request.user.is_authenticated and request.user.organization_id)


class IsOrgAdmin(IsOrganizationMember):
    """Membre de l'organisation et administrateur de celle-ci."""

    def has_permission(self, request, view) -> bool:
        return super().has_permission(request, view) and request.user.is_org_admin
