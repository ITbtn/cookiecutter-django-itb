from {{cookiecutter.project_slug}}.common.serializers.base import BaseCodeReadOnlyModelSerializer
from {{cookiecutter.project_slug}}.products.models import Unit


class UnitSerializer(BaseCodeReadOnlyModelSerializer):
    class Meta:
        model = Unit
        fields = [
            "id",
            "code",
            "name",
            "amount",
            "min_amount",
            "max_amount",
            "order_unit",
        ]
        read_only_fields = ["id"]
        ref_name = "dashboard_unit_serializer"
