from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import generics, serializers, status, viewsets
from rest_framework.exceptions import NotAuthenticated
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from core.mixins import OrganizationScopedMixin

from .cookies import REFRESH_COOKIE_NAME, delete_refresh_cookie, set_refresh_cookie
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


# Le refresh token ne figure jamais dans un corps de réponse : il part dans le cookie.
ACCESS_TOKEN_RESPONSE = inline_serializer(
    name="AccessToken",
    fields={"access": serializers.CharField()},
)


# Les trois vues suivantes héritent de simplejwt permission_classes = () et
# authentication_classes = () : pour se connecter, on n'est pas encore connecté, et pour le
# refresh et le logout, posséder le cookie suffit à prouver son droit.


class LoginView(TokenObtainPairView):
    # JSON seulement : un formulaire posté depuis un autre site reçoit 415 (login CSRF).
    parser_classes = [JSONParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(
        summary="Connexion",
        description=(
            "Renvoie l'access token dans le corps. Le refresh token est posé dans un cookie "
            "HttpOnly, envoyé seulement vers /api/auth/. Limité à 5 tentatives par minute."
        ),
        responses={
            200: ACCESS_TOKEN_RESPONSE,
            401: OpenApiResponse(description="Identifiants invalides."),
            429: OpenApiResponse(description="Trop de tentatives."),
        },
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        set_refresh_cookie(response, response.data.pop("refresh"))
        return response


class RefreshView(TokenRefreshView):
    @extend_schema(
        summary="Renouveler l'access token",
        description=(
            "Lit le refresh token dans le cookie, renvoie un nouvel access token et remplace "
            "le cookie par un nouveau refresh token (l'ancien est mis sur liste noire)."
        ),
        request=None,
        responses={
            200: ACCESS_TOKEN_RESPONSE,
            401: OpenApiResponse(description="Cookie absent, refresh token invalide ou révoqué."),
        },
    )
    def post(self, request, *args, **kwargs):
        # Comme TokenViewBase.post(), mais le refresh vient du cookie et non du corps.
        token = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if not token:
            raise NotAuthenticated("Aucun refresh token.")
        serializer = self.get_serializer(data={"refresh": token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e
        except User.DoesNotExist as e:
            # Le serializer de simplejwt ne gère pas un compte supprimé après le login (500).
            raise InvalidToken("Utilisateur introuvable.") from e

        response = Response({"access": serializer.validated_data["access"]})
        set_refresh_cookie(response, serializer.validated_data["refresh"])
        return response


class LogoutView(TokenBlacklistView):
    @extend_schema(
        summary="Déconnexion",
        description=(
            "Met le refresh token du cookie sur liste noire et supprime le cookie. L'access "
            "token reste valable jusqu'à son expiration (15 minutes au plus)."
        ),
        request=None,
        responses={204: None},
    )
    def post(self, request, *args, **kwargs):
        token = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if token:
            serializer = self.get_serializer(data={"refresh": token})
            try:
                serializer.is_valid(raise_exception=True)
            except TokenError:
                # Expiré ou déjà sur liste noire : il n'y a plus rien à révoquer.
                pass

        # Toujours 204 : un logout répété, ou sans cookie, aboutit au même état.
        response = Response(status=status.HTTP_204_NO_CONTENT)
        delete_refresh_cookie(response)
        return response
