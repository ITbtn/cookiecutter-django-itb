from {{cookiecutter.project_slug}}.common.bases import services
from {{cookiecutter.project_slug}}.products.models import Unit


class UnitService(services.BaseModelService):
    model = Unit


