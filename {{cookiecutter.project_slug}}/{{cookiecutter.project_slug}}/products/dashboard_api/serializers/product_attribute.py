from rest_framework import serializers

from {{cookiecutter.project_slug}}.attributes.dashboard_api.serializers.attribute import (
    AttributeOutputSerializer,
)
from {{cookiecutter.project_slug}}.attributes.dashboard_api.serializers.options import (
    OptionsOutputSerializer,
)
from {{cookiecutter.project_slug}}.attributes.services.attribute import AttributeService
from {{cookiecutter.project_slug}}.attributes.services.options import OptionService
from {{cookiecutter.project_slug}}.common.validators import validate_char_field
from {{cookiecutter.project_slug}}.products.models import ProductAttribute


class DashboardProductAttributeInputSerializer(serializers.ModelSerializer):
    attribute = serializers.CharField(max_length=128, validators=[validate_char_field])
    option = serializers.CharField(
        max_length=128,
        validators=[validate_char_field],
        allow_null=True,
        allow_blank=True,
        required=False,
    )
    available_options = serializers.ListField(
        required=False, allow_empty=True, allow_null=True
    )
    code = serializers.CharField(required=False)

    class Meta:
        model = ProductAttribute
        exclude = ["id"]

    def validate_option(self, value):
        # If submitted data is form data we validate here.
        if value:
            if value[0]:
                return value
            else:
                return None
        else:
            return None

    def validate_available_options(self, value):
        # If submitted data is form data we validate here.
        if value:
            if value[0]:
                return value
            else:
                return []
        else:
            return []


class DashboardProductAttributeOutputSerializer(serializers.ModelSerializer):
    attribute = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    option = serializers.SerializerMethodField()
    available_options = serializers.SerializerMethodField()

    class Meta:
        model = ProductAttribute
        exclude = ["id", "product"]

    def get_attribute(self, obj):
        request = self.context.get("request")
        if obj.attribute:
            attribute_name = AttributeService(
                tenant_code=request.tenant_code, site_profile=request.site_profile
            ).read_by_pk(pk_value=obj.attribute.pk)
            serializer = AttributeOutputSerializer(instance=attribute_name)
            return serializer.data

    @staticmethod
    def get_option(obj):
        if obj.option:
            serializer = OptionsOutputSerializer(instance=obj.option)
            return serializer.data

    @staticmethod
    def get_available_options(obj):
        if obj.available_options:
            serializer = OptionsOutputSerializer(
                instance=obj.available_options, many=True
            )
            if serializer.data:
                return serializer.data
            else:
                return None

    @staticmethod
    def get_created_by(obj):
        if obj.created_by:
            return obj.created_by.username
        return ""

    @staticmethod
    def get_updated_by(obj):
        if obj.updated_by:
            return obj.updated_by.username
        return ""


class DashboardProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        read_only_fields = ("id", "code", "product")
        extra_kwargs = {"available_options": {"allow_empty": True}}
        exclude = ["id", "product"]

    def to_internal_value(self, data):
        request = self.context.get("request")
        data["updated_by"] = request.user.id
        if data.get("attribute"):
            data["attribute"] = (
                AttributeService(
                    tenant_code=request.tenant_code, site_profile=request.site_profile
                )
                .get_attribute_by_code(attribute_code=data.get("attribute"))
                .pk
            )
        if data.get("option"):
            data["option"] = (
                OptionService(
                    tenant_code=request.tenant_code, site_profile=request.site_profile
                )
                .get_option_by_code(option_code=data.get("option"))
                .pk
            )

        available_options = []
        if data.get("available_options"):
            if isinstance(data.get("available_options"), str):
                data["available_options"] = data.getlist("available_options")
                data = data.dict()
            for option in data.get("available_options"):
                available_options.append(
                    OptionService(
                        tenant_code=request.tenant_code,
                        site_profile=request.site_profile,
                    )
                    .get_option_by_code(option_code=option)
                    .pk
                )
            data["available_options"] = available_options

        if "available_options" in data and not isinstance(
            data["available_options"], list
        ):
            data["available_options"] = available_options
            data = data.dict()
        return super().to_internal_value(data)
