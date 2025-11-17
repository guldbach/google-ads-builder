"""
Service klasser til negative keywords management
"""
from typing import List, Dict, Set, Tuple
from .models import NegativeKeyword, NegativeKeywordList
import re


class NegativeKeywordConflictAnalyzer:
    """
    Analyserer konflikter mellem negative keywords baseret på match type hierarkier.
    
    Hierarki:
    - Broad Match: Påvirker alle keywords der indeholder teksten
    - Phrase Match: Påvirker exact matches af samme phrase
    - Exact Match: Påvirker kun identiske keywords
    """
    
    def __init__(self, keyword_list: NegativeKeywordList):
        self.keyword_list = keyword_list
        self.existing_keywords = self._get_existing_keywords()
    
    def _get_existing_keywords(self) -> Dict[str, List[Dict]]:
        """Hent eksisterende keywords organiseret efter match type"""
        keywords = self.keyword_list.negative_keywords.all()
        
        organized = {
            'broad': [],
            'phrase': [],
            'exact': []
        }
        
        for kw in keywords:
            organized[kw.match_type].append({
                'id': kw.id,
                'text': kw.keyword_text.lower().strip(),
                'original_text': kw.keyword_text,
                'match_type': kw.match_type
            })
        
        return organized
    
    def analyze_import(self, import_keywords: List[Dict]) -> Dict:
        """
        Analyserer en liste af keywords for import.
        
        Args:
            import_keywords: Liste af {'text': str, 'match_type': str}
        
        Returns:
            Dict med analyse resultat
        """
        result = {
            'total_keywords': len(import_keywords),
            'conflicts': [],
            'safe_to_add': [],
            'will_make_redundant': [],  # Import vil gøre existing redundante
            'blocked_by_existing': [],  # Import blokeret af existing hierarki
            'redundant_in_upload': [],
            'optimizations': [],
            'cleanup_suggestions': []
        }
        
        # Normaliser import keywords
        normalized_import = []
        for kw in import_keywords:
            normalized = {
                'text': kw['text'].lower().strip(),
                'original_text': kw['text'],
                'match_type': kw['match_type']
            }
            normalized_import.append(normalized)
        
        # Find relationelle konflikter med eksisterende keywords
        for import_kw in normalized_import:
            relationships = self._analyze_all_relationships(import_kw)
            
            if relationships['identical'] or relationships['blocked_by']:
                # Import blokeret af eksisterende - KONFLIKT for frontend
                blocking_keywords = relationships['identical'] + relationships['blocked_by']
                result['conflicts'].append({
                    'import_keyword': import_kw,
                    'conflicting_keywords': blocking_keywords,
                    'reason': self._explain_blocking(import_kw, relationships)
                })
                # Også gem i ny struktur for backend logik
                result['blocked_by_existing'].append({
                    'import_keyword': import_kw,
                    'blocking_keywords': blocking_keywords,
                    'reason': self._explain_blocking(import_kw, relationships)
                })
            elif relationships['will_override']:
                # Import vil overskrive eksisterende - KAN TILFØJES for frontend (med cleanup)
                result['safe_to_add'].append(import_kw)
                # Også gem i ny struktur for backend logik  
                result['will_make_redundant'].append({
                    'import_keyword': import_kw,
                    'keywords_to_remove': relationships['will_override'],
                    'reason': self._explain_override(import_kw, relationships['will_override'])
                })
            else:
                # Ingen konflikter - safe to add
                result['safe_to_add'].append(import_kw)
        
        # Find redundans i upload (keywords der påvirker hinanden)
        result['redundant_in_upload'] = self._find_upload_redundancy(normalized_import)
        
        # Generer optimeringsforslag
        result['optimizations'] = self._suggest_optimizations(normalized_import)
        
        # Generer cleanup forslag
        result['cleanup_suggestions'] = self._suggest_cleanup(normalized_import)
        
        return result
    
    def _find_conflicts(self, import_keyword: Dict) -> List[Dict]:
        """Find eksisterende keywords der konflikter med import keyword"""
        conflicts = []
        import_text = import_keyword['text']
        import_match = import_keyword['match_type']
        
        # Check mod broad match keywords (de påvirker alt der indeholder teksten)
        for existing in self.existing_keywords['broad']:
            if self._is_affected_by_broad(import_text, existing['text']):
                conflicts.append(existing)
        
        # Check mod phrase match keywords
        for existing in self.existing_keywords['phrase']:
            if self._is_affected_by_phrase(import_text, import_match, existing['text']):
                conflicts.append(existing)
        
        # Check mod exact match keywords
        for existing in self.existing_keywords['exact']:
            if self._is_affected_by_exact(import_text, import_match, existing['text']):
                conflicts.append(existing)
        
        return conflicts
    
    def _is_affected_by_broad(self, import_text: str, broad_keyword: str) -> bool:
        """
        Tjek om import keyword bliver påvirket af eksisterende broad match.
        Broad match påvirker alt der indeholder keyword-teksten.
        """
        # Broad match keywords påvirker alt der indeholder teksten som ord
        broad_words = set(broad_keyword.split())
        import_words = set(import_text.split())
        
        # Hvis alle ord fra broad keyword findes i import keyword, så påvirkes det
        return broad_words.issubset(import_words)
    
    def _is_affected_by_phrase(self, import_text: str, import_match: str, phrase_keyword: str) -> bool:
        """
        Tjek om import keyword bliver påvirket af eksisterende phrase match.
        Phrase match påvirker exact matches af samme phrase og identiske phrase matches.
        """
        # Phrase match påvirker både exact og phrase matches med identisk tekst
        if import_match in ['exact', 'phrase']:
            return import_text.strip() == phrase_keyword.strip()
        
        return False
    
    def _is_affected_by_exact(self, import_text: str, import_match: str, exact_keyword: str) -> bool:
        """
        Tjek om import keyword bliver påvirket af eksisterende exact match.
        Exact match påvirker både exact og phrase matches med identisk tekst.
        """
        # Exact match påvirker både exact og phrase matches med identisk tekst
        if import_match in ['exact', 'phrase']:
            return import_text.strip() == exact_keyword.strip()
        
        return False
    
    def _find_upload_redundancy(self, import_keywords: List[Dict]) -> List[Dict]:
        """Find keywords i upload der påvirker hinanden"""
        redundant = []
        
        for i, kw1 in enumerate(import_keywords):
            for j, kw2 in enumerate(import_keywords[i+1:], i+1):
                if self._keywords_conflict(kw1, kw2):
                    redundant.append({
                        'keyword1': kw1,
                        'keyword2': kw2,
                        'recommendation': self._get_redundancy_recommendation(kw1, kw2)
                    })
        
        return redundant
    
    def _keywords_conflict(self, kw1: Dict, kw2: Dict) -> bool:
        """Tjek om to keywords konflikter med hinanden"""
        if kw1['match_type'] == 'broad':
            return self._is_affected_by_broad(kw2['text'], kw1['text'])
        elif kw2['match_type'] == 'broad':
            return self._is_affected_by_broad(kw1['text'], kw2['text'])
        elif kw1['match_type'] == 'phrase' and kw2['match_type'] == 'exact':
            return self._is_affected_by_phrase(kw2['text'], kw2['match_type'], kw1['text'])
        elif kw2['match_type'] == 'phrase' and kw1['match_type'] == 'exact':
            return self._is_affected_by_phrase(kw1['text'], kw1['match_type'], kw2['text'])
        else:
            return False
    
    def _get_redundancy_recommendation(self, kw1: Dict, kw2: Dict) -> str:
        """Få anbefaling for hvordan man håndterer redundante keywords"""
        match_hierarchy = {'broad': 3, 'phrase': 2, 'exact': 1}
        
        if match_hierarchy[kw1['match_type']] > match_hierarchy[kw2['match_type']]:
            return f"Behold '{kw1['original_text']}' ({kw1['match_type']}) - det er mere effektivt"
        else:
            return f"Behold '{kw2['original_text']}' ({kw2['match_type']}) - det er mere effektivt"
    
    def _suggest_optimizations(self, import_keywords: List[Dict]) -> List[Dict]:
        """Foreslå optimering af keyword listen"""
        optimizations = []
        
        # Grouped by broad potential
        broad_groups = {}
        for kw in import_keywords:
            words = tuple(sorted(kw['text'].split()))
            if len(words) == 1:  # Single word could be broad
                base_word = words[0]
                if base_word not in broad_groups:
                    broad_groups[base_word] = []
                broad_groups[base_word].append(kw)
        
        # Foreslå broad match optimering
        for base_word, keywords in broad_groups.items():
            if len(keywords) > 1:
                affected_keywords = []
                for kw in import_keywords:
                    if base_word in kw['text'].split() and kw not in keywords:
                        affected_keywords.append(kw)
                
                if affected_keywords:
                    optimizations.append({
                        'type': 'broad_optimization',
                        'suggestion': f"Tilføj '{base_word}' (broad) og slet {len(affected_keywords)} påvirkede keywords",
                        'new_keyword': {'text': base_word, 'match_type': 'broad'},
                        'keywords_to_remove': affected_keywords,
                        'efficiency_gain': len(affected_keywords)
                    })
        
        return optimizations
    
    def _suggest_cleanup(self, import_keywords: List[Dict]) -> List[Dict]:
        """Foreslå oprydning i eksisterende keywords baseret på import"""
        suggestions = []
        
        # Find eksisterende keywords der kunne optimeres
        for import_kw in import_keywords:
            if import_kw['match_type'] == 'broad':
                # Find eksisterende keywords der ville blive påvirket
                affected = []
                import_words = set(import_kw['text'].split())
                
                for match_type in ['phrase', 'exact']:
                    for existing in self.existing_keywords[match_type]:
                        existing_words = set(existing['text'].split())
                        if import_words.issubset(existing_words):
                            affected.append(existing)
                
                if affected:
                    suggestions.append({
                        'type': 'cleanup_opportunity',
                        'new_broad_keyword': import_kw,
                        'keywords_to_remove': affected,
                        'description': f"Hvis du tilføjer '{import_kw['original_text']}' (broad), kan du slette {len(affected)} eksisterende keywords"
                    })
        
        return suggestions
    
    def _explain_conflict(self, import_keyword: Dict, conflicting_keyword: Dict) -> str:
        """Forklarer hvorfor der er en konflikt"""
        conflict_type = conflicting_keyword['match_type']
        
        if conflict_type == 'broad':
            return f"Påvirket af eksisterende '{conflicting_keyword['original_text']}' (broad match) - denne blokerer alle keywords der indeholder ordene"
        elif conflict_type == 'phrase':
            return f"Påvirket af eksisterende '{conflicting_keyword['original_text']}' (phrase match) - identisk phrase"
        else:  # exact
            return f"Identisk med eksisterende '{conflicting_keyword['original_text']}' (exact match)"
    
    def execute_cleanup(self, keyword_ids_to_remove: List[int]) -> Dict:
        """Udfør oprydning af eksisterende keywords"""
        try:
            # Find keywords der skal slettes
            keywords_to_remove = NegativeKeyword.objects.filter(
                id__in=keyword_ids_to_remove,
                keyword_list=self.keyword_list
            )
            
            removed_count = keywords_to_remove.count()
            removed_keywords = list(keywords_to_remove.values_list('keyword_text', flat=True))
            
            # Slet keywords
            keywords_to_remove.delete()
            
            return {
                'success': True,
                'removed_count': removed_count,
                'removed_keywords': removed_keywords
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_keyword_relationship(self, import_kw: Dict, existing_kw: Dict) -> str:
        """
        Analyserer forholdet mellem import keyword og existing keyword.
        
        Returns:
            'no_conflict': Ingen konflikt
            'import_wins': Import keyword skal overskrive existing
            'existing_wins': Existing keyword blokerer import  
            'identical': Identiske keywords
        """
        import_text = import_kw['text']
        import_match = import_kw['match_type']
        existing_text = existing_kw['text']
        existing_match = existing_kw['match_type']
        
        # Hierarki: broad (3) > phrase (2) > exact (1)
        hierarchy = {'broad': 3, 'phrase': 2, 'exact': 1}
        
        # Check for identiske keywords
        if import_text == existing_text and import_match == existing_match:
            return 'identical'
        
        # Check for tekstuel redundans baseret på match type
        if self._keywords_are_redundant(import_kw, existing_kw):
            # Hvis redundante, check hierarki
            if hierarchy[import_match] > hierarchy[existing_match]:
                return 'import_wins'  # Import har højere hierarki
            elif hierarchy[import_match] < hierarchy[existing_match]:
                return 'existing_wins'  # Existing har højere hierarki
            else:
                # Samme hierarki, identical text
                return 'identical'
        
        return 'no_conflict'
    
    def _keywords_are_redundant(self, kw1: Dict, kw2: Dict) -> bool:
        """Check om to keywords er redundante baseret på match type logik"""
        text1, match1 = kw1['text'], kw1['match_type']
        text2, match2 = kw2['text'], kw2['match_type']
        
        # Identisk tekst er altid redundant
        if text1 == text2:
            return True
        
        # Broad match check - hvis en er broad og indeholder ordene fra den anden
        if match1 == 'broad':
            broad_words = set(text1.split())
            other_words = set(text2.split())
            return broad_words.issubset(other_words)
        
        if match2 == 'broad':
            broad_words = set(text2.split())
            other_words = set(text1.split())
            return broad_words.issubset(other_words)
        
        # Phrase vs exact check - kun hvis identisk tekst (allerede checket ovenfor)
        return False
    
    def _analyze_all_relationships(self, import_kw: Dict) -> Dict:
        """Analyserer import keyword mod alle eksisterende keywords"""
        relationships = {
            'identical': [],
            'will_override': [],
            'blocked_by': []
        }
        
        # Check mod alle eksisterende keywords
        for match_type in ['broad', 'phrase', 'exact']:
            for existing_kw in self.existing_keywords[match_type]:
                relationship = self._analyze_keyword_relationship(import_kw, existing_kw)
                
                if relationship == 'identical':
                    relationships['identical'].append(existing_kw)
                elif relationship == 'import_wins':
                    relationships['will_override'].append(existing_kw)
                elif relationship == 'existing_wins':
                    relationships['blocked_by'].append(existing_kw)
        
        return relationships
    
    def _explain_blocking(self, import_kw: Dict, relationships: Dict) -> str:
        """Forklarer hvorfor import bliver blokeret"""
        if relationships['identical']:
            existing = relationships['identical'][0]
            return f"Identisk med eksisterende '{existing['original_text']}' ({existing['match_type']} match)"
        
        if relationships['blocked_by']:
            existing = relationships['blocked_by'][0]
            if existing['match_type'] == 'broad':
                return f"Blokeret af eksisterende '{existing['original_text']}' (broad match) - denne dækker allerede keyword"
            else:
                return f"Blokeret af eksisterende '{existing['original_text']}' ({existing['match_type']} match) - højere hierarki"
        
        return "Ukendt blokeringsårsag"
    
    def _explain_override(self, import_kw: Dict, keywords_to_override: List[Dict]) -> str:
        """Forklarer hvorfor import vil overskrive eksisterende"""
        if not keywords_to_override:
            return ""
        
        count = len(keywords_to_override)
        first_kw = keywords_to_override[0]
        
        if import_kw['match_type'] == 'broad':
            return f"'{import_kw['original_text']}' (broad) vil dække {count} eksisterende keywords og gøre dem redundante"
        elif import_kw['match_type'] == 'phrase':
            return f"'{import_kw['original_text']}' (phrase) vil overskrive '{first_kw['original_text']}' (exact) - bredere dækning"
        
        return f"Vil overskrive {count} keywords med lavere hierarki"