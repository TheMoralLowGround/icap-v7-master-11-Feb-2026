"""
Organization: AIDocbuilder Inc.
File: access_control/models.py
Version: 6.0

Authors:
    - Nayem - Initial implementation
    - Sunny - Code optimization

Last Updated By: Sunny
Last Updated At: 2024-05-03

Description:
    This file define the database models for the access_control app, structure of 
    the database tables, their fields, and relationships between them.

Dependencies:
    - AbstractUser from django.contrib.auth.models
    - models from django.db
    - Project from dashboard.models
    - Country from core.models

Main Features:
    - Database structure and schema for 'access_control' app.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from dashboard.models import Project
from core.models import Country


class User(AbstractUser):
    class Meta:
        verbose_name_plural = "Users"


class ProjectCountry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    countries = models.ManyToManyField(Country)

    class Meta:
        verbose_name_plural = "Project Countries"

    def __str__(self):
        try:
            return f"Project: {self.project.name}, Selected Countries: ({len([country for country in self.countries.all()])})"
        except:
            return self.project.name
