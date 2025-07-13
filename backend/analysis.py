import requests
import json
import time
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod
import re
from geopy.distance import geodesic
import sqlite3
from urllib.parse import urljoin, urlparse
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PropertyData:
    """Standardized property data structure"""
    property_id: str
    address: str
    city: str
    county: str
    state: str
    zip_code: str
    latitude: float
    longitude: float
    building_area: float  # square feet
    lot_size: float  # square feet
    year_built: int
    zoning: str
    property_type: str
    assessed_value: float
    sale_price: Optional[float] = None
    sale_date: Optional[str] = None
    last_updated: str = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()

class APIRateLimiter:
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests_per_minute = max_requests_per_minute
        self.requests_made = []
        self.backoff_time = 1

    def wait_if_needed(self):
        now = datetime.now()
        self.requests_made = [req_time for req_time in self.requests_made if now - req_time < timedelta(minutes=1)]
        if len(self.requests_made) >= self.max_requests_per_minute:
            sleep_time = 60 - (now - self.requests_made[0]).seconds
            logger.info(f"Rate limit reached, sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
        self.requests_made.append(now)

class APIDiscoveryAgent:
    def __init__(self):
        self.rate_limiter = APIRateLimiter()
        self.api_endpoints = {
            'cook_county': 'https://datacatalog.cookcountyil.gov/resource/tx8h-7rnu.json',
            'dallas_county': 'https://maps.dcad.org/prd/rest/services/Property/PropertyLayer/MapServer/0/query',
            'los_angeles': 'https://data.lacounty.gov/resource/7rjj-f2pv.json'
        }

    def map_field_names(self, api_fields: set) -> Dict[str, str]:
        standard_mappings = {
            'pin': 'property_id',
            'address': 'address',
            'street_address': 'address',
            'property_address': 'address',
            'city': 'city',
            'municipality': 'city',
            'county': 'county',
            'state': 'state',
            'zip': 'zip_code',
            'zip_code': 'zip_code',
            'postal_code': 'zip_code',
            'lat': 'latitude',
            'latitude': 'latitude',
            'lon': 'longitude',
            'longitude': 'longitude',
            'building_area_sq_ft': 'building_area',
            'building_sqft': 'building_area',
            'square_footage': 'building_area',
            'lot_size_sq_ft': 'lot_size',
            'lot_sqft': 'lot_size',
            'parcel_size': 'lot_size',
            'year_built': 'year_built',
            'construction_year': 'year_built',
            'zoning': 'zoning',
            'zoning_code': 'zoning',
            'property_type': 'property_type',
            'assessed_value': 'assessed_value',
            'total_value': 'assessed_value'
        }
        field_mapping = {}
        for api_field in api_fields:
            normalized = api_field.lower().replace('_', '')
            for std_key, std_value in standard_mappings.items():
                if normalized in std_key.lower().replace('_', ''):
                    field_mapping[api_field] = std_value
                    break
        return field_mapping

class MockCountyAPI:
    def __init__(self, county_name: str):
        self.county_name = county_name
        self.properties = self._generate_mock_data()

    def _generate_mock_data(self) -> List[Dict]:
        np.random.seed(42)
        
        # Real industrial areas and their coordinates for each county
        county_industrial_areas = {
            'Cook County': [
                ('Elk Grove Village', [
                    ('Devon', 'Ave'), ('Busse', 'Rd'), ('Elmhurst', 'Rd'),
                    ('Oakton', 'St'), ('Nicholas', 'Blvd'), ('Lively', 'Blvd')
                ]),
                ('Bedford Park', [
                    ('State', 'Rd'), ('Central', 'Ave'), ('Archer', 'Ave'),
                    ('Cicero', 'Ave'), ('Harlem', 'Ave'), ('65th', 'St')
                ])
            ],
            'Dallas County': [
                ('South Stemmons', [
                    ('Mockingbird', 'Ln'), ('Empire Central', 'Dr'), ('Regal Row', 'Rd'),
                    ('Stemmons', 'Fwy'), ('Market Center', 'Blvd'), ('Manufacturing', 'St')
                ]),
                ('West Dallas', [
                    ('Singleton', 'Blvd'), ('Commerce', 'St'), ('Industrial', 'Blvd'),
                    ('Irving', 'Blvd'), ('Conveyor', 'Ln'), ('Distribution', 'Dr')
                ])
            ],
            'Los Angeles County': [
                ('Vernon', [
                    ('Alameda', 'St'), ('Soto', 'St'), ('Pacific', 'Blvd'),
                    ('Washington', 'Blvd'), ('Santa Fe', 'Ave'), ('District', 'Blvd')
                ]),
                ('City of Industry', [
                    ('Valley', 'Blvd'), ('Gale', 'Ave'), ('Azusa', 'Ave'),
                    ('Baldwin Park', 'Blvd'), ('Industry Hills', 'Pkwy'), ('Nelson', 'Ave')
                ])
            ]
        }

        # Base coordinates for each county
        county_coords = {
            'Cook County': (41.8781, -87.6298),
            'Dallas County': (32.7767, -96.7970),
            'Los Angeles County': (34.0522, -118.2437)
        }

        # Building sizes by county (sq ft)
        building_sizes = {
            'Cook County': (25000, 250000),
            'Dallas County': (30000, 300000),
            'Los Angeles County': (20000, 200000)
        }

        # Zoning codes by county
        zoning_by_county = {
            'Cook County': ['M1', 'M2', 'I1', 'I2'],
            'Dallas County': ['IR', 'IM', 'IL'],
            'Los Angeles County': ['M1', 'M2', 'MR1', 'MR2']
        }
        
        base_lat, base_lon = county_coords.get(self.county_name, (40.0, -100.0))
        properties = []
        
        # Get areas for this county
        county_areas = county_industrial_areas.get(self.county_name, [])
        
        for i in range(100):
            # Randomly select an area and its streets
            area_index = np.random.randint(0, len(county_areas))
            area, streets = county_areas[area_index]
            
            # Randomly select a street
            street_index = np.random.randint(0, len(streets))
            street_name, street_type = streets[street_index]
            
            # Generate realistic lat/lon offset
            lat_offset = np.random.uniform(-0.1, 0.1)
            lon_offset = np.random.uniform(-0.1, 0.1)
            
            # Generate building area using log-normal distribution
            min_size, max_size = building_sizes[self.county_name]
            building_area = np.random.lognormal(mean=np.log((min_size + max_size)/2), sigma=0.5)
            building_area = max(min_size, min(max_size, building_area))
            
            # Generate lot size (typically 2-4x building size)
            lot_size = building_area * np.random.uniform(2, 4)
            
            # Calculate assessed value based on location and size
            base_price_per_sqft = {
                'Cook County': np.random.uniform(80, 150),
                'Dallas County': np.random.uniform(60, 120),
                'Los Angeles County': np.random.uniform(100, 200)
            }[self.county_name]
            assessed_value = building_area * base_price_per_sqft * np.random.uniform(0.9, 1.1)
            
            property_data = {
                'property_id': f"{self.county_name[:2].upper()}{i:04d}",
                'address': f"{np.random.randint(100, 9999)} {street_name} {street_type}",
                'city': area,
                'county': self.county_name,
                'state': {'Cook County': 'IL', 'Dallas County': 'TX', 'Los Angeles County': 'CA'}[self.county_name],
                'zip_code': self._generate_zip_code(self.county_name, area),
                'latitude': base_lat + lat_offset,
                'longitude': base_lon + lon_offset,
                'building_area': building_area,
                'lot_size': lot_size,
                'year_built': self._generate_year_built(),
                'zoning': np.random.choice(zoning_by_county[self.county_name]),
                'property_type': 'Industrial',
                'assessed_value': assessed_value
            }
            properties.append(property_data)
        
        return properties

    def _generate_zip_code(self, county: str, area: str) -> str:
        """Generate realistic ZIP codes for each area"""
        zip_ranges = {
            'Cook County': {
                'Elk Grove Village': range(60007, 60009),
                'Bedford Park': range(60501, 60503)
            },
            'Dallas County': {
                'South Stemmons': range(75207, 75209),
                'West Dallas': range(75212, 75214)
            },
            'Los Angeles County': {
                'Vernon': range(90058, 90060),
                'City of Industry': range(91745, 91747)
            }
        }
        return str(np.random.choice(list(zip_ranges[county][area])))

    def _generate_year_built(self) -> int:
        """Generate realistic construction years with distribution favoring certain periods"""
        periods = [
            (1960, 1979, 0.3),  # 30% chance of older buildings
            (1980, 1999, 0.4),  # 40% chance of middle-age buildings
            (2000, 2023, 0.3)   # 30% chance of newer buildings
        ]
        
        period = np.random.choice(len(periods), p=[p[2] for p in periods])
        start_year, end_year, _ = periods[period]
        return np.random.randint(start_year, end_year + 1)

    def get_properties(self, filters: Dict = None) -> List[Dict]:
        """Get properties with optional filters"""
        filtered_properties = self.properties.copy()
        
        if filters:
            if 'zoning' in filters:
                filtered_properties = [p for p in filtered_properties if p['zoning'] in filters['zoning']]
            if 'min_building_area' in filters:
                filtered_properties = [p for p in filtered_properties if p['building_area'] >= filters['min_building_area']]
            if 'max_building_area' in filters:
                filtered_properties = [p for p in filtered_properties if p['building_area'] <= filters['max_building_area']]
            if 'city' in filters:
                filtered_properties = [p for p in filtered_properties if p['city'] == filters['city']]
                
        return filtered_properties


    def _generate_zip_code(self, county: str, area: str) -> str:
        """Generate realistic ZIP codes for each area"""
        zip_ranges = {
            'Cook County': {
                'Elk Grove Village': range(60007, 60009),
                'Bedford Park': range(60501, 60503)
            },
            'Dallas County': {
                'South Stemmons': range(75207, 75209),
                'West Dallas': range(75212, 75214)
            },
            'Los Angeles County': {
                'Vernon': range(90058, 90060),
                'City of Industry': range(91745, 91747)
            }
        }
        return str(np.random.choice(list(zip_ranges[county][area])))

    def _generate_year_built(self) -> int:
        """Generate realistic construction years with distribution favoring certain periods"""
        # Industrial development periods: 1960s-1970s, 1980s-1990s, 2000s-present
        periods = [
            (1960, 1979, 0.3),  # 30% chance of older buildings
            (1980, 1999, 0.4),  # 40% chance of middle-age buildings
            (2000, 2023, 0.3)   # 30% chance of newer buildings
        ]
        
        period = np.random.choice(len(periods), p=[p[2] for p in periods])
        start_year, end_year, _ = periods[period]
        return np.random.randint(start_year, end_year + 1)

    def get_properties(self, filters: Dict = None) -> List[Dict]:
        """Get properties with optional filters"""
        filtered_properties = self.properties.copy()
        
        if filters:
            if 'zoning' in filters:
                filtered_properties = [p for p in filtered_properties if p['zoning'] in filters['zoning']]
            if 'min_building_area' in filters:
                filtered_properties = [p for p in filtered_properties if p['building_area'] >= filters['min_building_area']]
            if 'max_building_area' in filters:
                filtered_properties = [p for p in filtered_properties if p['building_area'] <= filters['max_building_area']]
            if 'city' in filters:
                filtered_properties = [p for p in filtered_properties if p['city'] == filters['city']]
                
        return filtered_properties

class DataExtractionAgent:
    def __init__(self):
        self.rate_limiter = APIRateLimiter()
        self.api_discovery = APIDiscoveryAgent()

    def extract_industrial_properties(self, county: str) -> List[PropertyData]:
        logger.info(f"Extracting industrial properties from {county}")
        mock_api = MockCountyAPI(county)
        properties = mock_api.get_properties(filters={'zoning': ['M1', 'M2', 'I-1', 'I-2', 'IM', 'IL']})
        return [PropertyData(**prop) for prop in properties]

    def _validate_property_data(self, data: Dict) -> bool:
        required_fields = {
            'property_id': str,
            'address': str,
            'building_area': (int, float),
            'latitude': float,
            'longitude': float,
            'zoning': str
        }
        try:
            for field, field_type in required_fields.items():
                if field not in data:
                    return False
                if not isinstance(data[field], field_type):
                    return False
            if data['building_area'] <= 0:
                return False
            if not (-90 <= data['latitude'] <= 90):
                return False
            if not (-180 <= data['longitude'] <= 180):
                return False
            return True
        except:
            return False

    def _clean_property_data(self, data: Dict) -> Dict:
        cleaned = data.copy()
        if 'building_area' in cleaned:
            cleaned['building_area'] = float(cleaned['building_area'])
        if 'lot_size' in cleaned:
            cleaned['lot_size'] = float(cleaned['lot_size'])
        if 'year_built' in cleaned:
            cleaned['year_built'] = int(cleaned['year_built'])
        if 'assessed_value' in cleaned:
            cleaned['assessed_value'] = float(cleaned['assessed_value'])
        if 'address' in cleaned:
            cleaned['address'] = cleaned['address'].title()
        if 'city' in cleaned:
            cleaned['city'] = cleaned['city'].title()
        return cleaned

class ComparableDiscoveryAgent:
    def __init__(self):
        self.properties_db = []
        self.weight_factors = {
            'building_area': 0.30,
            'lot_size': 0.20,
            'age': 0.15,
            'zoning': 0.25,
            'location': 0.10
        }

    def load_properties(self, properties: List[PropertyData]):
        self.properties_db = properties
        logger.info(f"Loaded {len(properties)} properties into comparable discovery system")

    def calculate_similarity_score(self, target: PropertyData, comp: PropertyData) -> float:
        area_ratio = min(target.building_area, comp.building_area) / max(target.building_area, comp.building_area)
        distance = geodesic((target.latitude, target.longitude), (comp.latitude, comp.longitude)).miles
        location_score = max(0, 1 - (distance / 10))
        age_diff = abs(target.year_built - comp.year_built)
        age_score = max(0, 1 - age_diff / 50)
        final_score = (
            area_ratio * self.weight_factors['building_area'] +
            location_score * self.weight_factors['location'] +
            age_score * self.weight_factors['age']
        )
        return final_score

    def find_comparables(self, target: PropertyData, max_results: int = 5) -> List[Tuple[PropertyData, float]]:
        results = []
        for prop in self.properties_db:
            if prop.property_id != target.property_id:
                score = self.calculate_similarity_score(target, prop)
                results.append((prop, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]

class PropertyAnalysisSystem:
    def __init__(self):
        self.api_discovery = APIDiscoveryAgent()
        self.data_extraction = DataExtractionAgent()
        self.comparable_discovery = ComparableDiscoveryAgent()
        self.properties_database = []

    def initialize_system(self):
        logger.info("Initializing Property Analysis System")
        counties = ['Cook County', 'Dallas County', 'Los Angeles County']
        all_properties = []
        for county in counties:
            properties = self.data_extraction.extract_industrial_properties(county)
            all_properties.extend(properties)
        self.properties_database = all_properties
        self.comparable_discovery.load_properties(all_properties)
        logger.info(f"System initialized with {len(all_properties)} properties")

    def analyze_property_comparables(self, property_id: str = None, property_data: Dict = None) -> Dict:
        if property_id:
            target_property = next((p for p in self.properties_database if p.property_id == property_id), None)
            if not target_property:
                return {'error': f'Property with ID {property_id} not found'}
        elif property_data:
            target_property = PropertyData(**property_data)
        else:
            return {'error': 'Either property_id or property_data must be provided'}

        comparables = self.comparable_discovery.find_comparables(target_property)
        results = {
            'target_property': asdict(target_property),
            'comparables': [],
            'analysis_summary': {
                'total_comparables_found': len(comparables),
                'avg_similarity_score': sum(score for _, score in comparables) / len(comparables) if comparables else 0,
                'analysis_date': datetime.now().isoformat()
            }
        }
        for comp_property, similarity_score in comparables:
            comparable_data = asdict(comp_property)
            comparable_data['similarity_score'] = round(similarity_score, 3)
            comparable_data['confidence_level'] = 'High' if similarity_score > 0.8 else 'Medium' if similarity_score > 0.6 else 'Low'
            results['comparables'].append(comparable_data)
        return results

    def get_property_by_id(self, property_id: str) -> Optional[PropertyData]:
        return next((p for p in self.properties_database if p.property_id == property_id), None)

    def list_properties(self, county: str = None, limit: int = 10) -> List[Dict]:
        properties = self.properties_database
        if county:
            properties = [p for p in properties if p.county == county]
        return [
            {
                'property_id': p.property_id,
                'address': p.address,
                'city': p.city,
                'county': p.county,
                'building_area': p.building_area,
                'zoning': p.zoning,
                'assessed_value': p.assessed_value
            }
            for p in properties[:limit]
        ]

if __name__ == "__main__":
    system = PropertyAnalysisSystem()
    system.initialize_system()
    print("=== Example 1: Analyzing comparables for a specific property ===")
    properties = system.list_properties(limit=5)
    if properties:
        target_property_id = properties[0]['property_id']
        results = system.analyze_property_comparables(property_id=target_property_id)
        print(f"Target Property: {results['target_property']['address']}")
        print(f"Building Area: {results['target_property']['building_area']:,.0f} sq ft")
        print(f"Zoning: {results['target_property']['zoning']}")
        print(f"Found {len(results['comparables'])} comparables:")
        for i, comp in enumerate(results['comparables'], 1):
            print(f"  {i}. {comp['address']} (Score: {comp['similarity_score']}, {comp['confidence_level']} confidence)")
    print("\n=== Example 2: Analyzing comparables for custom property ===")
    custom_property = {
        'property_id': 'CUSTOM001',
        'address': '1234 Custom Industrial Way',
        'city': 'Chicago',
        'county': 'Cook County',
        'state': 'IL',
        'zip_code': '60601',
        'latitude': 41.8781,
        'longitude': -87.6298,
        'building_area': 50000,
        'lot_size': 100000,
        'year_built': 2000,
        'zoning': 'M1',
        'property_type': 'Industrial',
        'assessed_value': 2000000
    }
    results = system.analyze_property_comparables(property_data=custom_property)
    print(f"Custom Property: {results['target_property']['address']}")
    print(f"Building Area: {results['target_property']['building_area']:,.0f} sq ft")
    print(f"Found {len(results['comparables'])} comparables:")
    for i, comp in enumerate(results['comparables'], 1):
        print(f"  {i}. {comp['address']} (Score: {comp['similarity_score']}, {comp['confidence_level']} confidence)")
    print(f"\nAverage Similarity Score: {results['analysis_summary']['avg_similarity_score']:.3f}")
