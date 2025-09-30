from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ProtectedError

from {{cookiecutter.project_slug}}.common.bases import BaseModelService
from {{cookiecutter.project_slug}}.products.models.page_layout import PageLayout
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException


class PageLayoutService(BaseModelService):
    model = PageLayout

    def get_page_layout(self, code):
        """
        Get Page Layout by code
        :param code:
        :return: Page Layout object or raise exception
        """
        try:
            return self.read_by_code(code_value=code)
        except ObjectDoesNotExist:
            raise BadRequestException("Invalid Page Layout Code.")


    def delete_page_layout(self, instance):
        """
        Delete Page Layout
        :param instance: Page Layout object
        :return: None if success or raise exception
        """
        try:
            instance.delete()
        except ProtectedError:
            raise BadRequestException("Can't delete page layout. It is in use.")
