class OrganizationScopedMixin:
    """Limite une vue DRF aux données de l'organisation de l'utilisateur connecté.

    À placer AVANT la classe de vue DRF dans l'héritage : sinon, Python trouve d'abord
    le get_queryset() de DRF et celui-ci n'est jamais appelé.
    Suppose une permission qui garantit une organisation (IsOrganizationMember).
    """

    # Une ressource rattachée indirectement le redéfinit (ex. "assessment__organization").
    organization_field = "organization"

    def get_queryset(self):
        # Filtrer ici couvre toutes les actions, y compris list, que les permissions
        # d'objet ne protègent pas. Un objet d'une autre organisation donne donc un 404.
        queryset = super().get_queryset()
        return queryset.filter(**{self.organization_field: self.request.user.organization_id})

    def perform_create(self, serializer):
        # L'organisation vient de l'utilisateur, jamais du JSON envoyé.
        serializer.save(**{self.organization_field: self.request.user.organization})
