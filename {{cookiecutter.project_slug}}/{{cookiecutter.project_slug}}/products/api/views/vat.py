from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.api.serializers.vat import VatSerializer
from {{cookiecutter.project_slug}}.products.services.vat import VatService


class VatListCreateAPIView(api_views.BaseListCreateAPIView):
    service_class = VatService
    serializer_class = VatSerializer
