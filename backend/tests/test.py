import pytest
from analysis import PropertyAnalysisSystem, PropertyData

@pytest.fixture
def analysis_system():
    system = PropertyAnalysisSystem()
    system.initialize_system()
    return system

def test_property_analysis(analysis_system):
    # Test property listing
    properties = analysis_system.list_properties(limit=5)
    assert len(properties) > 0
    assert all(isinstance(p['property_id'], str) for p in properties)
    
    # Test comparable analysis
    test_property = {
        'property_id': 'TEST001',
        'address': '123 Test St',
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
    
    results = analysis_system.analyze_property_comparables(property_data=test_property)
    assert 'target_property' in results
    assert 'comparables' in results
    assert len(results['comparables']) > 0