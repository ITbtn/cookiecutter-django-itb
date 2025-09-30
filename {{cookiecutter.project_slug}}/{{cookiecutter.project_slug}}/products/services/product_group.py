from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ProtectedError

from {{cookiecutter.project_slug}}.common.bases.services import BaseModelService
from {{cookiecutter.project_slug}}.search.signals import task_es_registry_update

from ...rest_utils.exceptions import BadRequestException
from ..models import ProductGroup
from .page_layout_service import PageLayoutService


class ProductGroupService(BaseModelService):
    model = ProductGroup

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def list_by_catalog(self, **query_params):
        """
        We send list of ProductGroup based on the catalog
        :param query_params:
        :return:
        """
        from {{cookiecutter.project_slug}}.catalog.services.catalog_services import (
            CatalogRelationService,
            CatalogService,
        )

        catalog_service = CatalogService(
            tenant_code=self.get_tenant_code(), site_profile=self.site_profile
        )
        catalog_relation_service = CatalogRelationService()

        contact_group = None
        try:
            user = query_params.get("user")
            contact_group = user.contactperson.contact.contact_group
        except ObjectDoesNotExist:
            """
            What should we do in this case?
            Currently sending all ProductGroups saved in every catalog if
            user and contact group relation is not configured.
            """
            pass

        catalog_relations = (
            catalog_service.get_catalog_product_group_relations_by_content(
                content_type="contactgroup", content=contact_group
            )
        )
        product_groups_list = catalog_relation_service.get_content_object_list(
            qs=catalog_relations
        )

        return product_groups_list

    def get_or_create(self, defaults, **kwargs):
        obj, created = self.model.objects.get_or_create(defaults=defaults, **kwargs)
        return obj

    def update_field_values(self, **kwargs):
        if kwargs.get("page_layout_code"):
            page_layout = PageLayoutService(
                tenant_code=self.tenant_code, site_profile=self.site_profile
            ).get_page_layout(code=kwargs["page_layout_code"])
            kwargs["page_layout_id"] = page_layout.id
        else:
            kwargs["page_layout"] = None

        parent_group_code = kwargs.pop("parent", None)
        if parent_group_code == "":
            kwargs["parent"] = None
        elif parent_group_code:
            kwargs["parent"] = self.read_by_code(code_value=parent_group_code)

        return kwargs

    def create_product_group(self, **kwargs):
        """
        Create product group
        :param kwargs: product group data
        :return: product group instance or raise exception
        """
        try:
            kwargs = self.update_field_values(**kwargs)
            kwargs.update(
                {"tenant_code": self.get_tenant_code(), "created_by": self.user}
            )

            return self.create(**kwargs)
        except Exception as e:
            raise BadRequestException(message=f"{e.messages[0]}")

    def update_product_group(self, instance, **kwargs):
        """
        Update product group
        :param instance: product group instance
        :param kwargs: product group data
        :return: product group instance or raise exception
        """
        try:
            kwargs = self.update_field_values(**kwargs)
            kwargs.update(
                {"tenant_code": self.get_tenant_code(), "updated_by": self.user}
            )
            return self.update_model_instance(instance, **kwargs)
        except Exception as e:
            raise BadRequestException(message=f"{e.messages[0]}")

    def delete_product_group(self, instance):
        """
        Delete product group
        :param instance: product group instance
        :return: product group instance or raise exception
        """
        try:
            instance.delete()
        except ProtectedError:
            raise BadRequestException("Can't delete product group. It is in use.")

    def update_product_group_in_elastic(self, code):
        product_group = self.read_by_code(code_value=code)
        task_es_registry_update.delay(
            product_group.pk,
            product_group._meta.app_label,
            product_group._meta.concrete_model.__name__,
        )
