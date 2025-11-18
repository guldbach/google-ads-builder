# Danish Cities Lookup Service
# Automatisk hentning af korrekte danske bynavne til Google Ads

import requests
import time
import json
from typing import Dict, Optional

class DanishCitiesLookup:
    """Service til at hente korrekte danske bynavne og synonymer"""
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Google-Ads-Builder/1.0 (Danish Cities Lookup)'
        })
    
    def get_city_info(self, city_name: str, postal_code: str = None) -> Optional[Dict]:
        """
        Hent komplet information om en dansk by
        
        Args:
            city_name: Bynavnet (f.eks. "Odense")
            postal_code: Postnummer (f.eks. "5000") - valgfri
            
        Returns:
            Dict med byinformation eller None hvis ikke fundet
        """
        # Opbyg søgeterm
        query = f"{city_name}, Denmark"
        if postal_code:
            query = f"{city_name}, {postal_code}, Denmark"
        
        try:
            # Kald Nominatim API
            response = self.session.get(f"{self.base_url}/search", params={
                'q': query,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1,
                'countrycodes': 'dk'
            })
            
            # Rate limiting - vær venlig mod API'et
            time.sleep(1)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return self._parse_city_data(data[0])
            
        except Exception as e:
            print(f"Fejl ved hentning af data for {city_name}: {e}")
            
        return None
    
    def _parse_city_data(self, raw_data: Dict) -> Dict:
        """Parse raw API data til struktureret byinformation"""
        
        address = raw_data.get('address', {})
        
        # Udtræk relevante felter
        city = address.get('city') or address.get('town') or address.get('village')
        municipality = address.get('municipality', '')
        state = address.get('state', '')
        postcode = address.get('postcode', '')
        
        # Opbyg Google Ads kompatibelt navn
        google_ads_name = city
        if municipality:
            google_ads_name += f", {municipality}"
        if state:
            google_ads_name += f", {state}"
        google_ads_name += ", Danmark"
        
        return {
            'city_name': city,
            'municipality': municipality,
            'region': state,
            'postal_code': postcode,
            'country': 'Danmark',
            'google_ads_synonym': google_ads_name,
            'display_name': raw_data.get('display_name', ''),
            'latitude': float(raw_data.get('lat', 0)),
            'longitude': float(raw_data.get('lon', 0)),
            'coordinates_string': f"{raw_data.get('lat', '')},{raw_data.get('lon', '')}"
        }
    
    def lookup_multiple_cities(self, cities: list) -> Dict[str, Dict]:
        """
        Hent information for flere byer på én gang
        
        Args:
            cities: Liste af dicts med 'name' og evt 'postal_code'
            
        Returns:
            Dict med bynavn som nøgle og byinfo som værdi
        """
        results = {}
        
        for city_data in cities:
            city_name = city_data.get('name', '')
            postal_code = city_data.get('postal_code', '')
            
            if city_name:
                info = self.get_city_info(city_name, postal_code)
                if info:
                    results[city_name] = info
                else:
                    print(f"Kunne ikke finde information for: {city_name}")
        
        return results


# Predefinerede danske byer med korrekte synonymer
DANISH_CITIES_COMMON = {
    'København': 'København, Københavns Kommune, Region Hovedstaden, Danmark',
    'Aarhus': 'Aarhus, Aarhus Kommune, Region Midtjylland, Danmark', 
    'Odense': 'Odense, Odense Kommune, Region Syddanmark, Danmark',
    'Aalborg': 'Aalborg, Aalborg Kommune, Region Nordjylland, Danmark',
    'Esbjerg': 'Esbjerg, Esbjerg Kommune, Region Syddanmark, Danmark',
    'Randers': 'Randers, Randers Kommune, Region Midtjylland, Danmark',
    'Kolding': 'Kolding, Kolding Kommune, Region Syddanmark, Danmark',
    'Horsens': 'Horsens, Horsens Kommune, Region Midtjylland, Danmark',
    'Vejle': 'Vejle, Vejle Kommune, Region Syddanmark, Danmark',
    'Roskilde': 'Roskilde, Roskilde Kommune, Region Sjælland, Danmark',
    'Herning': 'Herning, Herning Kommune, Region Midtjylland, Danmark',
    'Hørsholm': 'Hørsholm, Hørsholm Kommune, Region Hovedstaden, Danmark',
    'Silkeborg': 'Silkeborg, Silkeborg Kommune, Region Midtjylland, Danmark',
    'Næstved': 'Næstved, Næstved Kommune, Region Sjælland, Danmark',
    'Fredericia': 'Fredericia, Fredericia Kommune, Region Syddanmark, Danmark',
    'Viborg': 'Viborg, Viborg Kommune, Region Midtjylland, Danmark',
    'Køge': 'Køge, Køge Kommune, Region Sjælland, Danmark',
    'Holstebro': 'Holstebro, Holstebro Kommune, Region Midtjylland, Danmark',
    'Taastrup': 'Taastrup, Høje-Taastrup Kommune, Region Hovedstaden, Danmark',
    'Slagelse': 'Slagelse, Slagelse Kommune, Region Sjælland, Danmark'
}


def get_google_ads_synonym(city_name: str, postal_code: str = None) -> str:
    """
    Hurtig funktion til at få Google Ads synonym for en by
    
    Args:
        city_name: Bynavnet
        postal_code: Postnummer (valgfri)
        
    Returns:
        Google Ads kompatibelt bynavn
    """
    
    # Tjek først common cities cache
    if city_name in DANISH_CITIES_COMMON:
        return DANISH_CITIES_COMMON[city_name]
    
    # Ellers brug API lookup
    lookup = DanishCitiesLookup()
    info = lookup.get_city_info(city_name, postal_code)
    
    if info:
        return info['google_ads_synonym']
    
    # Fallback til simpelt format
    return f"{city_name}, Danmark"


# Test funktion
if __name__ == "__main__":
    # Test med vores fire byer
    test_cities = [
        {'name': 'Husum', 'postal_code': '2650'},
        {'name': 'Greve', 'postal_code': '2670'},
        {'name': 'Odense', 'postal_code': '5000'},
        {'name': 'Aalborg', 'postal_code': '9000'}
    ]
    
    lookup = DanishCitiesLookup()
    results = lookup.lookup_multiple_cities(test_cities)
    
    print("🎯 Korrekte Google Ads synonymer:")
    for city, info in results.items():
        print(f"• {city}: {info['google_ads_synonym']}")
        print(f"  Koordinater: {info['coordinates_string']}")
        print()