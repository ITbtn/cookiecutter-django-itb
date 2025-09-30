from {{cookiecutter.project_slug}}.common.serializers.base import BaseCodeReadOnlyModelSerializer
from {{cookiecutter.project_slug}}.products.models import PageLayout


class PageLayoutsSerializer(BaseCodeReadOnlyModelSerializer):
    class Meta:
        model = PageLayout
        fields = ["code", "description", "is_available"]
