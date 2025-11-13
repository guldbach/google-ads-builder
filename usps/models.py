from django.db import models
from campaigns.models import Industry, Client


class USPCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "USP Categories"


class USPTemplate(models.Model):
    URGENCY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    text = models.CharField(max_length=200)
    category = models.ForeignKey(USPCategory, on_delete=models.CASCADE)
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE, null=True, blank=True)
    urgency_level = models.CharField(max_length=10, choices=URGENCY_LEVELS, default='medium')
    keywords = models.TextField(help_text="Komma-separerede søgeord der trigger denne USP")
    effectiveness_score = models.FloatField(default=0.5, help_text="Score mellem 0 og 1")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name_plural = "USP Templates"


class ClientUSP(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    usp_template = models.ForeignKey(USPTemplate, on_delete=models.CASCADE, null=True, blank=True)
    custom_text = models.CharField(max_length=200)
    is_discovered = models.BooleanField(default=False, help_text="Fundet via website crawling")
    is_selected = models.BooleanField(default=True)
    source_url = models.URLField(blank=True, help_text="URL hvor USP blev fundet")
    confidence_score = models.FloatField(default=0.5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.name} - {self.custom_text[:50]}"

    class Meta:
        verbose_name_plural = "Client USPs"


class IndustryUSPPattern(models.Model):
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)
    pattern = models.CharField(max_length=200, help_text="Regex pattern til at finde USPs")
    description = models.TextField()
    weight = models.FloatField(default=1.0)
    examples = models.TextField(help_text="Eksempler på tekst der matcher dette pattern")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.industry.name} - {self.pattern}"

    class Meta:
        verbose_name_plural = "Industry USP Patterns"
