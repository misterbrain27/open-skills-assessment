from rest_framework import serializers

from .models import Organization, User


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name"]


class UserSerializer(serializers.ModelSerializer):
    # Imbriquée et en lecture seule : une organisation envoyée dans le JSON est ignorée.
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = User
        # Liste explicite : jamais de password, is_staff ou is_superuser exposés.
        fields = ["id", "email", "first_name", "last_name", "role", "organization"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        # Sans mot de passe : le compte reste inutilisable jusqu'à ce que l'utilisateur
        # définisse le sien. L'admin de l'organisation ne connaît jamais ce mot de passe.
        return User.objects.create_user(**validated_data)
