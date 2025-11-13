from django.db import models
from campaigns.models import Client


class CrawlSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    pages_crawled = models.IntegerField(default=0)
    total_pages = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"Crawl {self.client.name} - {self.status}"


class WebPage(models.Model):
    crawl_session = models.ForeignKey(CrawlSession, on_delete=models.CASCADE)
    url = models.URLField()
    title = models.CharField(max_length=500, blank=True)
    content = models.TextField()
    meta_description = models.TextField(blank=True)
    h1_tags = models.TextField(blank=True)
    h2_tags = models.TextField(blank=True)
    word_count = models.IntegerField(default=0)
    is_service_page = models.BooleanField(default=False)
    is_about_page = models.BooleanField(default=False)
    is_contact_page = models.BooleanField(default=False)
    crawled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.url} - {self.title[:50]}"


class ExtractedUSP(models.Model):
    web_page = models.ForeignKey(WebPage, on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    context = models.TextField(help_text="Tekst omkring USP for kontekst")
    confidence_score = models.FloatField()
    extraction_method = models.CharField(max_length=50, help_text="AI, Pattern matching, etc.")
    position_on_page = models.CharField(max_length=50, help_text="Header, Hero, Footer, etc.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.web_page.url} - {self.text[:50]}"

    class Meta:
        verbose_name_plural = "Extracted USPs"


class ServiceArea(models.Model):
    web_page = models.ForeignKey(WebPage, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=200)
    service_description = models.TextField(blank=True)
    keywords_found = models.TextField()
    priority_score = models.FloatField(default=0.5)
    
    def __str__(self):
        return f"{self.web_page.url} - {self.service_name}"
