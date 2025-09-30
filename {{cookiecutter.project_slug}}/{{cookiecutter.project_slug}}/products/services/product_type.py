from {{cookiecutter.project_slug}}.common.bases.services import BaseModelService

from ..models import ProductGroup, ProductType


class ProductTypeService(BaseModelService):
    model = ProductType

    def get_or_create(self, get_data, default_data):
        product_type, created = self.model.objects.get_or_create(
            **get_data, defaults=default_data
        )
        return product_type

    def get_dummy_type(self):
        none_type = self.list(**{"system_type": "none"})
        dummy_type = ""
        if none_type.exists() and len(none_type) > 0:
            dummy_type = none_type.first()
        else:
            dummy_type = self.create(
                **{
                    "name": "None",
                    "system": "True",
                    "description": "Dummy Product Type",
                }
            )
        return dummy_type

    def list_list_all_groups_for_type(self, type_code):
        product_type = self.read_by_code(
            code_value=type_code, tenant_code=self.get_tenant_code()
        )
        qs = (
            ProductGroup.objects.filter(
                primary_products__product_type__system_type=product_type.system_type
            )
            .distinct()
            .exclude(name__in=["Laptops", "Tablets", "SIM"])
        )
        return qs

    def get_product_type_by_code(self, code):
        return self.read_by_code(code_value=code)

    def create_product_type(self, **product_type_data):
        return self.create(**product_type_data)
