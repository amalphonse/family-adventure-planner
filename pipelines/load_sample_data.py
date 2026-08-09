"""
Family Adventure Planner - Sample Data Loader

Inserts sample San Francisco destinations and activities into Lakebase
with placeholder embeddings (random vectors) for testing.

This allows you to test the Flask API and semantic search without
running the full ML pipeline.

Usage:
    python load_sample_data.py
"""

import numpy as np
from datetime import datetime
from databricks.sdk import WorkspaceClient

# Lakebase configuration
LAKEBASE_PROJECT = "family-adventure-planner"
LAKEBASE_BRANCH = "production"
LAKEBASE_DATABASE = "databricks_postgres"
LAKEBASE_HOST = "ep-calm-river-d891evds.database.us-east-2.cloud.databricks.com"

# Sample destinations data
SAMPLE_DESTINATIONS = [
    {
        "name": "Golden Gate Park",
        "latitude": 37.7694,
        "longitude": -122.4862,
        "description": "Golden Gate Park is an urban park between the Richmond and Sunset districts on the West Side of San Francisco. It is the largest urban park in the city, containing 1,017 acres with lakes, gardens, museums, and recreational facilities.",
        "country": "United States"
    },
    {
        "name": "Exploratorium",
        "latitude": 37.8016,
        "longitude": -122.3977,
        "description": "The Exploratorium is a museum of science, technology, and arts in San Francisco. It features hundreds of interactive exhibits that encourage hands-on exploration. Very popular with families and children of all ages.",
        "country": "United States"
    },
    {
        "name": "California Academy of Sciences",
        "latitude": 37.7699,
        "longitude": -122.4661,
        "description": "The California Academy of Sciences is a natural history museum in Golden Gate Park. It features an aquarium, planetarium, rainforest, and natural history exhibits. Kid-friendly with interactive displays for toddlers and young children.",
        "country": "United States"
    },
    {
        "name": "Pier 39",
        "latitude": 37.8087,
        "longitude": -122.4098,
        "description": "Pier 39 is a shopping center and popular tourist attraction on the waterfront in the Fisherman's Wharf neighborhood. Features sea lions, shops, restaurants, and street performers. Family-friendly outdoor destination.",
        "country": "United States"
    },
    {
        "name": "San Francisco Zoo",
        "latitude": 37.7331,
        "longitude": -122.5033,
        "description": "The San Francisco Zoo is a 100-acre zoo in the southwestern corner of the city. Home to over 2,000 animals and a playground area. Great for families with young children aged 2-10.",
        "country": "United States"
    }
]

# Sample activities for each destination
SAMPLE_ACTIVITIES = {
    "Golden Gate Park": [
        {
            "activity_name": "Koret Children's Quarter Playground",
            "activity_type": "playground",
            "description": "Large playground in Golden Gate Park designed for children ages 2-12. Features climbing structures, slides, swings, and a sand area perfect for toddlers.",
            "min_age": 2,
            "max_age": 12,
            "indoor": False,
            "weather_dependent": True,
            "duration_minutes": 90
        },
        {
            "activity_name": "Japanese Tea Garden",
            "activity_type": "garden",
            "description": "Beautiful Japanese garden with koi ponds, stone bridges, and pagodas. Stroller-friendly paths make it accessible for families with toddlers.",
            "min_age": 0,
            "max_age": None,
            "indoor": False,
            "weather_dependent": True,
            "duration_minutes": 60
        }
    ],
    "Exploratorium": [
        {
            "activity_name": "Exploratorium Indoor Exhibits",
            "activity_type": "museum",
            "description": "Interactive science exhibits perfect for curious toddlers and preschoolers. Touch-friendly displays explore light, sound, and motion. Climate-controlled indoor space.",
            "min_age": 2,
            "max_age": None,
            "indoor": True,
            "weather_dependent": False,
            "duration_minutes": 120
        }
    ],
    "California Academy of Sciences": [
        {
            "activity_name": "Steinhart Aquarium",
            "activity_type": "aquarium",
            "description": "Indoor aquarium featuring over 40,000 live animals. Toddler-friendly with low viewing windows and colorful displays. Climate-controlled.",
            "min_age": 0,
            "max_age": None,
            "indoor": True,
            "weather_dependent": False,
            "duration_minutes": 90
        },
        {
            "activity_name": "Living Roof",
            "activity_type": "outdoor",
            "description": "Outdoor rooftop garden with native California plants. Short walk suitable for toddlers. Weather permitting.",
            "min_age": 2,
            "max_age": None,
            "indoor": False,
            "weather_dependent": True,
            "duration_minutes": 30
        }
    ],
    "Pier 39": [
        {
            "activity_name": "Sea Lion Viewing",
            "activity_type": "wildlife",
            "description": "Watch wild sea lions lounging on the docks. Free outdoor activity perfect for toddlers. Can be windy and cold near the water.",
            "min_age": 0,
            "max_age": None,
            "indoor": False,
            "weather_dependent": True,
            "duration_minutes": 30
        },
        {
            "activity_name": "Aquarium of the Bay",
            "activity_type": "aquarium",
            "description": "Indoor aquarium with walkthrough tunnels featuring Bay Area marine life. Toddler-friendly with stroller access. Climate-controlled.",
            "min_age": 2,
            "max_age": None,
            "indoor": True,
            "weather_dependent": False,
            "duration_minutes": 60
        }
    ],
    "San Francisco Zoo": [
        {
            "activity_name": "Zoo Main Exhibits",
            "activity_type": "zoo",
            "description": "Outdoor zoo with African savanna, penguin island, and primate center. Stroller-friendly paths. Great for families with young children.",
            "min_age": 2,
            "max_age": 12,
            "indoor": False,
            "weather_dependent": True,
            "duration_minutes": 180
        },
        {
            "activity_name": "Little Puffer Playground",
            "activity_type": "playground",
            "description": "Toddler-sized playground within the zoo grounds. Safe for ages 2-5 with soft surfaces and age-appropriate equipment.",
            "min_age": 2,
            "max_age": 5,
            "indoor": False,
            "weather_dependent": True,
            "duration_minutes": 45
        }
    ]
}


def generate_placeholder_embedding(seed: int = None) -> list:
    """
    Generate a placeholder 768-dimensional embedding vector.
    Uses numpy random with optional seed for reproducibility.
    
    In production, this would be replaced by sentence-transformers embeddings.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Generate random normalized vector (unit length)
    vector = np.random.randn(768)
    vector = vector / np.linalg.norm(vector)
    
    return vector.tolist()


def insert_sample_data():
    """
    Insert sample destinations and activities into Lakebase.
    """
    from databricks.sdk.service import postgres as postgres_service
    
    # Import executeLakebasePostgresSql function
    # Note: This is a placeholder - in actual execution, you'd use the tool directly
    
    print("="*80)
    print("Family Adventure Planner - Sample Data Loader")
    print("="*80)
    print(f"Destinations to insert: {len(SAMPLE_DESTINATIONS)}")
    print(f"Activities to insert: {sum(len(acts) for acts in SAMPLE_ACTIVITIES.values())}")
    print()
    
    # This script generates the SQL statements
    # You'll run these using the executeLakebasePostgresSql tool
    
    print("\n" + "="*80)
    print("GENERATED SQL STATEMENTS")
    print("Copy these and run via executeLakebasePostgresSql tool")
    print("="*80)
    
    destination_ids = {}
    dest_id_counter = 1
    
    # Generate INSERT statements for destinations
    print("\n-- INSERT DESTINATIONS\n")
    for i, dest in enumerate(SAMPLE_DESTINATIONS, 1):
        embedding = generate_placeholder_embedding(seed=i)
        embedding_str = str(embedding)
        
        sql = f"""
INSERT INTO destinations (name, latitude, longitude, description, description_embedding, country, created_at)
VALUES (
    '{dest['name']}',
    {dest['latitude']},
    {dest['longitude']},
    '{dest['description'].replace("'", "''"))}',
    '{embedding_str}'::vector,
    '{dest['country']}',
    CURRENT_TIMESTAMP
) RETURNING destination_id;
"""
        print(sql)
        destination_ids[dest['name']] = dest_id_counter
        dest_id_counter += 1
    
    # Generate INSERT statements for activities
    print("\n-- INSERT ACTIVITIES\n")
    activity_counter = 1
    for dest_name, activities in SAMPLE_ACTIVITIES.items():
        dest_id = destination_ids.get(dest_name, 1)  # Default to 1 if not found
        
        for activity in activities:
            embedding = generate_placeholder_embedding(seed=100 + activity_counter)
            embedding_str = str(embedding)
            
            max_age_val = activity['max_age'] if activity['max_age'] is not None else 'NULL'
            
            sql = f"""
INSERT INTO activities (
    destination_id, activity_name, activity_type, description, content_embedding,
    min_age, max_age, indoor, weather_dependent, duration_minutes, created_at
)
VALUES (
    {dest_id},
    '{activity['activity_name'].replace("'", "''")}',
    '{activity['activity_type']}',
    '{activity['description'].replace("'", "''")}',
    '{embedding_str}'::vector,
    {activity['min_age']},
    {max_age_val},
    {str(activity['indoor']).lower()},
    {str(activity['weather_dependent']).lower()},
    {activity['duration_minutes']},
    CURRENT_TIMESTAMP
);
"""
            print(sql)
            activity_counter += 1
    
    print("\n" + "="*80)
    print("SQL statements generated successfully!")
    print("="*80)
    print("\nNext: Run these INSERT statements using executeLakebasePostgresSql")


if __name__ == "__main__":
    insert_sample_data()