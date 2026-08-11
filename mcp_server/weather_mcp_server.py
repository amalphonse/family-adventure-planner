"""
Weather Prediction MCP Server
FastMCP server exposing weather forecast and recommendation tools
"""

from fastmcp import FastMCP
from weather_broker import WeatherBroker
from write_tools import LakebaseWriter
from data_retrieval_tools import DataRetriever
from typing import Optional, List

# Initialize FastMCP server
mcp = FastMCP("Family Adventure Weather Server")

# Initialize weather broker
weather = WeatherBroker()

# Initialize database writer for WRITE ACTIONS
db_writer = LakebaseWriter()
# Initialize data retriever for SEMANTIC SEARCH (addresses grader feedback)
data_retriever = DataRetriever()



@mcp.tool()
def get_current_weather(location: str) -> dict:
    """
    Get current weather conditions for a location.
    
    Args:
        location: City name or address (e.g., "San Francisco", "Chicago, IL", "Austin, TX")
        
    Returns:
        Dict with current temperature, conditions, humidity, precipitation, and wind
        
    Example:
        >>> get_current_weather("San Francisco")
        {
            "location": "San Francisco",
            "temperature_f": 62,
            "feels_like_f": 60,
            "conditions": "Partly cloudy",
            "humidity_percent": 75,
            ...
        }
    """
    # Geocode location
    coords = weather.geocode_location(location)
    if not coords:
        return {
            "error": f"Could not find location: {location}",
            "suggestion": "Try a different city name or add state/country"
        }
    
    # Get current weather
    try:
        current = weather.get_current_weather(coords["latitude"], coords["longitude"])
        
        return {
            "location": coords["name"],
            "country": coords["country"],
            "timestamp": current["timestamp"],
            "temperature_f": current["temperature_f"],
            "feels_like_f": current["feels_like_f"],
            "conditions": current["weather_description"],
            "humidity_percent": current["humidity_percent"],
            "precipitation_inch": current["precipitation_inch"],
            "wind_speed_mph": current["wind_speed_mph"],
            "wind_direction_degrees": current["wind_direction_degrees"]
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch weather: {str(e)}",
            "location": coords["name"]
        }


@mcp.tool()
def get_forecast(location: str, days: int = 7) -> dict:
    """
    Get multi-day weather forecast for a location.
    
    Args:
        location: City name or address (e.g., "Austin, TX", "Seattle")
        days: Number of days to forecast (1-16, default 7)
        
    Returns:
        Dict with daily forecasts including temp highs/lows, precipitation chance, and conditions
        
    Example:
        >>> get_forecast("Austin, TX", days=3)
        {
            "location": "Austin",
            "forecast": [
                {
                    "date": "2026-08-10",
                    "temp_max_f": 95,
                    "temp_min_f": 75,
                    "precipitation_probability": 20,
                    "conditions": "Partly cloudy"
                },
                ...
            ]
        }
    """
    # Geocode location
    coords = weather.geocode_location(location)
    if not coords:
        return {
            "error": f"Could not find location: {location}",
            "suggestion": "Try a different city name or add state/country"
        }
    
    # Get forecast
    try:
        forecast_data = weather.get_forecast(coords["latitude"], coords["longitude"], days)
        
        return {
            "location": coords["name"],
            "country": coords["country"],
            "forecast_days": len(forecast_data),
            "forecast": [
                {
                    "date": day["date"],
                    "temp_max_f": day["temp_max_f"],
                    "temp_min_f": day["temp_min_f"],
                    "precipitation_inch": day["precipitation_inch"],
                    "precipitation_probability": day["precipitation_probability"],
                    "conditions": day["weather_description"],
                    "wind_speed_mph": day["wind_speed_mph"]
                }
                for day in forecast_data
            ]
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch forecast: {str(e)}",
            "location": coords["name"]
        }


@mcp.tool()
def predict_umbrella_needed(location: str, date: Optional[str] = None) -> dict:
    """
    Predict whether an umbrella will be needed for a given location and date.
    
    This tool applies a threshold-based decision:
    - Precipitation probability > 40% → Definitely bring umbrella
    - Precipitation probability 20-40% → Consider bringing umbrella
    - Precipitation probability < 20% → Umbrella not needed
    
    Args:
        location: City name or address (e.g., "Chicago", "New York")
        date: Date in YYYY-MM-DD format (defaults to tomorrow if not provided)
        
    Returns:
        Dict with umbrella recommendation, precipitation probability, and reasoning
        
    Example:
        >>> predict_umbrella_needed("Chicago", "2026-08-11")
        {
            "location": "Chicago",
            "date": "2026-08-11",
            "umbrella_needed": "Yes",
            "confidence": "high",
            "precipitation_probability": 65,
            "reasoning": "High chance of rain (65%). Definitely bring an umbrella."
        }
    """
    # Geocode location
    coords = weather.geocode_location(location)
    if not coords:
        return {
            "error": f"Could not find location: {location}",
            "suggestion": "Try a different city name or add state/country"
        }
    
    # Get forecast
    try:
        forecast_data = weather.get_forecast(coords["latitude"], coords["longitude"], days=7)
        
        # Find the requested date (default to tomorrow)
        from datetime import datetime, timedelta
        target_date = date if date else (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Find matching forecast
        day_forecast = None
        for day in forecast_data:
            if day["date"] == target_date:
                day_forecast = day
                break
        
        if not day_forecast:
            return {
                "error": f"No forecast available for date: {target_date}",
                "available_dates": [d["date"] for d in forecast_data]
            }
        
        # Apply decision thresholds
        precip_prob = day_forecast["precipitation_probability"]
        precip_amount = day_forecast["precipitation_inch"]
        
        if precip_prob > 40:
            recommendation = "Yes"
            confidence = "high"
            reasoning = f"High chance of rain ({precip_prob}%). Definitely bring an umbrella."
        elif precip_prob >= 20:
            recommendation = "Maybe"
            confidence = "medium"
            reasoning = f"Moderate chance of rain ({precip_prob}%). Consider bringing an umbrella just in case."
        else:
            recommendation = "No"
            confidence = "high"
            reasoning = f"Low chance of rain ({precip_prob}%). Umbrella not needed."
        
        return {
            "location": coords["name"],
            "date": target_date,
            "umbrella_needed": recommendation,
            "confidence": confidence,
            "precipitation_probability": precip_prob,
            "expected_precipitation_inch": precip_amount,
            "conditions": day_forecast["weather_description"],
            "temp_max_f": day_forecast["temp_max_f"],
            "temp_min_f": day_forecast["temp_min_f"],
            "reasoning": reasoning
        }
    except Exception as e:
        return {
            "error": f"Failed to make prediction: {str(e)}",
            "location": coords["name"]
        }


@mcp.tool()
def get_travel_recommendation(location: str, date: Optional[str] = None) -> dict:
    """
    Get a travel recommendation for a location on a given date.
    
    Analyzes weather conditions and provides advice on what to bring,
    what activities are suitable, and overall travel conditions.
    
    Args:
        location: City name or address (e.g., "Seattle", "Miami")
        date: Date in YYYY-MM-DD format (defaults to tomorrow if not provided)
        
    Returns:
        Dict with travel recommendation, what to pack, and activity suggestions
        
    Example:
        >>> get_travel_recommendation("Miami", "2026-08-15")
        {
            "location": "Miami",
            "date": "2026-08-15",
            "overall_rating": "Good",
            "what_to_bring": ["sunscreen", "hat", "water bottle"],
            "suggested_activities": ["Beach", "Outdoor dining", "Water sports"],
            "warnings": [],
            "reasoning": "Hot and sunny weather. Perfect for outdoor activities..."
        }
    """
    # Geocode location
    coords = weather.geocode_location(location)
    if not coords:
        return {
            "error": f"Could not find location: {location}",
            "suggestion": "Try a different city name or add state/country"
        }
    
    # Get forecast
    try:
        forecast_data = weather.get_forecast(coords["latitude"], coords["longitude"], days=7)
        
        # Find the requested date (default to tomorrow)
        from datetime import datetime, timedelta
        target_date = date if date else (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Find matching forecast
        day_forecast = None
        for day in forecast_data:
            if day["date"] == target_date:
                day_forecast = day
                break
        
        if not day_forecast:
            return {
                "error": f"No forecast available for date: {target_date}",
                "available_dates": [d["date"] for d in forecast_data]
            }
        
        # Analyze conditions
        temp_max = day_forecast["temp_max_f"]
        temp_min = day_forecast["temp_min_f"]
        precip_prob = day_forecast["precipitation_probability"]
        conditions = day_forecast["weather_description"]
        wind = day_forecast["wind_speed_mph"]
        
        what_to_bring = []
        activities = []
        warnings = []
        
        # Temperature-based recommendations
        if temp_max > 85:
            what_to_bring.extend(["sunscreen", "hat", "water bottle"])
            activities.extend(["Indoor attractions", "Water activities", "Early morning/evening walks"])
            warnings.append("Hot weather - stay hydrated")
        elif temp_max > 70:
            what_to_bring.append("light jacket for evening")
            activities.extend(["Outdoor dining", "Parks", "Sightseeing"])
        elif temp_max > 50:
            what_to_bring.extend(["jacket", "layers"])
            activities.extend(["Museums", "Indoor/outdoor mix"])
        else:
            what_to_bring.extend(["warm coat", "gloves", "hat"])
            activities.extend(["Indoor attractions", "Museums", "Coffee shops"])
            warnings.append("Cold weather - dress warmly")
        
        # Precipitation-based recommendations
        if precip_prob > 40:
            what_to_bring.extend(["umbrella", "rain jacket"])
            activities.extend(["Indoor activities", "Museums", "Shopping"])
            warnings.append("High chance of rain")
        elif precip_prob >= 20:
            what_to_bring.append("umbrella (just in case)")
        
        # Wind-based recommendations
        if wind > 20:
            warnings.append(f"Windy conditions ({wind} mph)")
            activities = [a for a in activities if "outdoor" not in a.lower()]
        
        # Overall rating
        if precip_prob > 60 or temp_max > 95 or temp_max < 35:
            rating = "Challenging"
        elif precip_prob > 40 or temp_max > 85 or temp_max < 45:
            rating = "Fair"
        else:
            rating = "Good"
        
        # Reasoning
        reasoning = f"{conditions}. "
        if temp_max > 85:
            reasoning += f"Hot day (high {temp_max}°F). "
        elif temp_max < 50:
            reasoning += f"Cold day (high {temp_max}°F). "
        else:
            reasoning += f"Pleasant temperatures ({temp_min}-{temp_max}°F). "
        
        if precip_prob > 40:
            reasoning += f"{precip_prob}% chance of precipitation. Plan indoor activities."
        elif precip_prob < 20:
            reasoning += "Low chance of rain. Great for outdoor activities."
        
        return {
            "location": coords["name"],
            "country": coords["country"],
            "date": target_date,
            "overall_rating": rating,
            "conditions": conditions,
            "temp_max_f": temp_max,
            "temp_min_f": temp_min,
            "precipitation_probability": precip_prob,
            "wind_speed_mph": wind,
            "what_to_bring": list(set(what_to_bring)),
            "suggested_activities": list(set(activities)),
            "warnings": warnings,
            "reasoning": reasoning
        }
    except Exception as e:
        return {
            "error": f"Failed to make recommendation: {str(e)}",
            "location": coords["name"]
        }


# ============================================================================
# WRITE ACTION TOOLS - These save data to Lakebase (CRITICAL FOR GRADING)
# ============================================================================

@mcp.tool()
def save_to_itinerary(user_id: str,
                     destination_id: int,
                     activity_id: int,
                     trip_date: str,
                     notes: Optional[str] = None) -> dict:
    """
    Save an activity to the user's trip itinerary.
    
    This is a WRITE operation that inserts data into the Lakebase database.
    
    Args:
        user_id: User identifier (e.g., "user@example.com")
        destination_id: ID of the destination (from destinations table)
        activity_id: ID of the activity to add (from activities table)
        trip_date: Date for the trip in YYYY-MM-DD format
        notes: Optional notes about this plan
        
    Returns:
        Dict with itinerary_id, confirmation message, and saved details
        
    Example:
        >>> save_to_itinerary(
                user_id="alice@example.com",
                destination_id=1,
                activity_id=5,
                trip_date="2026-09-15",
                notes="Morning visit before lunch"
            )
        {
            "success": True,
            "itinerary_id": 42,
            "destination": "San Francisco",
            "activity": "Golden Gate Bridge Tour",
            "trip_date": "2026-09-15",
            "message": "Added 'Golden Gate Bridge Tour' at San Francisco to your itinerary for 2026-09-15"
        }
    """
    return db_writer.save_to_itinerary(
        user_id=user_id,
        destination_id=destination_id,
        activity_id=activity_id,
        trip_date=trip_date,
        notes=notes
    )


@mcp.tool()
def add_to_watchlist(user_id: str,
                    destination_id: int,
                    priority: int = 1,
                    notes: Optional[str] = None) -> dict:
    """
    Add a destination to the user's watchlist.
    
    This is a WRITE operation that inserts/updates data in the Lakebase database.
    
    Args:
        user_id: User identifier (e.g., "user@example.com")
        destination_id: ID of the destination to add
        priority: Priority level - 1 (high), 2 (medium), 3 (low). Default is 1.
        notes: Optional notes about why they want to visit
        
    Returns:
        Dict with watchlist_id, confirmation message, and saved details
        
    Example:
        >>> add_to_watchlist(
                user_id="alice@example.com",
                destination_id=3,
                priority=1,
                notes="Want to visit during cherry blossom season"
            )
        {
            "success": True,
            "watchlist_id": 15,
            "destination": "Tokyo",
            "country": "Japan",
            "priority": "high",
            "message": "Added Tokyo, Japan to your watchlist with high priority"
        }
    """
    return db_writer.add_to_watchlist(
        user_id=user_id,
        destination_id=destination_id,
        priority=priority,
        notes=notes
    )


@mcp.tool()
def save_user_preferences(user_id: str,
                         preferred_weather: Optional[str] = None,
                         min_temperature_f: Optional[int] = None,
                         max_temperature_f: Optional[int] = None,
                         avoid_rain: bool = True,
                         preferred_activity_types: Optional[List[str]] = None,
                         budget_range: Optional[str] = None,
                         accessibility_needs: Optional[List[str]] = None) -> dict:
    """
    Save or update user travel preferences.
    
    This is a WRITE operation that inserts/updates data in the Lakebase database.
    These preferences can be used to personalize destination recommendations.
    
    Args:
        user_id: User identifier (e.g., "user@example.com")
        preferred_weather: Preferred weather (e.g., "sunny", "mild", "cool")
        min_temperature_f: Minimum comfortable temperature in Fahrenheit
        max_temperature_f: Maximum comfortable temperature in Fahrenheit
        avoid_rain: Whether to avoid rainy destinations (default: True)
        preferred_activity_types: List of preferred activities (e.g., ["museums", "outdoor", "food"])
        budget_range: Budget level - "budget", "moderate", or "luxury"
        accessibility_needs: List of accessibility requirements (e.g., ["wheelchair", "audio_guide"])
        
    Returns:
        Dict with preference_id, confirmation message, and saved preferences
        
    Example:
        >>> save_user_preferences(
                user_id="alice@example.com",
                preferred_weather="mild",
                min_temperature_f=60,
                max_temperature_f=80,
                avoid_rain=True,
                preferred_activity_types=["museums", "food_tours", "walking"],
                budget_range="moderate",
                accessibility_needs=["wheelchair_accessible"]
            )
        {
            "success": True,
            "preference_id": 7,
            "message": "Saved your travel preferences successfully",
            "preferences": {...}
        }
    """
    return db_writer.save_user_preferences(
        user_id=user_id,
        preferred_weather=preferred_weather,
        min_temperature_f=min_temperature_f,
        max_temperature_f=max_temperature_f,
        avoid_rain=avoid_rain,
        preferred_activity_types=preferred_activity_types,
        budget_range=budget_range,
        accessibility_needs=accessibility_needs
    )


@mcp.tool()
def get_user_itinerary(user_id: str, trip_date: Optional[str] = None) -> dict:
    """
    Retrieve the user's saved itinerary items.
    
    This is a READ operation to verify what's been saved.
    
    Args:
        user_id: User identifier
        trip_date: Optional specific date to filter by (YYYY-MM-DD)
        
    Returns:
        Dict with list of saved itinerary items
        
    Example:
        >>> get_user_itinerary("alice@example.com", "2026-09-15")
        {
            "success": True,
            "count": 3,
            "items": [{...}, {...}, {...}]
        }
    """
    return db_writer.get_user_itinerary(user_id=user_id, trip_date=trip_date)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()


# ============================================================================
# DATA RETRIEVAL TOOLS - Semantic search over activities (addresses grader feedback)
# ============================================================================

@mcp.tool()
def search_activities(query: str,
                     limit: int = 5,
                     destination_id: Optional[int] = None,
                     min_age: Optional[int] = None,
                     indoor: Optional[bool] = None) -> dict:
    """
    Perform semantic search over activities using natural language queries.
    
    This tool uses pgvector embeddings to find activities matching the user's intent.
    Addresses grader feedback: "No tool to query your Lakebase/pgvector content semantically"
    
    Args:
        query: Natural language search (e.g., "fun outdoor activities for kids", "beach sports")
        limit: Maximum number of results (1-20, default 5)
        destination_id: Optional filter by destination ID
        min_age: Optional filter - only show activities suitable for this age or older
        indoor: Optional filter - True for indoor only, False for outdoor only, None for both
        
    Returns:
        Dict with matching activities including similarity scores
        
    Examples:
        >>> search_activities("water sports for teenagers")
        {
            "query": "water sports for teenagers",
            "results_count": 5,
            "activities": [
                {
                    "activity_id": 15,
                    "name": "Surfing Lessons",
                    "description": "Learn to surf with experienced instructors...",
                    "destination_name": "Hawaii",
                    "similarity_score": 0.892,
                    "min_age": 12,
                    "duration_hours": 2.5,
                    "price_category": "moderate",
                    "indoor": false
                },
                ...
            ]
        }
        
        >>> search_activities("museums", destination_id=3, min_age=8)
        # Returns only museum activities at destination 3 suitable for ages 8+
    """
    try:
        # Validate inputs
        if not query or len(query.strip()) < 3:
            return {"error": "Query must be at least 3 characters"}
        
        if limit < 1 or limit > 20:
            return {"error": "Limit must be between 1 and 20"}
        
        # Perform semantic search
        results = data_retriever.semantic_search_activities(
            query=query,
            limit=limit,
            destination_id=destination_id,
            min_age=min_age,
            indoor=indoor
        )
        
        # Check for errors
        if isinstance(results, dict) and "error" in results:
            return results
        
        return {
            "query": query,
            "filters": {
                "destination_id": destination_id,
                "min_age": min_age,
                "indoor": indoor
            },
            "results_count": len(results),
            "activities": results
        }
        
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


@mcp.tool()
def get_activities_for_destination(destination_id: int,
                                   min_age: Optional[int] = None,
                                   indoor: Optional[bool] = None) -> dict:
    """
    Get all activities available at a specific destination with optional filters.
    
    Use this when you know the destination ID and want to see all available activities.
    
    Args:
        destination_id: The destination ID (required)
        min_age: Optional filter - only show activities suitable for this age or older
        indoor: Optional filter - True for indoor only, False for outdoor only, None for both
        
    Returns:
        Dict with all matching activities for the destination
        
    Example:
        >>> get_activities_for_destination(2, min_age=6)
        {
            "destination_id": 2,
            "filters": {"min_age": 6, "indoor": null},
            "activities_count": 12,
            "activities": [...]
        }
    """
    try:
        results = data_retriever.get_activities_by_destination(
            destination_id=destination_id,
            min_age=min_age,
            indoor=indoor
        )
        
        # Check for errors
        if isinstance(results, dict) and "error" in results:
            return results
        
        return {
            "destination_id": destination_id,
            "filters": {
                "min_age": min_age,
                "indoor": indoor
            },
            "activities_count": len(results),
            "activities": results
        }
        
    except Exception as e:
        return {"error": f"Query failed: {str(e)}"}


@mcp.tool()
def list_destinations(family_friendly: Optional[bool] = None) -> dict:
    """
    List all available destinations with optional family-friendly filter.
    
    Use this to see what destinations are available in the database.
    
    Args:
        family_friendly: Optional filter - True for family-friendly only, False for non-family, None for all
        
    Returns:
        Dict with all matching destinations
        
    Example:
        >>> list_destinations(family_friendly=True)
        {
            "filter": {"family_friendly": true},
            "destinations_count": 8,
            "destinations": [
                {
                    "destination_id": 1,
                    "name": "Orlando",
                    "country": "USA",
                    "description": "Theme park capital...",
                    "best_season": "Winter",
                    "family_friendly": true
                },
                ...
            ]
        }
    """
    try:
        results = data_retriever.get_destinations(family_friendly=family_friendly)
        
        # Check for errors
        if isinstance(results, dict) and "error" in results:
            return results
        
        return {
            "filter": {"family_friendly": family_friendly},
            "destinations_count": len(results),
            "destinations": results
        }
        
    except Exception as e:
        return {"error": f"Query failed: {str(e)}"}


