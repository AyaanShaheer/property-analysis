// pages/index.js
import { useState, useEffect } from 'react';
import Head from 'next/head';

export default function Home() {
  const [properties, setProperties] = useState([]);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [comparables, setComparables] = useState(null);
  const [loading, setLoading] = useState(false);
  const [customProperty, setCustomProperty] = useState({
    address: '',
    city: '',
    county: 'Cook County',
    state: 'IL',
    zip_code: '',
    latitude: '',
    longitude: '',
    building_area: '',
    lot_size: '',
    year_built: '',
    zoning: 'M1',
    assessed_value: ''
  });
  const [showCustomForm, setShowCustomForm] = useState(false);

  const fetchProperties = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:5000/api/properties');
      const data = await res.json();
      if (data.success) {
        setProperties(data.data);
      } else {
        setProperties([]);
        console.error('API error:', data.error);
      }
    } catch (error) {
      setProperties([]);
      console.error('Error fetching properties:', error);
    } finally {
      setLoading(false);
    }
  };

  const analyzeComparables = async (propertyId = null, propertyData = null) => {
    setLoading(true);
    try {
      let body = {};
      if (propertyId) {
        body.property_id = propertyId;
      } else if (propertyData) {
        body.property_data = propertyData;
      }
      const res = await fetch('http://localhost:5000/api/analyze/comparables', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (data.success) {
        setComparables(data.data);
      } else {
        setComparables(null);
        alert('Analysis error: ' + data.error);
      }
    } catch (error) {
      setComparables(null);
      alert('Error analyzing comparables: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProperties();
  }, []);

  const handlePropertySelect = (property) => {
    setSelectedProperty(property);
    analyzeComparables(property.property_id);
  };

  const handleCustomPropertySubmit = (e) => {
    e.preventDefault();
    const propertyData = {
      ...customProperty,
      latitude: parseFloat(customProperty.latitude),
      longitude: parseFloat(customProperty.longitude),
      building_area: parseFloat(customProperty.building_area),
      lot_size: parseFloat(customProperty.lot_size),
      year_built: parseInt(customProperty.year_built),
      assessed_value: parseFloat(customProperty.assessed_value)
    };
    analyzeComparables(null, propertyData);
    setShowCustomForm(false);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const getConfidenceColor = (level) => {
    switch (level) {
      case 'High': return 'text-green-600 bg-green-100';
      case 'Medium': return 'text-yellow-600 bg-yellow-100';
      case 'Low': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Starboard AI - Industrial Property Analysis</title>
        <meta name="description" content="AI-powered industrial property comparable analysis" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Starboard AI Property Analysis
          </h1>
          <p className="text-gray-600 text-lg">
            AI-powered industrial property comparable analysis across Cook County, Dallas County, and Los Angeles County
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Property Selection Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Properties</h2>
                <button
                  onClick={() => setShowCustomForm(!showCustomForm)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  {showCustomForm ? 'Cancel' : 'Add Custom'}
                </button>
              </div>

              {showCustomForm && (
                <form onSubmit={handleCustomPropertySubmit} className="mb-6 p-4 border rounded-lg bg-gray-50">
                  <h3 className="text-lg font-medium mb-4">Custom Property</h3>
                  <div className="space-y-4">
                    <input
                      type="text"
                      placeholder="Address"
                      value={customProperty.address}
                      onChange={(e) => setCustomProperty({...customProperty, address: e.target.value})}
                      className="w-full p-2 border rounded-md"
                      required
                    />
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        placeholder="City"
                        value={customProperty.city}
                        onChange={(e) => setCustomProperty({...customProperty, city: e.target.value})}
                        className="p-2 border rounded-md"
                        required
                      />
                      <select
                        value={customProperty.county}
                        onChange={(e) => setCustomProperty({...customProperty, county: e.target.value})}
                        className="p-2 border rounded-md"
                      >
                        <option value="Cook County">Cook County</option>
                        <option value="Dallas County">Dallas County</option>
                        <option value="Los Angeles County">Los Angeles County</option>
                      </select>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="number"
                        placeholder="Latitude"
                        value={customProperty.latitude}
                        onChange={(e) => setCustomProperty({...customProperty, latitude: e.target.value})}
                        className="p-2 border rounded-md"
                        step="any"
                        required
                      />
                      <input
                        type="number"
                        placeholder="Longitude"
                        value={customProperty.longitude}
                        onChange={(e) => setCustomProperty({...customProperty, longitude: e.target.value})}
                        className="p-2 border rounded-md"
                        step="any"
                        required
                      />
                    </div>
                    <input
                      type="number"
                      placeholder="Building Area (sq ft)"
                      value={customProperty.building_area}
                      onChange={(e) => setCustomProperty({...customProperty, building_area: e.target.value})}
                      className="w-full p-2 border rounded-md"
                      required
                    />
                    <input
                      type="number"
                      placeholder="Lot Size (sq ft)"
                      value={customProperty.lot_size}
                      onChange={(e) => setCustomProperty({...customProperty, lot_size: e.target.value})}
                      className="w-full p-2 border rounded-md"
                      required
                    />
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="number"
                        placeholder="Year Built"
                        value={customProperty.year_built}
                        onChange={(e) => setCustomProperty({...customProperty, year_built: e.target.value})}
                        className="p-2 border rounded-md"
                        required
                      />
                      <select
                        value={customProperty.zoning}
                        onChange={(e) => setCustomProperty({...customProperty, zoning: e.target.value})}
                        className="p-2 border rounded-md"
                      >
                        <option value="M1">M1</option>
                        <option value="M2">M2</option>
                        <option value="I-1">I-1</option>
                        <option value="I-2">I-2</option>
                        <option value="IM">IM</option>
                        <option value="IL">IL</option>
                      </select>
                    </div>
                    <input
                      type="number"
                      placeholder="Assessed Value"
                      value={customProperty.assessed_value}
                      onChange={(e) => setCustomProperty({...customProperty, assessed_value: e.target.value})}
                      className="w-full p-2 border rounded-md"
                      required
                    />
                    <button
                      type="submit"
                      className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                    >
                      Analyze Comparables
                    </button>
                  </div>
                </form>
              )}

              {loading && (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="text-gray-600 mt-2">Loading properties...</p>
                </div>
              )}

              <div className="space-y-3">
                {properties.map((property) => (
                  <div
                    key={property.property_id}
                    onClick={() => handlePropertySelect(property)}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedProperty?.property_id === property.property_id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <h3 className="font-medium text-gray-900">{property.address}</h3>
                    <p className="text-sm text-gray-600">{property.city}, {property.county}</p>
                    <div className="mt-2 flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-700">
                        {formatNumber(property.building_area)} sq ft
                      </span>
                      <span className="text-sm px-2 py-1 bg-gray-100 rounded">
                        {property.zoning}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {formatCurrency(property.assessed_value)}
                    </p>
                    {property.last_sale_amount && (
                      <p className="text-sm text-gray-600 mt-1">
                        Last Sale: {formatCurrency(property.last_sale_amount)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Analysis Results Panel */}
          <div className="lg:col-span-2">
            {comparables ? (
              <div className="space-y-6">
                {/* Target Property Info */}
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Target Property</h2>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Address</p>
                      <p className="font-medium">{comparables.target_property.address}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Building Area</p>
                      <p className="font-medium">{formatNumber(comparables.target_property.building_area)} sq ft</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Zoning</p>
                      <p className="font-medium">{comparables.target_property.zoning}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Assessed Value</p>
                      <p className="font-medium">{formatCurrency(comparables.target_property.assessed_value)}</p>
                    </div>
                    {comparables.target_property.last_sale_amount && (
                      <div>
                        <p className="text-sm text-gray-600">Last Sale</p>
                        <p className="font-medium">{formatCurrency(comparables.target_property.last_sale_amount)}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Analysis Summary */}
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Analysis Summary</h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">
                        {comparables.analysis_summary.total_comparables_found}
                      </p>
                      <p className="text-sm text-gray-600">Comparables Found</p>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <p className="text-2xl font-bold text-green-600">
                        {(comparables.analysis_summary.avg_similarity_score * 100).toFixed(1)}%
                      </p>
                      <p className="text-sm text-gray-600">Avg Similarity Score</p>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <p className="text-2xl font-bold text-purple-600">
                        {comparables.comparables.filter(c => c.confidence_level === 'High').length}
                      </p>
                      <p className="text-sm text-gray-600">High Confidence</p>
                    </div>
                  </div>
                </div>

                {/* Comparables List */}
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Comparable Properties</h2>
                  <div className="space-y-4">
                    {comparables.comparables.map((comp, index) => (
                      <div key={comp.property_id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h3 className="font-medium text-gray-900">{comp.address}</h3>
                            <p className="text-sm text-gray-600">{comp.city}, {comp.county}</p>
                          </div>
                          <div className="text-right">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(comp.confidence_level)}`}>
                              {comp.confidence_level} Confidence
                            </span>
                            <p className="text-sm text-gray-600 mt-1">
                              Score: {(comp.similarity_score * 100).toFixed(1)}%
                            </p>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                          <div>
                            <p className="text-gray-600">Building Area</p>
                            <p className="font-medium">{formatNumber(comp.building_area)} sq ft</p>
                          </div>
                          <div>
                            <p className="text-gray-600">Zoning</p>
                            <p className="font-medium">{comp.zoning}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">Assessed Value</p>
                            <p className="font-medium">{formatCurrency(comp.assessed_value)}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">$/sq ft</p>
                            <p className="font-medium">${(comp.assessed_value / comp.building_area).toFixed(2)}</p>
                          </div>
                          {comp.last_sale_amount && (
                            <div>
                              <p className="text-gray-600">Last Sale</p>
                              <p className="font-medium">{formatCurrency(comp.last_sale_amount)}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-md p-6 text-center">
                <div className="text-gray-400 mb-4">
                  <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Analysis Selected</h3>
                <p className="text-gray-600">
                  Select a property from the left panel or add a custom property to begin comparable analysis.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}