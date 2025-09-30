from django.db import models

from {{cookiecutter.project_slug}}.common.models import AbstractBaseModel
from {{cookiecutter.project_slug}}.products.models.product import Product


class ProductIAN(AbstractBaseModel):

    ian = models.CharField(max_length=128)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="ians")

    class Meta:
        unique_together = (("ian", "product"),)

    def __str__(self):
        return self.ian
