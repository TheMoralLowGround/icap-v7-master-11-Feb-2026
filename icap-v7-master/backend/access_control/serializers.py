"""
Organization: AIDocbuilder Inc.
File: access_control/serializer.py
Version: 6.0

Authors:
    - Nayem - Initial implementation

Last Updated By: Nayem
Last Updated At: 2024-11-26

Description:
    This file contains serializers for different models such as 
    CountrySerializer, ProjectSerializer, ProjectCountrySerializer and UserSerializer.

Dependencies:
    - from rest_framework import serializers
    - get_user_model from django.contrib.auth
    - Country, Project, ProjectCountry from .models

Main Features:
    - Convert database data into JSON.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Country, Project, ProjectCountry


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["name", "code"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["name"]


class ProjectCountrySerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)
    countries = CountrySerializer(many=True, read_only=True)

    class Meta:
        model = ProjectCountry
        fields = ["project", "countries"]


class UserSerializer(serializers.ModelSerializer):
    project_countries = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ["username", "is_superuser", "project_countries"]

    def get_project_countries(self, obj):
        project_countries = ProjectCountry.objects.filter(user=obj)
        return ProjectCountrySerializer(project_countries, many=True).data


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
