from {{cookiecutter.project_slug}}.common.bases import services
from {{cookiecutter.project_slug}}.products.models import Brand


class BrandService(services.BaseModelService):
    model = Brand

    def get_or_create(self, get_data, default_data):
        brand, created = self.model.objects.get_or_create(
            **get_data, defaults=default_data
        )
        return brand

    def get_brands(self, **kwargs):
        return self.model.objects.filter(**kwargs)

    def get_brand_name(self, brand_code):
        brand_obj = self.read_by_code(code_value=brand_code)
        return brand_obj.name

    def create_brand(self, **brand):
        return self.create(**brand)
