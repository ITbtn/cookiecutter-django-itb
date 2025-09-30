from {{cookiecutter.project_slug}}.common.serializers.base import BaseCodeReadOnlyModelSerializer
from {{cookiecutter.project_slug}}.products.models import Promotion


class PromotionSerializer(BaseCodeReadOnlyModelSerializer):
    class Meta:
        model = Promotion
        exclude = ["id", "created_by", "updated_by", "created_at", "updated_at"]
        read_only_fields = ["code"]
