from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
from datetime import datetime
import os
import sys

# Import our property analysis system
# (The PropertyAnalysisSystem code from the previous artifact would be in a separate file)
from analysis import PropertyAnalysisSystem, PropertyData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global system instance
property_system = None

def initialize_system():
    """Initialize the property analysis system"""
    global property_system
    if property_system is None:
        logger.info("Initializing Property Analysis System...")
        property_system = PropertyAnalysisSystem()
        property_system.initialize_system()
        logger.info("System initialized successfully")

# Initialize system once at startup
initialize_system()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Starboard Property Analysis API'
    })

@app.route('/api/properties', methods=['GET'])
def get_properties():
    """Get list of available properties"""
    try:
        county = request.args.get('county')
        limit = int(request.args.get('limit', 20))
        
        if property_system is None:
            initialize_system()
        
        properties = property_system.list_properties(county=county, limit=limit)
        
        return jsonify({
            'success': True,
            'data': properties,
            'count': len(properties)
        })
        
    except Exception as e:
        logger.error(f"Error fetching properties: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/properties/<property_id>', methods=['GET'])
def get_property(property_id):
    """Get specific property by ID"""
    try:
        if property_system is None:
            initialize_system()
        
        property_data = property_system.get_property_by_id(property_id)
        
        if property_data is None:
            return jsonify({
                'success': False,
                'error': 'Property not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'property_id': property_data.property_id,
                'address': property_data.address,
                'city': property_data.city,
                'county': property_data.county,
                'state': property_data.state,
                'zip_code': property_data.zip_code,
                'latitude': property_data.latitude,
                'longitude': property_data.longitude,
                'building_area': property_data.building_area,
                'lot_size': property_data.lot_size,
                'year_built': property_data.year_built,
                'zoning': property_data.zoning,
                'property_type': property_data.property_type,
                'assessed_value': property_data.assessed_value,
                'sale_price': property_data.sale_price,
                'sale_date': property_data.sale_date
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching property {property_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analyze/comparables', methods=['POST'])
def analyze_comparables():
    """Analyze comparables for a property"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        if property_system is None:
            initialize_system()
        
        # Check if it's analysis by property ID or custom property
        if 'property_id' in data:
            results = property_system.analyze_property_comparables(
                property_id=data['property_id']
            )
        elif 'property_data' in data:
            # Validate required fields for custom property
            required_fields = ['address', 'city', 'county', 'state', 'latitude', 
                             'longitude', 'building_area', 'zoning', 'assessed_value']
            
            property_data = data['property_data']
            missing_fields = [field for field in required_fields if field not in property_data]
            
            if missing_fields:
                return jsonify({
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }), 400
            
            # Add default values for optional fields
            if 'property_id' not in property_data:
                property_data['property_id'] = f"CUSTOM_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            if 'zip_code' not in property_data:
                property_data['zip_code'] = '00000'
            if 'lot_size' not in property_data:
                property_data['lot_size'] = property_data['building_area'] * 2
            if 'year_built' not in property_data:
                property_data['year_built'] = 1980
            if 'property_type' not in property_data:
                property_data['property_type'] = 'Industrial'
            
            results = property_system.analyze_property_comparables(
                property_data=property_data
            )
        else:
            return jsonify({
                'success': False,
                'error': 'Either property_id or property_data must be provided'
            }), 400
        
        if 'error' in results:
            return jsonify({
                'success': False,
                'error': results['error']
            }), 404
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Error analyzing comparables: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/counties', methods=['GET'])
def get_counties():
    """Get list of supported counties"""
    counties = [
        {
            'name': 'Cook County',
            'state': 'Illinois',
            'code': 'IL',
            'description': 'Largest industrial market nationally (Chicago area)'
        },
        {
            'name': 'Dallas County',
            'state': 'Texas',
            'code': 'TX',
            'description': 'Fastest growing industrial market'
        },
        {
            'name': 'Los Angeles County',
            'state': 'California',
            'code': 'CA',
            'description': 'Largest industrial inventory'
        }
    ]
    
    return jsonify({
        'success': True,
        'data': counties
    })

@app.route('/api/zoning-codes', methods=['GET'])
def get_zoning_codes():
    """Get list of supported industrial zoning codes"""
    zoning_codes = [
        {
            'code': 'M1',
            'description': 'Light Manufacturing'
        },
        {
            'code': 'M2',
            'description': 'Heavy Manufacturing'
        },
        {
            'code': 'I-1',
            'description': 'Light Industrial'
        },
        {
            'code': 'I-2',
            'description': 'Heavy Industrial'
        },
        {
            'code': 'IM',
            'description': 'Industrial Mixed'
        },
        {
            'code': 'IL',
            'description': 'Industrial Light'
        }
    ]
    
    return jsonify({
        'success': True,
        'data': zoning_codes
    })

@app.route('/api/stats', methods=['GET'])
def get_system_stats():
    """Get system statistics"""
    try:
        if property_system is None:
            initialize_system()
        
        total_properties = len(property_system.properties_database)
        
        # Count by county
        county_counts = {}
        for prop in property_system.properties_database:
            county = prop.county
            county_counts[county] = county_counts.get(county, 0) + 1
        
        # Count by zoning
        zoning_counts = {}
        for prop in property_system.properties_database:
            zoning = prop.zoning
            zoning_counts[zoning] = zoning_counts.get(zoning, 0) + 1
        
        # Calculate average values
        building_areas = [prop.building_area for prop in property_system.properties_database]
        assessed_values = [prop.assessed_value for prop in property_system.properties_database]
        
        stats = {
            'total_properties': total_properties,
            'county_distribution': county_counts,
            'zoning_distribution': zoning_counts,
            'averages': {
                'building_area': sum(building_areas) / len(building_areas) if building_areas else 0,
                'assessed_value': sum(assessed_values) / len(assessed_values) if assessed_values else 0
            },
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # For development
    app.run(debug=True, host='0.0.0.0', port=5000)