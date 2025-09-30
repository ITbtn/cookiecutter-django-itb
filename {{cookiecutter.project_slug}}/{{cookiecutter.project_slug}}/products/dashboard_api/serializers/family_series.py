from rest_framework import serializers

from {{cookiecutter.project_slug}}.products.models import Family, Series


class DashboardFamilyLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = [
            "code",
            "name",
        ]


class DashboardSeriesLiteSerializer(serializers.ModelSerializer):
    family = DashboardFamilyLiteSerializer()

    class Meta:
        model = Series
        fields = ["code", "name", "family"]


class DashboardFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ["code", "name", "description", "is_available"]


class FamilyCreateSerializer(serializers.ModelSerializer):
    # auto generate if not provided
    code = serializers.CharField(required=False, allow_null=False, allow_blank=False)

    class Meta:
        model = Family
        fields = ["code", "name", "description", "is_available"]


class FamilyUpdateSerializer(serializers.ModelSerializer):
    class Meta(FamilyCreateSerializer.Meta):
        model = Family
        fields = ["code", "name", "description", "is_available"]
        read_only_fields = ["code"]


class DashboardSeriesSerializer(serializers.ModelSerializer):
    family = DashboardFamilySerializer()

    class Meta:
        model = Series
        fields = ["code", "name", "description", "is_available", "family"]


class SeriesInputSerializer(serializers.ModelSerializer):
    # auto generate if not provided
    code = serializers.CharField(required=False, allow_null=False, allow_blank=False)
    family_code = serializers.CharField(
        required=False, allow_null=True, allow_blank=False
    )

    class Meta:
        model = Series
        fields = ["code", "name", "description", "is_available", "family_code"]
