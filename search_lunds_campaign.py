#!/usr/bin/env python
"""
Søg efter Lunds campaign
"""
import os
import sys
import django

# Setup Django
sys.path.append('/Users/guldbach/google-ads-builder')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ads_builder.settings')
django.setup()

from campaigns.models import Campaign, Client

def search_lunds_campaign():
    """Søg efter Lunds kampagne"""
    
    print("🔍 Searching for Lunds Fugeservice Campaign...")
    print("=" * 60)
    
    # Search campaigns
    lunds_campaigns = Campaign.objects.filter(name__icontains='Lunds')
    fugeservice_campaigns = Campaign.objects.filter(name__icontains='Fugeservice')
    
    print(f"📋 Campaigns with 'Lunds': {lunds_campaigns.count()}")
    for camp in lunds_campaigns:
        print(f"   ID {camp.id}: {camp.name}")
    
    print(f"📋 Campaigns with 'Fugeservice': {fugeservice_campaigns.count()}")
    for camp in fugeservice_campaigns:
        print(f"   ID {camp.id}: {camp.name}")
    
    # Search clients
    lunds_clients = Client.objects.filter(name__icontains='Lunds')
    fugeservice_clients = Client.objects.filter(name__icontains='Fugeservice')
    
    print(f"🏢 Clients with 'Lunds': {lunds_clients.count()}")
    for client in lunds_clients:
        print(f"   ID {client.id}: {client.name}")
        # Find campaigns for this client
        client_campaigns = Campaign.objects.filter(client=client)
        for camp in client_campaigns:
            print(f"     Campaign ID {camp.id}: {camp.name}")
    
    print(f"🏢 Clients with 'Fugeservice': {fugeservice_clients.count()}")
    for client in fugeservice_clients:
        print(f"   ID {client.id}: {client.name}")
        # Find campaigns for this client
        client_campaigns = Campaign.objects.filter(client=client)
        for camp in client_campaigns:
            print(f"     Campaign ID {camp.id}: {camp.name}")
    
    # Search by date (2025-11-12)
    print(f"\n📅 Campaigns from today (2025-11-12):")
    from datetime import datetime, date
    today = date(2025, 11, 12)
    
    # Try to filter by created date if field exists
    all_campaigns = Campaign.objects.all().order_by('-id')[:20]
    for camp in all_campaigns:
        if hasattr(camp, 'created_at') and camp.created_at:
            if camp.created_at.date() == today:
                print(f"   ID {camp.id}: {camp.name} (created: {camp.created_at})")
        else:
            # If no created_at, show all recent
            print(f"   ID {camp.id}: {camp.name}")
    
    # Search for AWM pattern
    print(f"\n🔍 Campaigns with 'AWM':")
    awm_campaigns = Campaign.objects.filter(name__icontains='AWM')
    for camp in awm_campaigns:
        print(f"   ID {camp.id}: {camp.name}")
    
    # Search for patterns like "4_Annoncegrupper"
    print(f"\n🔍 Campaigns with 'Annoncegrupper':")
    annoncegrupper_campaigns = Campaign.objects.filter(name__icontains='Annoncegrupper')
    for camp in annoncegrupper_campaigns:
        print(f"   ID {camp.id}: {camp.name}")

if __name__ == '__main__':
    search_lunds_campaign()