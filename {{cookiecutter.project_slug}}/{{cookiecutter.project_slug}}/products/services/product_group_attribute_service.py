from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from {{cookiecutter.project_slug}}.attributes.models.attribute import Attribute
from {{cookiecutter.project_slug}}.common.bases import BaseModelService
from {{cookiecutter.project_slug}}.products.exceptions import (
    ProductGroupAttributeAlreadyExistsException,
    ProductGroupAttributeNotFoundException,
    ProductGroupNotFoundException,
)

from ..models import ProductAttribute, ProductGroupAttribute


class ProductGroupAttributeService(BaseModelService):
    model = ProductGroupAttribute

    def get_search_attribute_instance(self, product_group_code, attribute_code):
        search_attribute_instance = None

        try:
            search_attribute_instance = self.model.objects.get(
                product_group__code=product_group_code, attribute_code=attribute_code
            )
        except self.model.DoesNotExist:
            raise ProductGroupAttributeNotFoundException

        return search_attribute_instance

    def get_search_attributes_by_product_group_code(self, product_group_code):
        attribute_codes = (
            ProductAttribute.objects.filter(
                Q(product__product_group__code=product_group_code)
                | Q(product__product_group__parent__code=product_group_code),
                is_available=True,
                attribute__is_available=True,
                tenant_code=self.get_tenant_code(),
            )
            .values_list("attribute__code", flat=True)
            .order_by("-id")
        )

        attribute_codes = set(attribute_codes)
        filtered_attribute_code = [
            attribute for attribute in attribute_codes if not attribute.isnumeric()
        ]

        search_attributes = list(
            self.model.objects.filter(
                product_group__code=product_group_code,
                product_group__tenant_code=self.get_tenant_code(),
                is_active=True,
                attribute_code__in=filtered_attribute_code,
            ).values_list("attribute_code", flat=True)
        )

        response = [
            {
                "product_group_code": product_group_code,
                "is_selected": True if attribute in search_attributes else False,
                "attribute_code": attribute,
                "attribute_name": Attribute.objects.get(code=attribute).name,
            }
            for attribute in filtered_attribute_code
        ]
        return response

    def process_search_attributes(
        self, product_group_code, new_search_attribute_codes, created_by
    ):
        # cyclic import
        from {{cookiecutter.project_slug}}.products.services import ProductGroupService

        existing_search_attributes = self.model.objects.filter(
            product_group__code=product_group_code,
            product_group__tenant_code=self.get_tenant_code(),
            is_active=True,
        ).values_list("attribute_code", flat=True)
        existing_search_attributes = list(existing_search_attributes)
        to_create_attriutes = []
        for search_attribute_code in new_search_attribute_codes:
            if search_attribute_code["attribute_code"] in existing_search_attributes:
                existing_search_attributes.remove(
                    search_attribute_code["attribute_code"]
                )
            else:
                to_create_attriutes.append(search_attribute_code["attribute_code"])

        # delete remaining attributes that are not sent from FE
        self.model.objects.filter(
            attribute_code__in=existing_search_attributes
        ).delete()

        # create attribute that are newly sent from FE
        if to_create_attriutes:
            self.create_search_attributes(
                product_group_code=product_group_code,
                search_attribute_codes=to_create_attriutes,
                created_by=created_by,
            )

        search_attributes = self.get_search_attributes_by_product_group_code(
            product_group_code=product_group_code
        )
        ProductGroupService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        ).update_product_group_in_elastic(code=product_group_code)
        return search_attributes

    def create_search_attributes(
        self, product_group_code, search_attribute_codes, created_by
    ):
        from ..services.product_group import ProductGroupService

        try:
            product_group_instance = ProductGroupService(
                tenant_code=self.tenant_code, site_profile=self.site_profile
            ).read_by_code(code_value=product_group_code)
        except ObjectDoesNotExist:
            raise ProductGroupNotFoundException

        product_group_search_attribute_objects = [
            self.model(
                product_group=product_group_instance,
                is_active=True,
                attribute_code=attribute_code,
                created_by=created_by,
            )
            for attribute_code in search_attribute_codes
        ]
        self.model.objects.bulk_create(product_group_search_attribute_objects)
        return product_group_search_attribute_objects

    def get_search_attribute_codes_by_product_group_code(
        self, product_group_code: str
    ) -> list:
        """Get all available search attribute code for the product group

        Args:
            product_group_code (str): product group code for search attributes

        Returns:
            list of attribute codes used as search attribute
        """
        search_attributes = (
            self.model.objects.filter(
                product_group__code=product_group_code,
                product_group__tenant_code=self.get_tenant_code(),
                is_active=True,
            )
            .select_related("product_group")
            .values_list("attribute_code", flat=True)
        )
        return list(search_attributes)

    def create_search_attribute(
        self, product_group_code: str, attribute_code: str, created_by
    ) -> ProductGroupAttribute:
        """Create/Connect attribute with ProductGroupSearchAttribute

        Args:
            product_group_code (str): attribute will be connected to this group
            attribute_code (str): the attribute which needs to be connected
            created_by (User): User instance who is creating the connection

        Returns:
            instance (ProductGroupAttribute): A newly created ProductGroupAttribute object

        Raises:
              ProductGroupNotFoundException: Product group unavailable
              ProductGroupAttributeAlreadyExistsException: Connection between attribute & group already exist

        """
        from ..services.product_group import ProductGroupService

        try:
            product_group_instance = ProductGroupService(
                tenant_code=self.tenant_code, site_profile=self.site_profile
            ).read_by_code(code_value=product_group_code)
        except ObjectDoesNotExist:
            raise ProductGroupNotFoundException

        # raise exception if already exists
        if self.model.objects.filter(
            product_group=product_group_instance,
            attribute_code=attribute_code,
        ).exists():
            raise ProductGroupAttributeAlreadyExistsException

        data = self.model.objects.create(
            product_group=product_group_instance,
            is_active=True,
            attribute_code=attribute_code,
            created_by=created_by,
        )

        # reindex
        ProductGroupService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        ).update_product_group_in_elastic(code=product_group_instance.code)
        return data

    def delete(self, instance) -> None:
        """Delete/Disconnect attribute from ProductGroupSearchAttribute

        Args:
            instance (ProductGroupAttribute): model instance to delete

        Returns:
        """
        instance.delete()
