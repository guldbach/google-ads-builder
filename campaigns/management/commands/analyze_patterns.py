from django.core.management.base import BaseCommand
from campaigns.pattern_analyzer import PerformancePatternAnalyzer
import json


class Command(BaseCommand):
    help = 'Analysér performance data og identificér mønstre per branche'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pattern-type',
            type=str,
            choices=['keywords', 'budgets', 'negatives', 'structure', 'all'],
            default='all',
            help='Hvilken type pattern analyse der skal køres'
        )

    def handle(self, *args, **options):
        analyzer = PerformancePatternAnalyzer()
        pattern_type = options['pattern_type']
        
        self.stdout.write(self.style.SUCCESS('Starter pattern analyse...'))
        
        if pattern_type == 'all':
            results = analyzer.analyze_all_patterns()
            self.stdout.write(self.style.SUCCESS('Fuld analyse fuldført!'))
            
            for analysis_type, result in results.items():
                self.stdout.write(f"\n{analysis_type}:")
                self.stdout.write(json.dumps(result, indent=2))
                
        elif pattern_type == 'keywords':
            result = analyzer.analyze_keyword_patterns()
            self.stdout.write(self.style.SUCCESS('Keyword analyse fuldført!'))
            self.stdout.write(json.dumps(result, indent=2))
            
        elif pattern_type == 'budgets':
            result = analyzer.analyze_budget_patterns()
            self.stdout.write(self.style.SUCCESS('Budget analyse fuldført!'))
            self.stdout.write(json.dumps(result, indent=2))
            
        elif pattern_type == 'negatives':
            result = analyzer.analyze_negative_keyword_patterns()
            self.stdout.write(self.style.SUCCESS('Negative keywords analyse fuldført!'))
            self.stdout.write(json.dumps(result, indent=2))
            
        elif pattern_type == 'structure':
            result = analyzer.analyze_ad_structure_patterns()
            self.stdout.write(self.style.SUCCESS('Ad struktur analyse fuldført!'))
            self.stdout.write(json.dumps(result, indent=2))
        
        self.stdout.write(self.style.SUCCESS('\nPattern analyse er færdig! Patterns er gemt i databasen.'))