# Claude Development Instructions - Google Ads Builder

Dette dokument indeholder guidelines og instruktioner til Claude når der bygges nye funktioner eller modificeres eksisterende kode i Google Ads Builder projektet.

## 🎯 Projekt Oversigt

Google Ads Builder er et intelligent Django-baseret værktøj til at bygge Google Ads kampagner baseret på website crawling, AI-analyse og prædefinerede USP'er.

## 📋 Generelle Development Guidelines

### Code Conventions
- **Sprog**: Brug dansk i UI tekster, brugerrettede beskeder og form labels
- **Kommentarer**: Hold kommentarer og variabelnavne på engelsk for kode-dokumentation
- **Django Patterns**: Følg Django best practices og eksisterende struktur
- **Docstrings**: Alle Django views skal have beskrivende docstrings
- **Model Methods**: Alle Django modeller skal have `__str__` methods
- **Error Handling**: Implementer proper exception handling og brugervenlige fejlbeskeder

### Testing
- Test alle nye features med eksisterende Playwright test suite
- Skriv unit tests for nye models og views
- Verificér at eksisterende funktionalitet ikke brydes

## 🎨 Design System Guidelines

### Farvepalette (Asana-inspireret)
- **Blue Palette**: Fra blue-0 (#cbefff) til blue-1000 (#222875) - Primary brand colors
- **Coral Palette**: Fra coral-0 (#ffeaec) til coral-1000 (#690031) - Alerts og warnings
- **Green Palette**: Fra green-0 (#c9fcdb) til green-1000 (#004232) - Success states
- **Purple Palette**: Fra purple-0 (#ffdcff) til purple-1000 (#6a0085) - Special features
- **Grayscale**: Fra gray-20 (#fafafa) til gray-1000 (#0d0d0d) - Text og backgrounds

### Layout Patterns (Asana System)
- **Card-based design**: Brug hvide cards med `shadow-asana` eller `shadow-asana-lg`
- **Responsive**: Custom breakpoints (xs:480px, sm:768px, md:960px, lg:1120px)
- **Spacing**: Asana spacing system (1-40 med 4px incrementer)
- **Border Radius**: Konsistent 3px (`rounded-asana`)

### Typography (Exact Asana System - Via Playwright Analysis)
- **Font Stack**: "TWK Lausanne", "Helvetica Neue", Helvetica, sans-serif
- **Heading Font**: Ghost, "Helvetica Neue", Helvetica, sans-serif  
- **Body Text**: 16px, line-height: 28px, color: rgb(100, 111, 121)
- **H1 Specifications**: 72px, line-height: 72px, letter-spacing: -0.5px, font-weight: 500, color: rgb(105, 0, 49)
- **Button Text**: 14px, font-weight: 500, "TWK Lausanne" font family

### Interactive Elements (Exact Asana System)
- **Buttons**: Font: "TWK Lausanne", 14px, font-weight: 500, padding: 0px 12px, border-radius: 3px
- **Input Fields**: Font: "TWK Lausanne", 12.8px, padding: 6px 35px 6px 15px, border-radius: 50px
- **Navigation**: Height: 56px, transparent background
- **Sections**: Transparent backgrounds, padding patterns: 120px 0px 80px (normal), 0px 0px 40px (small), 160px 0px 0px (large)
- **Icons**: Kun Lucide icons med Asana-sizing
- **Progress**: `.progress-bar` med `.step-indicator` (states: .step-active, .step-complete, .step-inactive)
- **Cards**: `.card`, `.card-elevated`, `.card-interactive` med hover effects
- **Alerts**: `.alert-info`, `.alert-success`, `.alert-warning`, `.alert-error`
- **Badges**: `.badge-blue`, `.badge-green`, `.badge-coral`, `.badge-gray`

### Form Design
- **Multi-step**: Brug progress bar med step indicators
- **Validation**: Live validation med tydelige fejlbeskeder
- **Loading states**: Implementer loading spinners for async operations

## 🏗️ Current System Architecture & Workflow

### 🎯 USP Manager (`/usps/manager/`)
- **Formål**: Centralt administrationspanel til alle USP kategorier og templates
- **Kernefunktioner**: 
  - Opret/redigér USP kategorier med ikoner og farver
  - Administrér USP templates med headline variations og use cases
  - Dublicér eksisterende USPs for hurtig opsætning
  - AJAX-baseret interface uden page refresh
- **Modeller**: `USPMainCategory`, `USPTemplate`, `ClientUSP`, `USPSet`
- **Key Views**: `usp_manager`, `create_usp_ajax`, `edit_usp_ajax`

### 🌍 Geo-Marketing System
- **GeoTemplate**: Templates til automatisk generering af geo-specifikt content
- **Placeholder system**: `{SERVICE}`, `{BYNAVN}`, `{URL_SLUG}` til dynamisk content
- **Auto-validation**: Tjek at templates overholder Google Ads limits (30 chars headlines, 90 chars descriptions)
- **Export formater**: Google Ads Editor CSV + WordPress WP All Import CSV
- **Models**: `GeoTemplate`, `GeoKeyword`, `GeoExport`

### 📊 Current Database Models
**Core Campaign Structure:**
- `Industry` → `Client` → `Campaign` → `AdGroup` → `Keyword`/`Ad`
- `USPMainCategory` → `USPTemplate` → `ClientUSP`
- `GeoTemplate` → `GeoKeyword` → `GeoExport`

**Performance Tracking:**
- `PerformanceDataImport` → `HistoricalCampaignPerformance`
- `IndustryPerformancePattern` → `CampaignArchitecturePattern`

**Negative Keywords (Existing):**
- `NegativeKeywordList` → `NegativeKeyword`
- `CampaignNegativeKeywordList` (Many-to-Many)

### 🔗 Current URL Structure
- `/` - Home/dashboard
- `/campaigns/builder/` - Campaign builder
- `/campaigns/geo/` - Geo campaign builder  
- `/campaigns/quick/` - Quick builder
- `/usps/manager/` - USP administration panel
- `/admin/` - Django admin interface

### 🔧 Development Commands
```bash
# Start development
cd /Users/guldbach/google-ads-builder
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# CSS compilation
npm run build-css        # Development
npm run build-css-prod   # Production

# Database management
python manage.py makemigrations
python manage.py migrate

# USP data seeding
python manage.py seed_usps
python manage.py load_sample_usps
```

## 🏗️ Arkitektur Guidelines

### File Organization
```
google-ads-builder/
├── campaigns/          # Hovedfunktionalitet
│   ├── templates/campaigns/  # HTML templates
│   ├── models.py      # Database modeller
│   ├── views.py       # Django views
│   ├── urls.py        # URL routing
│   └── geo_export.py  # Export funktionalitet
├── static/
│   ├── css/style.css  # Kompileret Tailwind
│   └── src/input.css  # Tailwind source
└── templates/base.html # Base template
```

### Django Apps
- **campaigns**: Hovedfunktionalitet for kampagne management
- **crawler**: Website crawling og USP extraction
- **usps**: USP database og matching
- **ai_integration**: AI/ChatGPT integration

### Database Design
- Følg existing model patterns med proper relationships
- Brug `created_at` og `updated_at` timestamps
- Implementer `__str__` methods for admin interface

## 🚀 Funktionalitet Guidelines

### Geo-Kampagner
- Skal understøtte danske byer og regioner
- Brug `DanishSlugGenerator` til URL-venlige navne
- Implementer GeoKeywordGenerator til lokale keywords

### Export Funktionalitet
- Primært focus på Google Ads Editor format
- Understøt CSV og Excel exports
- Følg existing pattern i `geo_export.py`

### Background Tasks
- Brug Celery til tunge processer (web crawling, AI requests)
- Implementer proper task status tracking
- Giv brugeren feedback om task progress

### USP Extraction
- Website crawling med BeautifulSoup
- Pattern matching til USP identifikation
- AI-assisteret analyse for forbedrede resultater

### API Integration
- Google Ads API til kampagne creation
- OpenAI API til content generation
- Proper rate limiting og error handling

## 🔧 Development Workflow

### Starting Development
```bash
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
npm run build-css  # For CSS changes
```

### Before Committing
- Test funktionalitet i browser
- Kør existing tests: `python manage.py test`
- Verificér CSS compilation: `npm run build-css-prod`

### CSS Development
- Redigér kun `static/src/input.css`
- Kompilér med `npm run build-css` under development
- Brug `npm run build-css-prod` til production

## 🎯 Prioriterede Features & Roadmap

### 🔥 Næste Development Fase

#### 1. **Standard Negative Søgeordslister System**
- **Formål**: Centraliseret negative keyword management koblet til brancher og kampagnetyper
- **Struktur**: 
  - Branche-specifikke lister (Håndværk, Service, Skønhed & Beauty)
  - Kampagnetype-specifikke lister (Search, Display, Shopping)
  - Segment-specifikke lister (generelle ausschlüsse)
- **Auto-kobling**: Automatisk tildeling baseret på industry/campaign type selection
- **Database**: Udbyg eksisterende `NegativeKeywordList` model med industry/segment kobling

#### 2. **Geografisk Segmentering & Automation**
- **Geo-segmenter**: Nordsjælland, Storkøbenhavn, Vestsjælland, etc.
- **Funktionalitet**:
  - Excel/CSV generering med geo-undersider til WordPress
  - Automatisk geo-targeting i Google Ads kampagner ved upload
  - Template system til geo-specifikke landing pages
- **Integration**: Kobl sammen med eksisterende `GeoTemplate` system

#### 3. **Branche-Specifikke Standard Kampagnestrukturer**
- **Template System**: Færdige campaign + ad group strukturer per branche
- **Konfigurerbar Workflow**:
  - Vælg branche → Auto-load standard struktur
  - Tilpas USPs via checkbox interface  
  - Set budget og målområde
  - Vælg ønskede kampagner/annoncegrupper (checkbox)
- **Database Models**: `IndustryTemplate`, `StandardCampaignStructure`, `StandardAdGroupTemplate`

#### 4. **Google Ads Extensions System**
- **Extension Typer**:
  - Sitelink Extensions (underside udvidelser)
  - Call Extensions (opkald udvidelser) 
  - Location Extensions (adresse udvidelser)
  - Callout Extensions (info udvidelser)
- **Management**: Admin interface til at definere standard extensions per branche/kampagne
- **Auto-Application**: Automatisk tildeling baseret på campaign/industry type

### 🏗️ Arkitektur Tilføjelser

#### Database Models (Nye)
```python
# Geo Segmentering
class GeoSegment(models.Model):
    name = models.CharField(max_length=100)  # "Nordsjælland", "Storkøbenhavn"
    description = models.TextField()
    included_cities = models.JSONField()  # Array af byer i segmentet
    google_ads_location_criteria = models.JSONField()  # Location targeting criteria

# Standard Kampagne Strukturer
class IndustryTemplate(models.Model):
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # "VVS Standard Setup"
    default_budget = models.DecimalField(max_digits=10, decimal_places=2)
    default_geo_segments = models.ManyToManyField(GeoSegment)
    
class StandardCampaignStructure(models.Model):
    industry_template = models.ForeignKey(IndustryTemplate, on_delete=models.CASCADE)
    campaign_name_template = models.CharField(max_length=200)
    campaign_type = models.CharField(max_length=20)
    is_enabled_by_default = models.BooleanField(default=True)
    
class StandardAdGroupTemplate(models.Model):
    campaign_structure = models.ForeignKey(StandardCampaignStructure, on_delete=models.CASCADE)
    ad_group_name_template = models.CharField(max_length=200)
    default_keywords = models.JSONField()  # Array af standard søgetermer
    default_cpc = models.DecimalField(max_digits=8, decimal_places=2)

# Extensions System
class AdExtensionTemplate(models.Model):
    EXTENSION_TYPES = [
        ('sitelink', 'Sitelink Extension'),
        ('call', 'Call Extension'),
        ('location', 'Location Extension'),
        ('callout', 'Callout Extension'),
    ]
    
    extension_type = models.CharField(max_length=20, choices=EXTENSION_TYPES)
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE, null=True, blank=True)
    template_data = models.JSONField()  # Extension-specific data
    is_active = models.BooleanField(default=True)
```

### 🎨 UI/UX Forbedringer
- Forbedret error handling og user feedback
- Loading states for alle async operations
- Better responsive design på mobile
- **Wizard-based setup** til branche-specifikke templates

### 🔧 Teknisk Funktionalitet
- AI-powered keyword suggestions
- Advanced performance predictions baseret på historical data
- **Bulk operations** til kampagne management
- Enhanced USP pattern matching
- **Checkbox-baseret campaign/ad group selection interface**

## 🚨 Vigtige Begrænsninger

### Sikkerhed
- Aldrig commit API keys eller secrets
- Validér all bruger input
- Implementer proper authentication hvor nødvendigt

### Performance
- Optimér database queries med select_related/prefetch_related
- Implementér caching for tunge operationer
- Brug background tasks til lang-kørende processer

### Kompatibilitet
- Understøt de seneste 2 major browser versioner
- Test på både desktop og mobile devices
- Følg WCAG guidelines for accessibility

## 📚 Ressourcer

- **Django Docs**: https://docs.djangoproject.com/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Lucide Icons**: https://lucide.dev/
- **Google Ads API**: https://developers.google.com/google-ads/api/

---

**Husk**: Dette dokument skal opdateres når nye patterns eller guidelines introduceres i projektet.