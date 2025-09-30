from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.cart_validator.exception import (
    MinimumAmountCrossingMax,
    MinimumAmountCanNotBeZero,
    OrderUnitCanNotBeZero,
    MinAmountCrossingOrderUnitException,
    OrderUnitCrossingMaxAmountException,
)
from {{cookiecutter.project_slug}}.common.validators import ScreenMethodValidator
from {{cookiecutter.project_slug}}.products.models.base import ProductBase


class Unit(ProductBase):
    validators = [ScreenMethodValidator]

    name = models.CharField(max_length=50, help_text=_("Name of Unit."))
    amount = models.IntegerField(default=1, help_text=_("Amount of Unit. default 1"))
    min_amount = models.IntegerField(
        blank=True,
        default=1,
        verbose_name=_("Minimum Amount"),
        help_text=_("The minimum amount that needs to be purchased to be eligible to place an order."),
    )
    max_amount = models.IntegerField(
        blank=True,
        default=0,
        verbose_name=_("Maximum Amount"),
        help_text=_("The maximum amount that can be purchased."),
    )
    order_unit = models.IntegerField(
        blank=True,
        default=1,
        verbose_name=_("Order Unit"),
        help_text=_("The product can only by ordered per unit.")
    )

    def screen_max_amount(self):
        if self.max_amount > 0 and self.min_amount > self.max_amount:
            raise MinimumAmountCrossingMax

    def screen_min_amount(self):
        if self.min_amount < 1:
            raise MinimumAmountCanNotBeZero
        if self.min_amount > self.order_unit:
            raise MinAmountCrossingOrderUnitException

    def screen_order_unit(self):
        if self.order_unit < 1:
            raise OrderUnitCanNotBeZero
        if self.max_amount != 0 and self.order_unit > self.max_amount:
            raise OrderUnitCrossingMaxAmountException

    def __str__(self):
        # Need to specify format
        return self.name + " (" + str(self.amount) + ")"
