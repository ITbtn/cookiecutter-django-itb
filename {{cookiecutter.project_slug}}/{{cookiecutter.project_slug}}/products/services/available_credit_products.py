from {{cookiecutter.project_slug}}.common.bases.services import BaseModelService

from ..models import AvailableCreditProduct


class AvailableCreditProductService(BaseModelService):
    model = AvailableCreditProduct
