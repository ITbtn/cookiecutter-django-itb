from enum import Enum

from django.utils.translation import gettext_lazy as _


def add_choices(cls):
    """
    Add choices to the class
    :param cls:
    :return cls:

    Add this as decorator on top of the class we are using for choices in model
    This will add choices to the class based on the class variables
    For example:
    @add_choices
    class TestClass:
        FIRST_CHOICE = "first_choice"
        SECOND_CHOICE = "second_choice"
    This will automatically add choices to the class as follows
    TestClass.CHOICES = [   ("first_choice", "First Choice"),
                            ("second_choice", "Second Choice")
                        ]
    """

    def capitalize(input_string):
        return " ".join(word.capitalize() for word in input_string.split("_"))

    if issubclass(cls, Enum):
        setattr(cls, "CHOICES", [(item.value, _(capitalize(item.value))) for item in cls])
    else:
        cls.CHOICES = [
            (cls.__dict__[key], _(capitalize(key)))
            for key, value in cls.__dict__.items()
            if not key.startswith("__") and not callable(value)
        ]
    return cls
