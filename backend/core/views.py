import logging

from django.db import DatabaseError, connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

StatusSerializer = inline_serializer("Status", fields={"status": serializers.CharField()})


class LivenessView(APIView):
    # Sonde appelée par l'orchestrateur sans identifiants : seule exception justifiée
    # à IsAuthenticated. Elle ne révèle rien, elle répond juste que le processus vit.
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Liveness : le processus répond",
        description="Ne touche à aucune dépendance : un échec entraîne un redémarrage.",
        responses={200: StatusSerializer},
    )
    def get(self, request):
        return Response({"status": "ok"})


class ReadinessView(APIView):
    # Même justification que la liveness : appelée sans identifiants par l'orchestrateur.
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Readiness : l'API peut servir des requêtes",
        description="Vérifie la connexion à PostgreSQL. 503 si elle est indisponible.",
        responses={200: StatusSerializer, 503: StatusSerializer},
    )
    def get(self, request):
        try:
            connection.ensure_connection()
        except DatabaseError:
            # Le détail (hôte, utilisateur, version) va dans les logs, jamais dans la
            # réponse : la sonde est publique.
            logger.exception("Base de données indisponible")
            return Response({"status": "unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"status": "ok"})
