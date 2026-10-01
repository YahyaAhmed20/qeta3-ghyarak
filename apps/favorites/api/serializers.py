from rest_framework import serializers

from apps.favorites.models import Favorite


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = [
            "id",
            "customer",
            "product",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "customer",
            "product",
            "created_at",
        ]