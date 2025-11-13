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

### Farvepalette
- **Primær**: Blue-600 (#2563eb) til hovedelementer
- **Sekundær**: Green-600 (#16a34a) til success states og call-to-action
- **Accenter**: 
  - Orange-600 (#ea580c) til advarsler
  - Purple-600 (#9333ea) til specialfunktioner
  - Yellow-600 (#ca8a04) til notifikationer

### Layout Patterns
- **Card-based design**: Brug hvide cards med `shadow-md` eller `shadow-lg`
- **Responsive**: Mobile-first approach med Tailwind breakpoints
- **Spacing**: Følg 4px interval system (`mb-4`, `mb-6`, `mb-8`)
- **Max width**: Brug `max-w-6xl` for hovedcontainere

### Typography
- **Headers**: Gradient tekst med `bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent`
- **Body**: Standard Tailwind font stack
- **Sizes**: `text-4xl` til h1, `text-2xl` til h2, `text-xl` til h3

### Interactive Elements
- **Buttons**: Følg btn-secondary pattern eller custom Tailwind classes
- **Forms**: Brug input-field class for konsistent styling
- **Icons**: Kun Lucide icons (`data-lucide="icon-name"`)
- **Progress**: Multi-step forms skal have progress indicators

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