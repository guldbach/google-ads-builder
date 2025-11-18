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

## 🎨 Modern Design System Guidelines

### 🌈 Color Palette (Moderne Gradient System)
- **Primary Gradient**: `from-purple-600 to-pink-600` - Hovedhandlinger og vigtige elementer
- **Secondary Gradient**: `from-blue-600 to-purple-600` - Sekundære handlinger
- **Category Colors**: Dynamiske farver per kategori (purple-500, blue-500, green-500, etc.)
- **Text Colors**: `text-gray-900` (headings), `text-gray-600` (body), `text-gray-500` (meta)
- **Background Tints**: `bg-{color}-100` til `bg-{color}-50` for category headers

### 🏗️ Layout & Card Patterns
- **Hero Sections**: Gradient background `from-purple-100 via-blue-50 to-pink-100`, centered content
- **Primary Cards**: `bg-white rounded-2xl shadow-lg border border-gray-100`
- **Category Cards**: Color-coded headers med `linear-gradient(135deg, {color}20, {color}10)`
- **Item Cards**: `bg-gray-50 rounded-xl hover:bg-gray-100 transition-all duration-200`
- **Spacing**: Standard Tailwind spacing (space-y-3, space-y-6, space-y-8)
- **Border Radius**: `rounded-lg` (8px), `rounded-2xl` (16px), `rounded-3xl` (24px)

### 📝 Typography System
- **Hero Titles**: `text-5xl font-bold text-gray-900` + 24x24 icon container
- **Page Titles**: `text-2xl font-bold text-gray-900 mb-4`
- **Section Headers**: `text-lg font-medium text-gray-900` (h4)
- **Category Titles**: `text-2xl font-bold text-gray-900` (h3)
- **Body Text**: `text-gray-600` standard line-height
- **Meta Text**: `text-sm text-gray-500`

### 🔘 Button Hierarchy & Interactive Elements
- **Primary Buttons**: `bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-lg hover:shadow-lg transition-all duration-200`
- **Secondary Buttons**: `bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-2 rounded-lg hover:shadow-lg transition-all duration-200`
- **Icon Buttons**: `text-gray-500 hover:text-{color}-600 p-2` (edit, delete, duplicate)
- **Toggle Elements**: Expandable content med smooth animations
- **Hover States**: Consistent `hover:shadow-lg` og color transitions
- **Transition Duration**: Standard 200ms for alle interactions

### 🖼️ Icon Strategy
- **SVG Icons**: Primær icon strategi med 16x16 eller 20x20 sizing
- **Emoji Icons**: Selektiv brug til hurtig genkendelse (➕, ⭐, 🏢)
- **Category Icons**: Bruger-definerede emojis i circular containers
- **Priority Badges**: Circular, color-coded numbers med white text

### 📱 Responsive Design Patterns
- **Container**: `max-w-7xl mx-auto` med responsive padding
- **Grid Systems**: Flex-wrap patterns med gap-3 til gap-8
- **Button Groups**: `flex flex-wrap gap-3` for responsive button layout
- **Mobile**: Single column layout, stacked elements
- **Tablet**: 2-3 column grids, wrapped flex containers

### 📋 Slide-in Panel System
- **Panel Size**: 1000px width, right-side overlay
- **Overlay**: `fixed inset-0 bg-black bg-opacity-50` med backdrop blur
- **Animation**: `translate-x-full` → `translate-x-0` med 300ms timing
- **Content Sections**: Border-separated med `border-t border-gray-200 pt-6`
- **Form Layout**: Consistent input styling med `rounded-lg` borders

### 🏷️ Badge & Status Systems
- **Priority Badges**: `w-8 h-8 text-sm font-bold text-white rounded-full` med kategorifarve
- **Industry Tags**: `px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded`
- **Status Indicators**: Color-coded badges (green for active, gray for inactive)
- **Headlines Preview**: `bg-yellow-100 text-yellow-800` for example content

### ⚡ State Management & Feedback
- **Loading States**: Smooth transitions med opacity changes
- **Success Feedback**: Toast notifications med green accents
- **Error States**: Red color variations med clear messaging
- **Progressive Disclosure**: Hidden details expandable med toggle icons
- **Copy Feedback**: Temporary button text change + color animation

## 🎯 UX Patterns & Interaction Guidelines

### 📋 Quick Actions Pattern
- **Placement**: Prominent bar under hero section
- **Structure**: `flex justify-between items-center` med title + actions
- **Buttons**: Gradient styling med icon + text for clarity
- **Responsive**: Flex-wrap på smaller screens

### 🏷️ Category Management Pattern
- **Header Design**: Color-coded gradient backgrounds matching category theme
- **Icon Strategy**: Circular containers med category-specific emoji
- **Actions**: Edit + Add USP buttons i header for quick access
- **Visual Hierarchy**: Large category name + meta information underneath

### 📝 Item Management Pattern
- **Priority Display**: Circular badge med category color + white text
- **Expandable Details**: Click on title to toggle detailed view
- **Action Buttons**: Minimal icon-only buttons (edit, duplicate, delete)
- **Hover States**: Subtle background color change + smooth transitions

### 📱 Slide-in Panel Workflow
- **Trigger**: Primary buttons open slide-in instead af modal popups
- **Overlay**: Semi-transparent backdrop blocks main content
- **Animation**: Smooth slide-in from right med 300ms timing
- **Sections**: Visually separated content areas med border dividers
- **Form Strategy**: Multi-section forms med clear visual grouping

### 🔄 Interactive Feedback Systems
- **Hover Preview**: Consistent color changes + shadow elevation
- **Click Feedback**: Smooth transitions for all interactive elements
- **Copy to Clipboard**: Visual confirmation med temporary text change
- **Form Submission**: Toast notifications for success/error states
- **Loading Indicators**: Spinner or progress feedback for async operations

### 📐 Information Architecture Principles
- **Progressive Disclosure**: Hide complexity, reveal on demand
- **Categorization**: Group related items under clear category headers
- **Scannable Content**: Use priority numbers, color coding, clear typography
- **Action Hierarchy**: Primary (gradient), Secondary (outlined), Tertiary (icon-only)
- **Context Switching**: Slide-in panels maintain context vs full page navigation

### 💡 Best Practices
- **Consistent Spacing**: Use Tailwind's spacing scale (4, 6, 8, 12px etc.)
- **Color Semantic**: Match colors to meaning (green=success, red=danger, blue=info)
- **Touch Targets**: Minimum 44px for all clickable elements
- **Focus States**: Clear keyboard navigation support
- **Responsive**: Mobile-first design med progressive enhancement

## 📝 Modern Form Design Guidelines

### 🎨 Input Field Styling
- **Standard Inputs**: `w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent`
- **Textarea Fields**: Same styling som inputs med `rows` attribute for height
- **Select Fields**: Consistent styling med input fields for unified appearance
- **Input Groups**: Grid layouts med `grid-cols-2 gap-4` for related fields

### 🏷️ Label & Helper Text
- **Labels**: `block text-sm font-medium text-gray-700 mb-2`
- **Helper Text**: `text-xs text-gray-500 mt-1` underneath inputs
- **Character Counters**: Real-time feedback med color coding (green/yellow/red)
- **Placeholders**: Clear, helpful examples i placeholder attributes

### 📊 Multi-Section Forms
- **Section Headers**: `text-lg font-medium text-gray-900 mb-4` med emoji icons
- **Section Dividers**: `border-t border-gray-200 pt-6` mellem sections
- **Visual Grouping**: Related fields grupperet med consistent spacing
- **Progress Indication**: Clear section progress for long forms

### 🔘 Interactive Form Elements
- **Button Placement**: Primary save button i bottom-right, cancel til venstre
- **Dynamic Content**: Add/remove functionality med smooth animations
- **Copy Features**: Click-to-copy buttons med visual feedback
- **Validation**: Live validation med immediate feedback

### ⚡ Form Behavior Patterns
- **Auto-save**: Background save functionality for long forms
- **Character Limits**: Visual countdown for text constraints
- **Placeholder System**: Standardized placeholder reference (ikke manual input)
- **Industry Selection**: Checkbox grids med search functionality
- **AJAX Submissions**: Form submission uden page refresh

## 💻 Code Patterns & Examples

### 🎨 Essential CSS Classes
```css
/* Primary Card Pattern */
.primary-card { @apply bg-white rounded-2xl shadow-lg border border-gray-100; }

/* Primary Button Pattern */  
.btn-primary { @apply bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-lg hover:shadow-lg transition-all duration-200; }

/* Secondary Button Pattern */
.btn-secondary { @apply bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-2 rounded-lg hover:shadow-lg transition-all duration-200; }

/* Icon Button Pattern */
.btn-icon { @apply text-gray-500 hover:text-blue-600 p-2 transition-colors duration-200; }

/* Form Input Pattern */
.form-input { @apply w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent; }
```

### 🏗️ HTML Structure Patterns
```html
<!-- Hero Section Pattern -->
<div class="text-center mb-12 p-12 bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 rounded-3xl">
    <div class="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl mb-6 shadow-2xl">
        <!-- Icon or Emoji -->
    </div>
    <h1 class="text-5xl font-bold text-gray-900 mb-4">Page Title</h1>
    <p class="text-xl text-gray-600 max-w-2xl mx-auto">Description</p>
</div>

<!-- Quick Actions Pattern -->
<div class="bg-white rounded-2xl shadow-lg p-6 mb-8 border border-gray-100">
    <div class="flex flex-wrap justify-between items-center gap-4">
        <h2 class="text-lg font-semibold text-gray-900">Quick Actions</h2>
        <div class="flex flex-wrap gap-3">
            <button class="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-lg hover:shadow-lg transition-all duration-200">
                Primary Action
            </button>
        </div>
    </div>
</div>

<!-- Category Card Pattern -->
<div class="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
    <div class="p-6" style="background: linear-gradient(135deg, #8B5CF620, #8B5CF610);">
        <div class="flex items-center justify-between">
            <div class="flex items-center space-x-4">
                <div class="w-12 h-12 rounded-xl flex items-center justify-center text-2xl text-white" style="background-color: #8B5CF6;">
                    🎯
                </div>
                <div>
                    <h3 class="text-2xl font-bold text-gray-900">Category Name</h3>
                    <p class="text-gray-600">Category description</p>
                </div>
            </div>
            <div class="flex items-center space-x-2">
                <!-- Action buttons -->
            </div>
        </div>
    </div>
</div>
```

### ⚡ JavaScript Interaction Patterns
```javascript
// Slide-in Panel Pattern
function openSlidePanel(title, subtitle, content, saveCallback) {
    $('#slide-panel-title').text(title);
    $('#slide-panel-subtitle').text(subtitle);
    $('#slide-panel-content').html(content);
    $('#slide-panel-save').off('click').on('click', saveCallback);
    
    $('#slide-panel-overlay').removeClass('hidden');
    setTimeout(() => {
        $('#slide-panel-overlay').removeClass('opacity-0');
        $('#slide-panel').removeClass('translate-x-full');
    }, 10);
}

// Copy to Clipboard Pattern
$(document).on('click', '.copy-placeholder', function() {
    const text = $(this).data('text');
    navigator.clipboard.writeText(text).then(() => {
        const button = $(this);
        const originalText = button.text();
        button.text('Copied!').addClass('bg-green-200 text-green-800');
        setTimeout(() => {
            button.text(originalText).removeClass('bg-green-200 text-green-800');
        }, 1000);
    });
});

// Character Counter Pattern
function updateCharacterCount(inputId, counterId, maxLength) {
    const input = document.getElementById(inputId);
    const counter = document.getElementById(counterId);
    if (input && counter) {
        const length = input.value.length;
        counter.textContent = `${length}/${maxLength}`;
        
        if (length > maxLength) {
            counter.parentElement.classList.add('text-red-500');
        } else if (length > maxLength * 0.8) {
            counter.parentElement.classList.add('text-yellow-500');
        } else {
            counter.parentElement.classList.remove('text-red-500', 'text-yellow-500');
        }
    }
}
```

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