from {{cookiecutter.project_slug}}.common.serializers.base import BaseCodeReadOnlyModelSerializer
from {{cookiecutter.project_slug}}.products.models import Lineup


class DashboardLineupSerializer(BaseCodeReadOnlyModelSerializer):
    class Meta:
        model = Lineup
        fields = ["name", "code", "description", "is_default", "lineup_type"]
