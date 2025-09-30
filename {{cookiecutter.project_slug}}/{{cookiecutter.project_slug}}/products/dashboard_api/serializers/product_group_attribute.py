from rest_framework import serializers

from {{cookiecutter.project_slug}}.attributes.constants import AttributeType
from {{cookiecutter.project_slug}}.attributes.dashboard_api.serializers.attribute import (
    AttributeGroupOutputSerializer,
)
from {{cookiecutter.project_slug}}.attributes.models.attribute import Attribute


class DashboardProductGroupAttributeInputSerializer(serializers.Serializer):
    attribute_code = serializers.CharField()


class DashboardProductGroupAttributeOutputSerializer(serializers.ModelSerializer):
    attribute_group = AttributeGroupOutputSerializer()
    attribute_type = serializers.SerializerMethodField()
    is_selected = serializers.SerializerMethodField()

    class Meta:
        model = Attribute
        fields = ["code", "attribute_group", "name", "attribute_type", "is_selected"]

    def get_attribute_type(self, obj):
        attribute_types = AttributeType()
        return attribute_types.get_attribute_type_name_by_value(
            value=obj.attribute_type
        )

    def get_is_selected(self, obj):
        if obj.code in self.context.get("regular_attribute_codes_list", []):
            return True
        return False
