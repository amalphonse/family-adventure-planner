"""
Weather Prediction MCP Server
FastMCP server exposing weather forecast and recommendation tools
"""

from fastmcp import FastMCP
from weather_broker import WeatherBroker
from typing import Optional

# Initialize FastMCP server
mcp = FastMCP("Family Adventure Weather Server")

# Initialize weather broker
weather = WeatherBroker()


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


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
