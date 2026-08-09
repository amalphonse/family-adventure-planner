"""
Family Adventure Planner - API Test Script

Simple test script to verify all API endpoints work correctly.

Usage:
    # Start the Flask app in another terminal:
    python app.py
    
    # Then run tests:
    python test_api.py
"""

import requests
import json
from typing import Dict, List

BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test the health check endpoint."""
    print("\n" + "="*60)
    print("Test 1: Health Check")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✓ Health check passed")


def test_list_destinations():
    """Test listing all destinations."""
    print("\n" + "="*60)
    print("Test 2: List Destinations")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/destinations")
    print(f"Status: {response.status_code}")
    
    destinations = response.json()
    print(f"Found {len(destinations)} destinations:")
    for dest in destinations:
        print(f"  - {dest['name']} ({dest['country']})")
    
    assert response.status_code == 200
    assert len(destinations) > 0
    print("✓ List destinations passed")
    
    return destinations


def test_get_destination(destination_id: int):
    """Test getting a single destination."""
    print("\n" + "="*60)
    print(f"Test 3: Get Destination {destination_id}")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/destinations/{destination_id}")
    print(f"Status: {response.status_code}")
    
    destination = response.json()
    print(f"Destination: {destination['name']}")
    print(f"Location: ({destination['latitude']}, {destination['longitude']})")
    print(f"Description: {destination['description'][:100]}...")
    
    assert response.status_code == 200
    assert destination['destination_id'] == destination_id
    print("✓ Get destination passed")


def test_get_destination_activities(destination_id: int):
    """Test getting activities for a destination."""
    print("\n" + "="*60)
    print(f"Test 4: Get Activities for Destination {destination_id}")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/destinations/{destination_id}/activities")
    print(f"Status: {response.status_code}")
    
    activities = response.json()
    print(f"Found {len(activities)} activities:")
    for activity in activities:
        print(f"  - {activity['activity_name']} ({activity['activity_type']})")
        print(f"    Ages: {activity['min_age']}-{activity['max_age'] or 'all'}")
        print(f"    Indoor: {activity['indoor']}, Duration: {activity['duration_minutes']} min")
    
    assert response.status_code == 200
    print("✓ Get destination activities passed")


def test_search_activities_basic():
    """Test basic semantic search over activities."""
    print("\n" + "="*60)
    print("Test 5: Search Activities (Basic)")
    print("="*60)
    
    params = {
        "query": "indoor museum for toddlers",
        "limit": 5
    }
    
    response = requests.get(f"{BASE_URL}/activities/search", params=params)
    print(f"Status: {response.status_code}")
    
    data = response.json()
    print(f"Query: {data['query']}")
    print(f"Found {data['count']} results:")
    
    for result in data['results']:
        print(f"\n  {result['activity_name']}")
        print(f"    Destination: {result['destination_name']}")
        print(f"    Type: {result['activity_type']}")
        print(f"    Indoor: {result['indoor']}, Ages: {result['min_age']}-{result['max_age'] or 'all'}")
        print(f"    Similarity: {result['similarity_score']:.3f}")
    
    assert response.status_code == 200
    assert data['count'] > 0
    print("\n✓ Search activities (basic) passed")


def test_search_activities_with_filters():
    """Test semantic search with filters."""
    print("\n" + "="*60)
    print("Test 6: Search Activities (With Filters)")
    print("="*60)
    
    params = {
        "query": "outdoor playground",
        "min_age": 2,
        "max_age": 10,
        "indoor": "false",
        "limit": 3
    }
    
    response = requests.get(f"{BASE_URL}/activities/search", params=params)
    print(f"Status: {response.status_code}")
    
    data = response.json()
    print(f"Query: {data['query']}")
    print(f"Filters: {json.dumps(data['filters'], indent=2)}")
    print(f"Found {data['count']} results:")
    
    for result in data['results']:
        print(f"\n  {result['activity_name']}")
        print(f"    Destination: {result['destination_name']}")
        print(f"    Indoor: {result['indoor']}, Ages: {result['min_age']}-{result['max_age'] or 'all'}")
        print(f"    Similarity: {result['similarity_score']:.3f}")
    
    assert response.status_code == 200
    print("\n✓ Search activities (with filters) passed")


def run_all_tests():
    """Run all API tests."""
    print("\n" + "#"*60)
    print("# Family Adventure Planner - API Test Suite")
    print("#"*60)
    
    try:
        # Test 1: Health check
        test_health_check()
        
        # Test 2: List destinations
        destinations = test_list_destinations()
        
        if destinations:
            # Test 3: Get single destination
            test_get_destination(destinations[0]['destination_id'])
            
            # Test 4: Get activities for destination
            test_get_destination_activities(destinations[0]['destination_id'])
        
        # Test 5: Search activities (basic)
        test_search_activities_basic()
        
        # Test 6: Search activities (with filters)
        test_search_activities_with_filters()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
    
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection error: Is the Flask app running on http://localhost:8000?")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())