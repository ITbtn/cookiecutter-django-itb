from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ProtectedError

from {{cookiecutter.project_slug}}.common.bases import BaseModelService
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException

from ..models.family_series import Family, Series


class FamilyService(BaseModelService):
    model = Family

    def read_by_code(self, code_value, **kwargs):
        """
        Get Family by code
        :param code:
        :return: Family object or raise exception
        """
        try:
            return super().read_by_code(code_value=code_value, **kwargs)
        except ObjectDoesNotExist:
            raise BadRequestException("Family doesn't exist.")

    def delete_family(self, instance):
        """
        Delete Family
        :param instance: Family object
        :return: None if success or raise exception
        """
        try:
            instance.delete()
        except ProtectedError:
            raise BadRequestException("Can't delete the family. It is in use.")


class SeriesService(BaseModelService):
    model = Series

    def read_by_code(self, code_value, **kwargs):
        """
        Get Series by code
        :param code:
        :return: Series object or raise exception
        """
        try:
            return super().read_by_code(code_value=code_value, **kwargs)
        except ObjectDoesNotExist:
            raise BadRequestException("Series doesn't exist.")

    def list(self, **query_params):
        queryset = super().list(**query_params)
        return queryset.select_related("family")

    def update_field_values(self, **data):
        if data.get("family_code"):
            data["family"] = FamilyService(
                tenant_code=self.tenant_code,
                site_profile=self.site_profile,
            ).read_by_code(code_value=data["family_code"])
        elif data.get("family_code") == "":
            # when family code is empty string, that means user want to remove the family
            data["family"] = None
        else:
            data["family"] = None
        return data

    def create_series(self, **kwargs):
        try:
            kwargs = self.update_field_values(**kwargs)
            kwargs.update(
                {
                    "tenant_code": self.get_tenant_code(),
                    "created_by": self.kwargs.get("user"),
                }
            )
            return self.create(**kwargs)
        except Exception as exp:
            raise BadRequestException(message=f"{exp.messages[0]}")

    def update_series(self, instance, **kwargs):
        kwargs = self.update_field_values(**kwargs)
        # We all not update code value
        kwargs.pop("code", None)
        kwargs.update({"updated_by": self.kwargs.get("user")})
        return self.update_model_instance(instance, **kwargs)

    def delete_series(self, instance):
        """
        Delete the Series
        :param instance: Series object
        :return: None if success or raise exception
        """
        try:
            instance.delete()
        except ProtectedError:
            raise BadRequestException("Can't delete the Series. It is in use.")
