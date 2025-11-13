# Google Ads Campaign Builder

Et intelligent værktøj til at bygge Google Ads kampagner baseret på website crawling, AI-analyse og prædefinerede USP'er.

## Features

- **Website Crawling**: Automatisk analyse af kunde websites for at identificere services og USP'er
- **AI Integration**: ChatGPT integration til tekstgenerering og kampagne optimering
- **USP Management**: Database med branche-specifikke USP'er og automatisk matching
- **Campaign Builder**: Intelligente forslag til kampagne struktur og budget allokering
- **Google Ads Export**: Direkte eksport til Google Ads format

## Tech Stack

- **Backend**: Django 5.2 + Django REST Framework
- **Database**: PostgreSQL
- **Frontend**: Tailwind CSS
- **AI**: OpenAI GPT integration
- **Background Tasks**: Celery + Redis
- **Web Crawling**: BeautifulSoup + Requests
- **Export**: Google Ads API + pandas

## Installation

1. Klon projektet og naviger til mappen:
```bash
cd google-ads-builder
```

2. Opret virtual environment og installer dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Installer frontend dependencies:
```bash
npm install
```

4. Konfigurer environment variabler i `.env` filen:
```bash
# Database
DB_NAME=ads_builder
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN=your_token
GOOGLE_ADS_CLIENT_ID=your_client_id
GOOGLE_ADS_CLIENT_SECRET=your_client_secret
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
```

5. Kør migrations:
```bash
python manage.py migrate
```

6. Opret superuser:
```bash
python manage.py createsuperuser
```

7. Build CSS:
```bash
npm run build-css-prod
```

8. Start development server:
```bash
python manage.py runserver
```

## Projekt Struktur

```
google-ads-builder/
├── campaigns/          # Kampagne management og modeller
├── crawler/            # Website crawling funktionalitet
├── usps/              # USP database og matching
├── ai_integration/    # AI/ChatGPT integration
├── static/            # CSS og frontend assets
├── templates/         # HTML templates
└── ads_builder/       # Django settings og konfiguration
```

## Database Modeller

### Campaigns App
- **Industry**: Brancher og kategorier
- **Client**: Kunde information
- **Campaign**: Google Ads kampagner
- **AdGroup**: Annoncegrupper
- **Keyword**: Keywords og bidding
- **Ad**: Annoncer og tekster
- **CampaignPerformancePrediction**: Performance forudsigelser

### USPs App
- **USPCategory**: USP kategorier
- **USPTemplate**: Prædefinerede USP templates
- **ClientUSP**: Kunde-specifikke USP'er
- **IndustryUSPPattern**: Branchemønstre til USP identifikation

### Crawler App
- **CrawlSession**: Crawling sessioner
- **WebPage**: Crawlede sider
- **ExtractedUSP**: Automatisk fundne USP'er
- **ServiceArea**: Identificerede service områder

### AI Integration App
- **AIPromptTemplate**: AI prompt templates
- **AIAnalysisSession**: AI analyse sessioner
- **GeneratedAdCopy**: AI-genererede annoncer
- **KeywordSuggestion**: AI keyword forslag
- **CampaignOptimizationSuggestion**: Optimeringsforslag

## Development

### Start Celery worker:
```bash
celery -A ads_builder worker -l info
```

### Watch CSS changes:
```bash
npm run build-css
```

### Admin Interface
Tilgå Django admin på: `http://localhost:8000/admin/`

## Web Crawling

Web crawling funktionaliteten er nu implementeret og kan:
- Crawle kunde websites automatisk
- Udtrække USP'er ved hjælp af pattern matching
- Identificere service sider og områder
- Matche fundne USP'er med prædefinerede templates
- Køre som background tasks via Celery

### Test web crawling

1. Load sample USP data:
```bash
python manage.py load_sample_usps
```

2. Create test client:
```bash
python manage.py crawl_website --create-test-client
```

3. Test crawling (eksempel med en rigtig website):
```bash
python manage.py crawl_website --url https://example.com --max-pages 5
```

4. Test med Celery task:
```bash
# Start Celery worker (i en separat terminal)
celery -A ads_builder worker -l info

# Queue crawl task
python -c "
from crawler.tasks import crawl_client_website
from campaigns.models import Client
client = Client.objects.first()
result = crawl_client_website.delay(client.id, 5)
print(f'Task queued: {result.id}')
"
```

### Run tests
```bash
python manage.py test crawler
```

## Next Steps

1. ✅ Web crawling funktionalitet
2. Integrer OpenAI API til AI-drevet analyse
3. Byg frontend interface
4. Implementer Google Ads eksport
5. Tilføj avancerede optimeringsalgoritmer