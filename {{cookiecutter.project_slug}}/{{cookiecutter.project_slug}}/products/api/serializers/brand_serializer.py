from {{cookiecutter.project_slug}}.common.serializers.base import BaseCodeReadOnlyModelSerializer
from {{cookiecutter.project_slug}}.products.models import Brand


class BrandSerializer(BaseCodeReadOnlyModelSerializer):
    class Meta:
        model = Brand
        exclude = ["id", "created_by", "updated_by", "created_at", "updated_at"]
        read_only_fields = ["code"]

        ref_name = "brand_serializer"
