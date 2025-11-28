from django.core.management.base import BaseCommand
from campaigns.models import BudgetStrategy, AdTemplate, Industry
from usps.models import USPTemplate
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Seed campaign builder data - budget strategies, ad templates, and CTA flags'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting Campaign Builder Data Seeding...")
        self.stdout.write("=" * 60)
        
        self.create_budget_strategies()
        self.stdout.write("")
        self.create_ad_templates() 
        self.stdout.write("")
        self.update_usp_cta_flags()
        
        self.stdout.write("")
        self.stdout.write("🎉 Campaign Builder data seeding completed!")
        self.stdout.write("=" * 60)
        self.stdout.write("📋 Summary:")
        self.stdout.write(f"  Budget Strategies: {BudgetStrategy.objects.count()}")
        self.stdout.write(f"  Ad Templates: {AdTemplate.objects.count()}")
        self.stdout.write(f"  CTA USPs: {USPTemplate.objects.filter(is_cta=True).count()}")

    def create_budget_strategies(self):
        """Create standard budget strategies"""
        self.stdout.write("🔧 Creating Budget Strategies...")
        
        # Get or create demo user
        user, created = User.objects.get_or_create(
            username='demo',
            defaults={'email': 'demo@example.com'}
        )
        
        # Get industries
        vvs_industry = Industry.objects.filter(name__icontains='VVS').first()
        handvaerker_industry = Industry.objects.filter(name__icontains='Håndværker').first()
        
        strategies = [
            {
                'name': 'Standard Håndværker',
                'description': 'Standard budget strategi for håndværker brancher med moderate budgetter',
                'bidding_strategy': 'enhanced_cpc',
                'default_daily_budget': 500.00,
                'default_cpc': 15.00,
                'industries': [vvs_industry, handvaerker_industry] if vvs_industry and handvaerker_industry else [],
                'is_default': True,
            },
            {
                'name': 'Akut Service - Høj Prioritet',
                'description': 'Aggressiv strategi for akutte services med højere budgetter',
                'bidding_strategy': 'target_cpa',
                'default_daily_budget': 1000.00,
                'target_cpa': 250.00,
                'industries': [vvs_industry] if vvs_industry else [],
                'is_default': False,
            },
            {
                'name': 'Konkurrencedygtig CPC',
                'description': 'Manuel CPC strategi for konkurrencedygtige markeder',
                'bidding_strategy': 'manual_cpc',
                'default_daily_budget': 750.00,
                'default_cpc': 12.00,
                'industries': [],
                'is_default': False,
            },
            {
                'name': 'Maximize Clicks - Lav Budget',
                'description': 'Maksimer clicks ved lavere budgetter',
                'bidding_strategy': 'maximize_clicks',
                'default_daily_budget': 300.00,
                'industries': [],
                'is_default': False,
            }
        ]
        
        for strategy_data in strategies:
            industries_list = strategy_data.pop('industries')
            
            strategy, created = BudgetStrategy.objects.get_or_create(
                name=strategy_data['name'],
                defaults={
                    **strategy_data,
                    'created_by': user
                }
            )
            
            if created:
                self.stdout.write(f"  ✅ Created: {strategy.name}")
                # Add industries
                for industry in industries_list:
                    if industry:
                        strategy.industries.add(industry)
            else:
                self.stdout.write(f"  ⏭️ Exists: {strategy.name}")

    def create_ad_templates(self):
        """Create standard ad templates"""
        self.stdout.write("📝 Creating Ad Templates...")
        
        # Get or create demo user
        user, created = User.objects.get_or_create(
            username='demo',
            defaults={'email': 'demo@example.com'}
        )
        
        # Get industries
        vvs_industry = Industry.objects.filter(name__icontains='VVS').first()
        handvaerker_industry = Industry.objects.filter(name__icontains='Håndværker').first()
        
        if not vvs_industry:
            self.stdout.write("  ❌ VVS industry not found - creating one")
            vvs_industry = Industry.objects.create(
                name='VVS',
                description='VVS og sanitets branchen',
                icon='🔧',
                color='#2563EB'
            )
        
        templates = [
            {
                'name': 'VVS Standard med Pris',
                'description': 'Standard template for VVS services med prisfokus',
                'industry': vvs_industry,
                'headline_1_pattern': '{PRIMARY_KEYWORD} fra kun {PRICE},-',
                'headline_2_pattern': '{USP_TRUST}',
                'headline_3_pattern': '{USP_CTA}',
                'description_1_pattern': 'Professionel {SERVICE} af erfarne VVS-folk. {USP_TRUST}.',
                'description_2_pattern': '{USP_SPEED}. {USP_CTA}.',
                'final_url_pattern': '{BASE_URL}/{SERVICE_SLUG}',
                'prioritize_trust_usps': True,
                'prioritize_speed_usps': True,
                'prioritize_price_usps': True,
                'require_cta_usp': True,
                'is_default': True
            },
            {
                'name': 'VVS Akut Service',
                'description': 'Template for akutte VVS services med hastighedsfokus',
                'industry': vvs_industry,
                'headline_1_pattern': 'Akut {PRIMARY_KEYWORD}',
                'headline_2_pattern': '{USP_SPEED}',
                'headline_3_pattern': '{USP_CTA}',
                'description_1_pattern': '{USP_SPEED} - Professionel {SERVICE}. {USP_TRUST}.',
                'description_2_pattern': 'Ring nu og få hjælp i dag. {USP_CTA}.',
                'final_url_pattern': '{BASE_URL}/akut/{SERVICE_SLUG}',
                'prioritize_trust_usps': True,
                'prioritize_speed_usps': True,
                'prioritize_price_usps': False,
                'require_cta_usp': True,
                'is_default': False
            }
        ]
        
        if handvaerker_industry:
            templates.append({
                'name': 'Håndværker Standard',
                'description': 'Generel template for håndværker services',
                'industry': handvaerker_industry,
                'headline_1_pattern': 'Professionel {PRIMARY_KEYWORD}',
                'headline_2_pattern': '{USP_TRUST}',
                'headline_3_pattern': '{USP_CTA}',
                'description_1_pattern': 'Kvalitets {SERVICE} af erfarne håndværkere. {USP_TRUST}.',
                'description_2_pattern': '{USP_SPEED}. {USP_CTA}.',
                'final_url_pattern': '{BASE_URL}/{SERVICE_SLUG}',
                'prioritize_trust_usps': True,
                'prioritize_speed_usps': True,
                'prioritize_price_usps': False,
                'require_cta_usp': True,
                'is_default': True
            })
        
        for template_data in templates:
            template, created = AdTemplate.objects.get_or_create(
                name=template_data['name'],
                industry=template_data['industry'],
                defaults={
                    **template_data,
                    'created_by': user
                }
            )
            
            if created:
                self.stdout.write(f"  ✅ Created: {template.name} for {template.industry.name}")
            else:
                self.stdout.write(f"  ⏭️ Exists: {template.name}")

    def update_usp_cta_flags(self):
        """Update existing USPs to mark CTAs"""
        self.stdout.write("📞 Updating USP CTA flags...")
        
        # CTA keywords to identify CTAs
        cta_keywords = [
            'ring', 'få en pris', 'få pris', 'kontakt', 'tilbud', 'book', 
            'bestil', 'kald', 'opkald', 'telefon', 'pris på', 'gratis tilbud'
        ]
        
        usps = USPTemplate.objects.filter(is_active=True)
        updated_count = 0
        
        for usp in usps:
            usp_text_lower = usp.text.lower()
            is_cta = any(keyword in usp_text_lower for keyword in cta_keywords)
            
            if is_cta and not usp.is_cta:
                usp.is_cta = True
                usp.save(update_fields=['is_cta'])
                self.stdout.write(f"  ✅ Marked as CTA: {usp.text[:50]}...")
                updated_count += 1
        
        self.stdout.write(f"  📊 Updated {updated_count} USPs with CTA flag")