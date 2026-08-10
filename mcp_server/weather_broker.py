"""
Weather Broker Module - handles all API calls to Open-Meteo
Keeps MCP tool functions clean by encapsulating HTTP logic
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class WeatherBroker:
    """
    Adapter for Open-Meteo API (free, no API key required)
    https://open-meteo.com/
    """
    
    BASE_URL = "https://api.open-meteo.com/v1"
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "FamilyAdventurePlanner/1.0"
        })
    
    def geocode_location(self, location: str) -> Optional[Dict]:
        """
        Convert a location string (city name, address) to lat/lon coordinates.
        
        Args:
            location: City name or address (e.g., "San Francisco", "Chicago, IL")
            
        Returns:
            Dict with {name, latitude, longitude, country, timezone} or None if not found
        """
        try:
            response = self.session.get(
                f"{self.GEOCODING_URL}/search",
                params={
                    "name": location,
                    "count": 1,
                    "language": "en",
                    "format": "json"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("results"):
                return None
                
            result = data["results"][0]
            return {
                "name": result.get("name"),
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude"),
                "country": result.get("country"),
                "timezone": result.get("timezone", "UTC")
            }
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None
    
    def get_current_weather(self, latitude: float, longitude: float) -> Dict:
        """
        Get current weather conditions for a location.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dict with current weather data
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                              "precipitation,weather_code,wind_speed_10m,wind_direction_10m",
                    "temperature_unit": "fahrenheit",
                    "wind_speed_unit": "mph",
                    "precipitation_unit": "inch"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            return {
                "timestamp": current.get("time"),
                "temperature_f": current.get("temperature_2m"),
                "feels_like_f": current.get("apparent_temperature"),
                "humidity_percent": current.get("relative_humidity_2m"),
                "precipitation_inch": current.get("precipitation"),
                "weather_code": current.get("weather_code"),
                "weather_description": self._decode_weather_code(current.get("weather_code")),
                "wind_speed_mph": current.get("wind_speed_10m"),
                "wind_direction_degrees": current.get("wind_direction_10m")
            }
        except Exception as e:
            raise RuntimeError(f"Failed to fetch current weather: {e}")
    
    def get_forecast(self, latitude: float, longitude: float, days: int = 7) -> List[Dict]:
        """
        Get weather forecast for upcoming days.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            days: Number of days to forecast (1-16)
            
        Returns:
            List of daily forecast dicts
        """
        try:
            days = max(1, min(days, 16))  # Clamp to API limits
            
            response = self.session.get(
                f"{self.BASE_URL}/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,"
                            "precipitation_probability_max,weather_code,wind_speed_10m_max",
                    "temperature_unit": "fahrenheit",
                    "wind_speed_unit": "mph",
                    "precipitation_unit": "inch",
                    "forecast_days": days
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            
            forecasts = []
            for i, date in enumerate(dates):
                forecasts.append({
                    "date": date,
                    "temp_max_f": daily.get("temperature_2m_max", [])[i],
                    "temp_min_f": daily.get("temperature_2m_min", [])[i],
                    "precipitation_inch": daily.get("precipitation_sum", [])[i],
                    "precipitation_probability": daily.get("precipitation_probability_max", [])[i],
                    "weather_code": daily.get("weather_code", [])[i],
                    "weather_description": self._decode_weather_code(daily.get("weather_code", [])[i]),
                    "wind_speed_mph": daily.get("wind_speed_10m_max", [])[i]
                })
            
            return forecasts
        except Exception as e:
            raise RuntimeError(f"Failed to fetch forecast: {e}")
    
    def _decode_weather_code(self, code: Optional[int]) -> str:
        """
        Convert WMO weather code to human-readable description.
        https://open-meteo.com/en/docs
        """
        if code is None:
            return "Unknown"
        
        codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        return codes.get(code, f"Unknown weather code {code}")
