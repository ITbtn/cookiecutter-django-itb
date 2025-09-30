from {{cookiecutter.project_slug}}.products.models import Lineup
from {{cookiecutter.project_slug}}.common.bases import services


class LineupService(services.BaseModelService):
    model = Lineup


