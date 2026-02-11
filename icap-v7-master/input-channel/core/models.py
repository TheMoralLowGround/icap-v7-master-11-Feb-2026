from django.db import models

class ProcessLog(models.Model):
    project = models.CharField(max_length=50, blank=True)
    service = models.CharField(max_length=50, blank=True)
    mailbox = models.EmailField(blank=True, null=True)
    queue_id = models.CharField(max_length=255, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    path = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=50, default="queued")
    batch_id = models.CharField(max_length=50, blank=True, null=True)
    message = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.service}] {self.status} at {self.created_at}"