from celery import shared_task
from django.utils import timezone
from .services import WebsiteCrawler, USPMatcher
from .models import CrawlSession
from campaigns.models import Client


@shared_task
def crawl_client_website(client_id, max_pages=20):
    """
    Celery task to crawl a client's website
    """
    try:
        client = Client.objects.get(id=client_id)
        
        # Update any running sessions to failed if they're too old
        old_running_sessions = CrawlSession.objects.filter(
            client=client,
            status='running',
            started_at__lt=timezone.now() - timezone.timedelta(hours=1)
        )
        old_running_sessions.update(
            status='failed',
            error_message='Session timed out'
        )
        
        # Start new crawl
        crawler = WebsiteCrawler(client, max_pages=max_pages)
        crawl_session = crawler.crawl_website()
        
        # Match extracted USPs with templates
        if crawl_session.status == 'completed':
            matcher = USPMatcher(client)
            matcher.match_extracted_usps()
        
        return {
            'status': 'success',
            'crawl_session_id': crawl_session.id,
            'pages_crawled': crawl_session.pages_crawled,
            'session_status': crawl_session.status
        }
        
    except Client.DoesNotExist:
        return {
            'status': 'error',
            'message': f'Client with id {client_id} not found'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task
def process_extracted_usps(crawl_session_id):
    """
    Process and match extracted USPs with templates
    """
    try:
        crawl_session = CrawlSession.objects.get(id=crawl_session_id)
        client = crawl_session.client
        
        matcher = USPMatcher(client)
        matcher.match_extracted_usps()
        
        return {
            'status': 'success',
            'message': 'USPs processed successfully'
        }
        
    except CrawlSession.DoesNotExist:
        return {
            'status': 'error',
            'message': f'CrawlSession with id {crawl_session_id} not found'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task
def bulk_crawl_clients(client_ids, max_pages=15):
    """
    Crawl multiple clients in batch
    """
    results = []
    
    for client_id in client_ids:
        try:
            result = crawl_client_website.delay(client_id, max_pages)
            results.append({
                'client_id': client_id,
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            results.append({
                'client_id': client_id,
                'status': 'error',
                'message': str(e)
            })
    
    return {
        'status': 'success',
        'total_clients': len(client_ids),
        'results': results
    }