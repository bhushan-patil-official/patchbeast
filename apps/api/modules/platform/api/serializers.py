from rest_framework import serializers


class PublicConfigSerializer(serializers.Serializer):
    flags = serializers.DictField(child=serializers.BooleanField())
    contact_email = serializers.EmailField()
    kill_switch = serializers.BooleanField()
