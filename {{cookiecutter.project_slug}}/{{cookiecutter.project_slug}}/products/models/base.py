from {{cookiecutter.project_slug}}.common.models import BaseHistoryModel
from {{cookiecutter.project_slug}}.common.utils import generate_unique_code


class ProductBase(BaseHistoryModel):
    class Meta(BaseHistoryModel.Meta):
        abstract = True

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.code:
            self.code = generate_unique_code()
        super().save(force_insert, force_update, using, update_fields)
