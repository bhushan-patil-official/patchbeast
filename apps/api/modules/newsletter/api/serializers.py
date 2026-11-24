from rest_framework import serializers


class SubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    game = serializers.SlugField(
        required=False,
        allow_blank=True,
        help_text="game slug: only that game's changes; empty = all games",
    )
    website = serializers.CharField(
        required=False, allow_blank=True, help_text="honeypot: must stay empty"
    )


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=64)


class OkSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
