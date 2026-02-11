from django.db import models
import hashlib


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


def get_cache_key(prompt: str, schema_version: str = "1.0") -> str:
    """
    Generate cache key from prompt and schema version.

    Args:
        prompt: Natural language transformation prompt
        schema_version: Version of the JSON schema

    Returns:
        SHA-256 hash (first 16 characters)
    """
    normalized_prompt = prompt.strip().lower()
    content = f"{normalized_prompt}:{schema_version}"
    hash_obj = hashlib.sha256(content.encode("utf-8"))
    return hash_obj.hexdigest()[:16]


class PostProcess(TimeStampedModel):
    code = models.TextField(blank=True, null=True, help_text="Code/text content")
    prompt = models.TextField(
        blank=True, null=True, help_text="Prompt used for processing"
    )
    process = models.TextField(
        blank=True, null=True, help_text="Process definition or name"
    )
    unique_hash = models.CharField(
        max_length=255, blank=True, null=True, help_text="Unique hash of the process"
    )

    def save(self, *args, **kwargs):
        if self.prompt:
            self.unique_hash = get_cache_key(self.prompt)
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"PostProcess {self.id} - {self.process if self.process else 'No Process'}"
        )

    class Meta:
        verbose_name_plural = "Post Processes"
        ordering = ["-created_at"]


class PromptDictionary(TimeStampedModel):
    name = models.CharField(max_length=255, blank=True, null=True)
    prompt = models.TextField(
        blank=True, null=True, help_text="Prompt used for processing"
    )
    unique_hash = models.CharField(
        max_length=255, blank=True, null=True, help_text="Unique hash of the prompt"
    )

    def save(self, *args, **kwargs):
        if self.prompt:
            self.unique_hash = get_cache_key(self.prompt)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"PromptDictionary {self.id} - {self.prompt if self.prompt else 'No Prompt'}"

    class Meta:
        verbose_name_plural = "Prompt Dictionaries"
        ordering = ["-created_at"]
