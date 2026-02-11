from django.db import models


class CustomCategory(models.Model):
    profile = models.CharField(max_length=255, blank=True, null=True)
    data = models.JSONField(default=dict, blank=True, null=True)
    manual_classification_data = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Custom Categories"
