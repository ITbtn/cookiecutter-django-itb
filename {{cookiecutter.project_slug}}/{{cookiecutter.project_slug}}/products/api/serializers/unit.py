from rest_framework import serializers

from {{cookiecutter.project_slug}}.products.models import Unit


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ["id", "code", "name", "amount"]
        read_only_fields = ["id"]
