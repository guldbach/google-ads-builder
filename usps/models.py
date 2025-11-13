from django.db import models
from campaigns.models import Industry, Client


class USPMainCategory(models.Model):
    """Hovedkategorier for USPs - dynamiske og fleksible"""
    name = models.CharField(max_length=100, help_text="F.eks. 'Hurtigt tilbud/hurtig service'")
    description = models.TextField(help_text="Forklaring af kategoriens formål")
    icon = models.CharField(max_length=10, default="⚡", help_text="Emoji ikon til UI")
    color = models.CharField(max_length=7, default="#8B5CF6", help_text="Hex farve til UI")
    sort_order = models.IntegerField(default=1, help_text="Sorteringsrækkefølge")
    is_recommended_per_campaign = models.BooleanField(
        default=True, 
        help_text="Om kategorien anbefales i hver kampagne"
    )
    max_selections = models.IntegerField(
        default=1, 
        help_text="Maks antal USPs fra denne kategori per kampagne"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.icon} {self.name}"

    class Meta:
        verbose_name_plural = "USP Main Categories"
        ordering = ['sort_order', 'name']


class USPCategoryTemplate(models.Model):
    """Predefinerede kategori-templates for hurtig opsætning"""
    name = models.CharField(max_length=100, help_text="F.eks. 'Håndværker Standard 5-Pack'")
    description = models.TextField(help_text="Beskrivelse af template")
    target_industries = models.ManyToManyField(Industry, blank=True)
    category_data = models.JSONField(help_text="Array af kategori objekter")
    auto_populate_usps = models.BooleanField(
        default=True, 
        help_text="Auto-populer med standard USPs"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "USP Category Templates"


class USPCategory(models.Model):
    """Legacy model - beholdes for migration kompatibilitet"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "USP Categories (Legacy)"


class USPTemplate(models.Model):
    URGENCY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'), 
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    text = models.CharField(max_length=200, help_text="USP teksten")
    main_category = models.ForeignKey(
        USPMainCategory, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Hovedkategori (ny struktur)"
    )
    category = models.ForeignKey(
        USPCategory, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Legacy kategori - brug main_category i stedet"
    )
    priority_rank = models.IntegerField(
        default=1, 
        help_text="1 = højest prioritet (øverste i listen)"
    )
    ideal_for_industries = models.ManyToManyField(
        Industry, 
        blank=True,
        help_text="Industrier denne USP passer bedst til"
    )
    use_cases = models.JSONField(
        default=list, 
        help_text="Array med use cases, f.eks. ['let_at_udregne', 'telefon_vurdering']"
    )
    explanation = models.TextField(
        blank=True,
        help_text="Forklaring af hvornår denne USP skal bruges"
    )
    example_headlines = models.JSONField(
        default=list,
        help_text="Array med eksempel headlines baseret på denne USP"
    )
    placeholders_used = models.JSONField(
        default=list,
        help_text="Array med placeholders brugt, f.eks. ['{SERVICE}', '{BYNAVN}']"
    )
    
    # Legacy felter - beholdes for kompatibilitet
    urgency_level = models.CharField(max_length=10, choices=URGENCY_LEVELS, default='medium')
    keywords = models.TextField(blank=True, help_text="Komma-separerede søgeord")
    effectiveness_score = models.FloatField(
        default=0.5, 
        help_text="Performance score mellem 0 og 1 (opdateres automatisk)"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.priority_rank}] {self.text[:60]}..."

    def get_main_category_display(self):
        """Helper til at vise kategori selv hvis legacy"""
        return self.main_category.name if self.main_category else (self.category.name if self.category else "Ingen kategori")

    class Meta:
        verbose_name_plural = "USP Templates"
        ordering = ['main_category__sort_order', 'priority_rank', 'text']


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


class USPSet(models.Model):
    """Gruppering af valgte USPs til en kampagne"""
    name = models.CharField(max_length=100, help_text="F.eks. 'Murer Kampagne - Frederiksberg'")
    campaign = models.ForeignKey(
        'campaigns.Campaign', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Tilknyttet kampagne (valgfri)"
    )
    selected_usps = models.ManyToManyField(USPTemplate, help_text="Valgte USPs til denne kampagne")
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE, null=True, blank=True)
    service_name = models.CharField(max_length=100, blank=True, help_text="F.eks. 'Murer', 'VVS'")
    target_areas = models.JSONField(default=list, help_text="Array med målrettede områder")
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    is_template = models.BooleanField(
        default=False, 
        help_text="Om dette sæt kan bruges som template for andre"
    )
    effectiveness_score = models.FloatField(
        default=0.0,
        help_text="Samlet effectiveness score for dette USP-sæt"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_category_completion(self):
        """Returnerer hvor mange af de anbefalede kategorier der er dækket"""
        selected_categories = set(usp.main_category for usp in self.selected_usps.all())
        recommended_categories = USPMainCategory.objects.filter(is_recommended_per_campaign=True, is_active=True)
        return len(selected_categories & set(recommended_categories)), len(recommended_categories)

    def is_complete(self):
        """Checker om alle anbefalede kategorier er dækket"""
        completed, total = self.get_category_completion()
        return completed >= total

    class Meta:
        verbose_name_plural = "USP Sets"


class IndustryUSPPattern(models.Model):
    """Legacy model - beholdes for migration kompatibilitet"""
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)
    pattern = models.CharField(max_length=200, help_text="Regex pattern til at finde USPs")
    description = models.TextField()
    weight = models.FloatField(default=1.0)
    examples = models.TextField(help_text="Eksempler på tekst der matcher dette pattern")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.industry.name} - {self.pattern}"

    class Meta:
        verbose_name_plural = "Industry USP Patterns (Legacy)"
