"""
Organization: AIDocbuilder Inc.
File: access_control/admin.py
Version: 6.0

Authors:
    - Nayem - Initial implementation

Last Updated By: Nayem
Last Updated At: 2024-12-04

Description:
    This file handles the updating of User permission control form and manages the inline functionality.

Dependencies:
    - admin from django.contrib
    - UserAdmin from django.contrib.auth.admin
    - Group from django.contrib.auth.models
    - User, Country, ProjectCountry from .models
    - BaseInlineFormSet from django.forms.models 

Main Features:
    - Customized admin user dashboard interface and features.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import User, Country, ProjectCountry
from django.forms.models import BaseInlineFormSet


class ProjectCountryInlineFormSet(BaseInlineFormSet):
    def __init_gettext_lazy(self, *args, **kwargs):
        super(ProjectCountryInlineFormSet, self).__init_gettext_lazy(*args, **kwargs)
        self.form.base_fields["countries"].queryset = Country.objects.order_by("name")


class ProjectCountryInline(admin.TabularInline):
    model = ProjectCountry
    formset = ProjectCountryInlineFormSet
    extra = 1
    filter_horizontal = ("countries",)


class CustomUserAdmin(UserAdmin):
    model = User
    change_form_template = "access_control/change_form.html"
    add_form_template = "access_control/change_form.html"
    inlines = (ProjectCountryInline,)
    fieldsets = [
        (None, {"fields": ("username", "password")}),
        # (("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            ("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser")},
        ),
        # (("Important dates"), {"fields": ("last_login", "date_joined")}),
    ]

    list_display = ("username", "is_staff", "last_login")

    def get_form(self, request, obj=None, **kwargs):
        
        # Updates the form label and help text for User permission control

        form = super().get_form(request, obj, **kwargs)
        if form.base_fields.get("username"):
            form.base_fields["username"].label = "User ID (LDAP)"

        if 'is_active' in form.base_fields:
            form.base_fields['is_active'].label = "Active (For Agent access)"

        if 'is_staff' in form.base_fields:
            form.base_fields['is_staff'].label = "Staff status (For SuperUser access)"
            form.base_fields["is_staff"].help_text = (
                "Check only if the user is approved as a staff (Sandeep Biradar)"
            )
            
        if 'is_superuser' in form.base_fields:
            form.base_fields['is_superuser'].label = "Superuser status (For admin support access)"

        return form


admin.site.unregister(Group)
admin.site.register(User, CustomUserAdmin)
