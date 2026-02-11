from rest_framework import serializers
from core.models import CustomCategory


class CustomCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomCategory
        fields = ["id", "profile", "data", "manual_classification_data"]
