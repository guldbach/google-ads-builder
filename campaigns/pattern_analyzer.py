import json
import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
from decimal import Decimal
from django.db.models import Avg, Count, Sum, Q
import openai
from decouple import config

from .models import (
    HistoricalCampaignPerformance, 
    HistoricalKeywordPerformance, 
    IndustryPerformancePattern,
    Industry
)


class PerformancePatternAnalyzer:
    """Analysér performance data og identificér mønstre per branche"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=config('OPENAI_API_KEY', ''))
        
    def analyze_all_patterns(self) -> Dict:
        """Kør fuld analyse af alle data og opret patterns"""
        
        results = {
            'keyword_patterns': self.analyze_keyword_patterns(),
            'budget_patterns': self.analyze_budget_patterns(), 
            'negative_keyword_patterns': self.analyze_negative_keyword_patterns(),
            'ad_structure_patterns': self.analyze_ad_structure_patterns()
        }
        
        return results
    
    def analyze_keyword_patterns(self) -> Dict:
        """Analysér keyword mønstre per branche"""
        
        # Group keywords by industry
        industries = HistoricalKeywordPerformance.objects.values('industry_category').distinct()
        
        patterns_created = 0
        
        for industry_data in industries:
            industry = industry_data['industry_category']
            if not industry or industry == 'Andre':
                continue
                
            # Get top performing keywords for this industry
            top_keywords = HistoricalKeywordPerformance.objects.filter(
                industry_category=industry,
                conversions__gte=3,  # Minimum 3 conversions
                cost_per_conversion__isnull=False
            ).order_by('cost_per_conversion')[:50]
            
            if len(top_keywords) < 5:  # Need minimum data
                continue
            
            # Analyze patterns in these keywords
            keyword_analysis = self._analyze_keywords_for_industry(industry, top_keywords)
            
            if keyword_analysis:
                # Save pattern to database
                pattern, created = IndustryPerformancePattern.objects.update_or_create(
                    industry_name=industry,
                    pattern_type='keyword_pattern',
                    defaults={
                        'pattern_data': keyword_analysis,
                        'sample_size': len(top_keywords),
                        'confidence_score': self._calculate_confidence_score(len(top_keywords)),
                        'avg_cost_per_conversion': top_keywords.aggregate(
                            avg_cost=Avg('cost_per_conversion')
                        )['avg_cost'],
                        'avg_conversion_rate': top_keywords.aggregate(
                            avg_rate=Avg('conversions')
                        )['avg_rate'],
                        'avg_ctr': top_keywords.aggregate(
                            avg_ctr=Avg('ctr')
                        )['avg_ctr']
                    }
                )
                
                if created:
                    patterns_created += 1
        
        return {
            'patterns_created': patterns_created,
            'industries_analyzed': industries.count()
        }
    
    def analyze_budget_patterns(self) -> Dict:
        """Analysér budget og performance mønstre"""
        
        industries = HistoricalCampaignPerformance.objects.values('industry_category').distinct()
        patterns_created = 0
        
        for industry_data in industries:
            industry = industry_data['industry_category']
            if not industry or industry == 'Andre':
                continue
            
            # Get campaigns for this industry
            campaigns = HistoricalCampaignPerformance.objects.filter(
                industry_category=industry,
                conversions__gte=5,
                cost_per_conversion__isnull=False
            )
            
            if len(campaigns) < 3:
                continue
            
            # Analyze budget patterns
            budget_analysis = self._analyze_budget_patterns_for_industry(industry, campaigns)
            
            if budget_analysis:
                pattern, created = IndustryPerformancePattern.objects.update_or_create(
                    industry_name=industry,
                    pattern_type='budget_pattern',
                    defaults={
                        'pattern_data': budget_analysis,
                        'sample_size': len(campaigns),
                        'confidence_score': self._calculate_confidence_score(len(campaigns)),
                        'avg_cost_per_conversion': campaigns.aggregate(
                            avg_cost=Avg('cost_per_conversion')
                        )['avg_cost']
                    }
                )
                
                if created:
                    patterns_created += 1
        
        return {
            'patterns_created': patterns_created,
            'industries_analyzed': industries.count()
        }
    
    def analyze_negative_keyword_patterns(self) -> Dict:
        """Analysér og generér negative keyword patterns baseret på poor performing keywords"""
        
        # Find keywords med høj cost per conversion eller lav conversion rate
        poor_keywords = HistoricalKeywordPerformance.objects.filter(
            Q(cost_per_conversion__gt=500) |  # Højere end 500 DKK per conversion
            Q(conversions=0, clicks__gte=20)  # Mange clicks men ingen conversions
        ).values('keyword', 'industry_category')
        
        # Group by industry
        industry_negative_keywords = defaultdict(list)
        
        for keyword_data in poor_keywords:
            industry = keyword_data['industry_category']
            keyword = keyword_data['keyword'].lower()
            
            if industry and industry != 'Andre':
                industry_negative_keywords[industry].append(keyword)
        
        patterns_created = 0
        
        for industry, negative_keywords in industry_negative_keywords.items():
            if len(negative_keywords) < 3:
                continue
            
            # Analyze patterns in negative keywords
            negative_patterns = self._extract_negative_keyword_patterns(negative_keywords)
            
            # Add common negative keywords
            common_negatives = self._get_common_negative_keywords(industry)
            negative_patterns.extend(common_negatives)
            
            pattern_data = {
                'negative_keywords': list(set(negative_patterns)),
                'sample_poor_keywords': negative_keywords[:20],
                'pattern_explanation': f"Negative keywords baseret på poor performing keywords i {industry}"
            }
            
            pattern, created = IndustryPerformancePattern.objects.update_or_create(
                industry_name=industry,
                pattern_type='negative_keywords',
                defaults={
                    'pattern_data': pattern_data,
                    'sample_size': len(negative_keywords),
                    'confidence_score': self._calculate_confidence_score(len(negative_keywords))
                }
            )
            
            if created:
                patterns_created += 1
        
        return {
            'patterns_created': patterns_created,
            'total_negative_keywords': sum(len(keywords) for keywords in industry_negative_keywords.values())
        }
    
    def analyze_ad_structure_patterns(self) -> Dict:
        """Analysér kampagne og ad group struktur mønstre"""
        
        # This would be implemented when we have ad performance data
        # For now, return basic structure recommendations
        
        industries = HistoricalCampaignPerformance.objects.values('industry_category').distinct()
        patterns_created = 0
        
        for industry_data in industries:
            industry = industry_data['industry_category']
            if not industry or industry == 'Andre':
                continue
            
            # Basic structure recommendations based on industry
            structure_recommendations = self._get_basic_structure_recommendations(industry)
            
            pattern, created = IndustryPerformancePattern.objects.update_or_create(
                industry_name=industry,
                pattern_type='ad_structure_pattern',
                defaults={
                    'pattern_data': structure_recommendations,
                    'sample_size': 1,
                    'confidence_score': 0.6  # Lower confidence for basic recommendations
                }
            )
            
            if created:
                patterns_created += 1
        
        return {
            'patterns_created': patterns_created
        }
    
    def _analyze_keywords_for_industry(self, industry: str, keywords) -> Dict:
        """Analysér keyword mønstre for en specifik branche"""
        
        keyword_texts = [kw.keyword.lower() for kw in keywords]
        
        # Extract common patterns
        patterns = {
            'high_intent_patterns': [],
            'location_patterns': [],
            'service_patterns': [],
            'urgency_patterns': [],
            'match_type_recommendations': {},
            'avg_performance': {}
        }
        
        # Analyze match types
        match_type_performance = defaultdict(list)
        for kw in keywords:
            match_type_performance[kw.match_type].append(float(kw.cost_per_conversion or 0))
        
        for match_type, costs in match_type_performance.items():
            patterns['match_type_recommendations'][match_type] = {
                'avg_cost_per_conversion': sum(costs) / len(costs) if costs else 0,
                'recommendation_score': len(costs)
            }
        
        # Common word patterns
        all_words = []
        for keyword in keyword_texts:
            all_words.extend(keyword.split())
        
        word_counts = Counter(all_words)
        common_words = [word for word, count in word_counts.most_common(20) if count >= 2]
        
        # Categorize patterns
        location_words = ['København', 'århus', 'odense', 'aalborg', 'esbjerg', 'lokal', 'nær', 'område']
        urgency_words = ['akut', 'hurtigt', 'samme dag', 'emergency', 'øjeblikkelig', 'nu']
        
        patterns['location_patterns'] = [word for word in common_words if any(loc in word.lower() for loc in location_words)]
        patterns['urgency_patterns'] = [word for word in common_words if any(urg in word.lower() for urg in urgency_words)]
        patterns['service_patterns'] = [word for word in common_words if word not in patterns['location_patterns'] + patterns['urgency_patterns']]
        
        # High intent indicators
        high_intent_indicators = ['pris', 'køb', 'bestil', 'tilbud', 'få hjælp', 'løsning']
        patterns['high_intent_patterns'] = [word for word in common_words if any(intent in word.lower() for intent in high_intent_indicators)]
        
        # Calculate average performance
        patterns['avg_performance'] = {
            'avg_cost_per_conversion': float(sum(float(kw.cost_per_conversion or 0) for kw in keywords) / len(keywords)),
            'avg_conversions': float(sum(kw.conversions for kw in keywords) / len(keywords)),
            'avg_ctr': float(sum(kw.ctr for kw in keywords) / len(keywords))
        }
        
        return patterns
    
    def _analyze_budget_patterns_for_industry(self, industry: str, campaigns) -> Dict:
        """Analysér budget mønstre for en branche"""
        
        # Calculate budget ranges and performance
        costs = [float(campaign.total_cost) for campaign in campaigns]
        conversions = [campaign.conversions for campaign in campaigns]
        cost_per_conv = [float(campaign.cost_per_conversion) for campaign in campaigns if campaign.cost_per_conversion]
        
        if not costs or not cost_per_conv:
            return None
        
        # Calculate percentiles for budget recommendations
        costs.sort()
        n = len(costs)
        
        budget_patterns = {
            'recommended_daily_budget_ranges': {
                'small': {
                    'min': costs[0],
                    'max': costs[int(n * 0.33)] if n > 3 else costs[-1],
                    'description': 'Konservativ start'
                },
                'medium': {
                    'min': costs[int(n * 0.33)] if n > 3 else costs[0],
                    'max': costs[int(n * 0.66)] if n > 3 else costs[-1],
                    'description': 'Moderat investering'
                },
                'large': {
                    'min': costs[int(n * 0.66)] if n > 3 else costs[0],
                    'max': costs[-1],
                    'description': 'Aggressiv vækst'
                }
            },
            'performance_expectations': {
                'avg_cost_per_conversion': sum(cost_per_conv) / len(cost_per_conv),
                'avg_monthly_conversions': sum(conversions) / len(conversions),
                'budget_efficiency_score': len([c for c in cost_per_conv if c < 300]) / len(cost_per_conv)  # % under 300 DKK
            },
            'industry_benchmarks': {
                'best_cost_per_conversion': min(cost_per_conv),
                'worst_cost_per_conversion': max(cost_per_conv),
                'median_cost_per_conversion': sorted(cost_per_conv)[len(cost_per_conv)//2]
            }
        }
        
        return budget_patterns
    
    def _extract_negative_keyword_patterns(self, negative_keywords: List[str]) -> List[str]:
        """Extract mønstre fra poor performing keywords til negative keywords"""
        
        negative_patterns = []
        
        # Common negative patterns
        common_negatives = [
            'gratis', 'free', 'diy', 'selv', 'job', 'jobs', 'arbejde', 'stillinger',
            'kurser', 'uddannelse', 'wikipedia', 'hvad er', 'definition',
            'brugt', 'used', 'second hand', 'køb og salg'
        ]
        
        negative_patterns.extend(common_negatives)
        
        # Extract words that appear frequently in poor performers
        all_words = []
        for keyword in negative_keywords:
            all_words.extend(keyword.split())
        
        word_counts = Counter(all_words)
        frequent_poor_words = [word for word, count in word_counts.most_common(10) if count >= 3]
        
        # Filter out service-specific words (don't want to negative those)
        service_words = ['reparation', 'installation', 'service', 'hjælp', 'løsning']
        filtered_words = [word for word in frequent_poor_words if word.lower() not in service_words]
        
        negative_patterns.extend(filtered_words)
        
        return list(set(negative_patterns))
    
    def _get_common_negative_keywords(self, industry: str) -> List[str]:
        """Get industry-specific negative keywords"""
        
        industry_negatives = {
            'VVS': ['diy', 'selv', 'youtube', 'guide', 'job', 'jobs', 'uddannelse'],
            'El': ['diy', 'selv', 'fare', 'farlig', 'job', 'jobs', 'kurser'],
            'Advokat': ['gratis', 'free', 'selv', 'diy', 'job', 'jobs', 'uddannelse'],
            'Tandlæge': ['gratis', 'free', 'job', 'jobs', 'tandplejer', 'uddannelse'],
            'Læge': ['gratis', 'free', 'job', 'jobs', 'uddannelse', 'sygeplejerske'],
            'Bilmekaniker': ['diy', 'selv', 'guide', 'job', 'jobs', 'uddannelse'],
            'Rengøring': ['diy', 'selv', 'tips', 'job', 'jobs', 'deltid'],
        }
        
        return industry_negatives.get(industry, ['gratis', 'free', 'job', 'jobs', 'diy', 'selv'])
    
    def _get_basic_structure_recommendations(self, industry: str) -> Dict:
        """Basic kampagne struktur anbefalinger per branche"""
        
        # Industry-specific recommendations
        structures = {
            'VVS': {
                'recommended_campaigns': ['Brand', 'Service Typer', 'Acute/Emergency', 'Geografisk'],
                'recommended_ad_groups_per_campaign': 3,
                'recommended_keywords_per_ad_group': 10,
                'bidding_strategy': 'Target CPA',
                'typical_target_cpa_dkk': 250
            },
            'El': {
                'recommended_campaigns': ['Brand', 'Service Typer', 'Emergency', 'Geografisk'],
                'recommended_ad_groups_per_campaign': 3,
                'recommended_keywords_per_ad_group': 8,
                'bidding_strategy': 'Target CPA',
                'typical_target_cpa_dkk': 200
            },
            'Advokat': {
                'recommended_campaigns': ['Brand', 'Practice Areas', 'Geografisk'],
                'recommended_ad_groups_per_campaign': 4,
                'recommended_keywords_per_ad_group': 12,
                'bidding_strategy': 'Maximize Conversions',
                'typical_target_cpa_dkk': 500
            }
        }
        
        return structures.get(industry, {
            'recommended_campaigns': ['Brand', 'Services', 'Geografisk'],
            'recommended_ad_groups_per_campaign': 3,
            'recommended_keywords_per_ad_group': 10,
            'bidding_strategy': 'Target CPA',
            'typical_target_cpa_dkk': 300
        })
    
    def _calculate_confidence_score(self, sample_size: int) -> float:
        """Beregn confidence score baseret på sample størrelse"""
        
        if sample_size >= 50:
            return 0.95
        elif sample_size >= 25:
            return 0.85
        elif sample_size >= 10:
            return 0.75
        elif sample_size >= 5:
            return 0.65
        else:
            return 0.5
    
    def get_patterns_for_industry(self, industry_name: str) -> Dict:
        """Hent alle patterns for en specifik branche"""
        
        patterns = IndustryPerformancePattern.objects.filter(
            industry_name=industry_name
        )
        
        result = {}
        for pattern in patterns:
            result[pattern.pattern_type] = {
                'data': pattern.pattern_data,
                'confidence': pattern.confidence_score,
                'sample_size': pattern.sample_size,
                'last_updated': pattern.last_updated
            }
        
        return result