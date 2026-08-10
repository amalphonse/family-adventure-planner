"""
Family Adventure Planner - Comprehensive Test Suite
Tests both the main app and the Weather MCP Server
"""

import requests
import json
from datetime import datetime

# App URLs
MAIN_APP_URL = "https://family-adventure-planner-7474644727314917.aws.databricksapps.com"
WEATHER_MCP_URL = "https://weather-mcp-server-7474644727314917.aws.databricksapps.com"

def test_main_app():
    """Test the Family Adventure Planner app endpoints"""
    print("=" * 60)
    print("TESTING FAMILY ADVENTURE PLANNER APP")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{MAIN_APP_URL}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: List destinations
    print("\n2. Testing destinations endpoint...")
    try:
        response = requests.get(f"{MAIN_APP_URL}/destinations", timeout=10)
        if response.status_code == 200:
            destinations = response.json()
            print(f"   ✅ Destinations loaded: {len(destinations)} found")
            if destinations:
                print(f"   Sample: {destinations[0]['name']} ({destinations[0]['country']})")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Get single destination
    print("\n3. Testing single destination endpoint...")
    try:
        response = requests.get(f"{MAIN_APP_URL}/destinations/1", timeout=10)
        if response.status_code == 200:
            destination = response.json()
            print(f"   ✅ Destination retrieved: {destination.get('name', 'N/A')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Weather endpoint
    print("\n4. Testing weather endpoint...")
    try:
        response = requests.get(f"{MAIN_APP_URL}/destinations/1/weather?days=3", timeout=15)
        if response.status_code == 200:
            weather = response.json()
            print(f"   ✅ Weather data retrieved")
            print(f"   Location: {weather.get('location', 'N/A')}")
            if 'forecast' in weather:
                print(f"   Forecast days: {len(weather['forecast'])}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Activities search
    print("\n5. Testing activities search...")
    try:
        response = requests.get(
            f"{MAIN_APP_URL}/activities/search?query=museum&limit=5",
            timeout=15
        )
        if response.status_code == 200:
            activities = response.json()
            print(f"   ✅ Search returned {len(activities)} activities")
            if activities:
                print(f"   Top result: {activities[0]['activity_name']}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_weather_mcp():
    """Test the Weather MCP Server (if deployed)"""
    print("\n" + "=" * 60)
    print("TESTING WEATHER MCP SERVER")
    print("=" * 60)
    print("\nNote: MCP server needs to be deployed first!")
    print("Deploy from: /family-adventure-planner/mcp_server/")
    print("\nSkipping automated tests - MCP requires Agent Bricks integration")
    print("See TEST_EXAMPLES.md for manual test cases")


def test_database_connection():
    """Test database connection using psycopg2"""
    print("\n" + "=" * 60)
    print("TESTING DATABASE CONNECTION")
    print("=" * 60)
    
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host="ep-calm-river-d891evds.database.us-east-2.cloud.databricks.com",
            port=5432,
            dbname="databricks_postgres",
            user="user",
            password="npg_ZlOMFTehK8J3",
            sslmode="require"
        )
        
        print("\n✅ Database connection successful")
        
        # Test query
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM destinations")
            count = cur.fetchone()[0]
            print(f"✅ Query successful: {count} destinations in database")
        
        conn.close()
        
    except ImportError:
        print("\n⚠️  psycopg2 not installed - install with: pip install psycopg2-binary")
    except Exception as e:
        print(f"\n❌ Database connection failed: {e}")


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("🧪 " + "=" * 58 + " 🧪")
    print("   FAMILY ADVENTURE PLANNER - TEST SUITE")
    print("   Date: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🧪 " + "=" * 58 + " 🧪")
    
    test_main_app()
    test_database_connection()
    test_weather_mcp()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)
    print("\n📋 Summary:")
    print("   - Main app endpoints tested")
    print("   - Database connection tested")
    print("   - Weather MCP server info provided")
    print("\n✅ Tests completed!")
    print("\n📖 For Weather MCP testing, see:")
    print("   - mcp_server/TEST_EXAMPLES.md")
    print("   - mcp_server/DEPLOYMENT_GUIDE.md")
    

if __name__ == "__main__":
    run_all_tests()
