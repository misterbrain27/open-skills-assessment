from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, viewsets

from core.mixins import OrganizationScopedMixin

from .models import User
from .permissions import IsOrgAdmin, IsOrganizationMember
from .serializers import UserSerializer


@extend_schema_view(
    get=extend_schema(
        summary="Profil de l'utilisateur connecté",
        description="Renvoie l'utilisateur connecté et son organisation.",
    ),
)
class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsOrganizationMember]

    def get_object(self):
        return self.request.user


@extend_schema_view(
    list=extend_schema(summary="Lister les utilisateurs de mon organisation"),
    retrieve=extend_schema(summary="Détail d'un utilisateur de mon organisation"),
    create=extend_schema(
        summary="Créer un utilisateur dans mon organisation",
        description="Réservé aux admins. Le compte est créé sans mot de passe utilisable.",
    ),
    update=extend_schema(summary="Modifier un utilisateur (admins)"),
    partial_update=extend_schema(summary="Modifier partiellement un utilisateur (admins)"),
    destroy=extend_schema(summary="Supprimer un utilisateur (admins)"),
)
class UserViewSet(OrganizationScopedMixin, viewsets.ModelViewSet):
    # select_related : l'organisation imbriquée vient dans la même requête que les
    # utilisateurs, sinon une requête par ligne. order_by : la pagination exige un ordre
    # stable, sinon une même ligne peut apparaître sur deux pages.
    queryset = User.objects.select_related("organization").order_by("email")
    serializer_class = UserSerializer
    # Par défaut le plus restrictif : get_permissions() n'ouvre que la lecture.
    permission_classes = [IsOrgAdmin]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsOrganizationMember()]
        return super().get_permissions()
