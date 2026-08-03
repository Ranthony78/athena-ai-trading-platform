from rest_framework import serializers


class DashboardSerializer(serializers.Serializer):
    application = serializers.CharField()
    version = serializers.CharField()
    status = serializers.CharField()
    user = serializers.DictField()
    modules = serializers.DictField()