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

## 🎯 Prioriterede Features

### UI/UX Forbedringer
- Forbedret error handling og user feedback
- Loading states for alle async operations
- Better responsive design på mobile

### Funktionalitet
- AI-powered keyword suggestions
- Advanced performance predictions
- Batch campaign operations
- Enhanced USP pattern matching

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