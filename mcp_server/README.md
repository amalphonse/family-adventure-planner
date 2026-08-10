# Weather Prediction MCP Server + Agent Bricks

**Weather forecasting and travel recommendations for the Family Adventure Planner**

Built for: Databricks MCP Server Homework (Due: 2026-08-10, 6pm)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User / Agent Bricks                   │
│                                                           │
│  "Will it rain in Chicago tomorrow?"                     │
│  "Should I bring a jacket to Austin this weekend?"       │
└─────────────────────┬─────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│          Weather MCP Server (FastMCP)                    │
│                                                           │
│  Tools:                                                   │
│  • get_current_weather(location)                         │
│  • get_forecast(location, days)                          │
│  • predict_umbrella_needed(location, date)               │
│  • get_travel_recommendation(location, date)             │
└─────────────────────┬─────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│           Weather Broker (weather_broker.py)             │
│                                                           │
│  • geocode_location() - City → lat/lon                   │
│  • get_current_weather() - Current conditions            │
│  • get_forecast() - Multi-day forecast                   │
│  • _decode_weather_code() - WMO codes → text            │
└─────────────────────┬─────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Open-Meteo API (free, no key)               │
│                                                           │
│  • Geocoding API: https://geocoding-api.open-meteo.com   │
│  • Forecast API: https://api.open-meteo.com/v1           │
│  • ~10,000 calls/day (non-commercial use)                │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
mcp_server/
├── weather_mcp_server.py   # FastMCP server with 4 tools
├── weather_broker.py        # API adapter (all HTTP logic here)
├── requirements.txt         # fastmcp>=0.2.0, requests>=2.31.0
├── app.yaml                 # Databricks App config
└── README.md               # This file
```

## Weather API Choice

**Open-Meteo** (https://open-meteo.com/)
* ✅ No signup required
* ✅ No API key required
* ✅ ~10,000 calls/day (non-commercial)
* ✅ Global coverage
* ✅ Current conditions + 16-day forecast
* ✅ WMO standard weather codes

**Why Open-Meteo?**
* Zero friction - works immediately without credentials
* No secrets management needed for this homework
* Reliable and well-documented API
* Perfect for prototyping and educational use

## MCP Tools

### 1. `get_current_weather(location: str)`

Get current weather conditions for any location.

**Args:**
* `location`: City name or address (e.g., "San Francisco", "Chicago, IL", "Austin, TX")

**Returns:**
```json
{
  "location": "San Francisco",
  "country": "United States",
  "timestamp": "2026-08-10T19:00",
  "temperature_f": 62,
  "feels_like_f": 60,
  "conditions": "Partly cloudy",
  "humidity_percent": 75,
  "precipitation_inch": 0.0,
  "wind_speed_mph": 8,
  "wind_direction_degrees": 270
}
```

### 2. `get_forecast(location: str, days: int = 7)`

Get multi-day weather forecast (1-16 days).

**Args:**
* `location`: City name or address
* `days`: Number of days to forecast (1-16, default 7)

**Returns:**
```json
{
  "location": "Austin",
  "country": "United States",
  "forecast_days": 3,
  "forecast": [
    {
      "date": "2026-08-10",
      "temp_max_f": 95,
      "temp_min_f": 75,
      "precipitation_inch": 0.0,
      "precipitation_probability": 20,
      "conditions": "Partly cloudy",
      "wind_speed_mph": 12
    },
    ...
  ]
}
```

### 3. `predict_umbrella_needed(location: str, date: str = None)`

**Prediction tool with threshold-based reasoning** - not just a passthrough!

**Decision Logic:**
* Precipitation probability > 40% → **"Yes"** (high confidence)
* Precipitation probability 20-40% → **"Maybe"** (medium confidence)
* Precipitation probability < 20% → **"No"** (high confidence)

**Args:**
* `location`: City name or address
* `date`: YYYY-MM-DD format (defaults to tomorrow)

**Returns:**
```json
{
  "location": "Chicago",
  "date": "2026-08-11",
  "umbrella_needed": "Yes",
  "confidence": "high",
  "precipitation_probability": 65,
  "expected_precipitation_inch": 0.25,
  "conditions": "Moderate rain",
  "temp_max_f": 75,
  "temp_min_f": 62,
  "reasoning": "High chance of rain (65%). Definitely bring an umbrella."
}
```

### 4. `get_travel_recommendation(location: str, date: str = None)`

**Advanced prediction tool** - provides comprehensive travel advice based on weather.

**Analyzes:**
* Temperature range → What to pack
* Precipitation → Umbrella/rain gear
* Wind speed → Outdoor activity suitability
* Overall conditions → Activity suggestions

**Returns:**
```json
{
  "location": "Seattle",
  "country": "United States",
  "date": "2026-08-15",
  "overall_rating": "Fair",
  "conditions": "Slight rain",
  "temp_max_f": 68,
  "temp_min_f": 55,
  "precipitation_probability": 45,
  "wind_speed_mph": 10,
  "what_to_bring": [
    "light jacket for evening",
    "umbrella",
    "rain jacket"
  ],
  "suggested_activities": [
    "Indoor activities",
    "Museums",
    "Shopping"
  ],
  "warnings": [
    "High chance of rain"
  ],
  "reasoning": "Slight rain. Pleasant temperatures (55-68°F). 45% chance of precipitation. Plan indoor activities."
}
```

## Setup Instructions

### 1. Deploy the MCP Server

**Option A: Using Databricks CLI**
```bash
# App already created - just deploy source code
databricks apps deploy weather-mcp-server \
  --source-code-path /Workspace/Users/anju.chinniah@gmail.com/family-adventure-planner/mcp_server
```

**Option B: Using Databricks Apps UI**
1. Navigate to Apps in your Databricks workspace
2. Find "weather-mcp-server" app
3. Click "Deploy"
4. Select source code path: `/Workspace/Users/anju.chinniah@gmail.com/family-adventure-planner/mcp_server`
5. Wait for deployment to complete (~2-3 minutes)

**MCP Server URL:**
```
https://weather-mcp-server-7474644727314917.aws.databricksapps.com
```

### 2. Register MCP Server as External Tool in Agent Bricks

1. Go to the Databricks UI → **Agents** (or **Agent Bricks**)
2. Click **"External Tools"** or **"MCP Servers"**
3. Click **"Add MCP Server"**
4. Enter:
   * **Name:** `weather-mcp-server`
   * **URL:** `https://weather-mcp-server-7474644727314917.aws.databricksapps.com`
   * **Type:** HTTP/Streaming MCP
5. Click **"Test Connection"** to verify
6. Click **"Save"**

### 3. Create the Agent Bricks Agent

**Agent Configuration:**

* **Name:** `Family Adventure Weather Agent`
* **Description:** `Weather forecasting and travel recommendations for family trips`
* **Tools:** Select your registered `weather-mcp-server` (all 4 tools)
* **System Prompt:** (see below)

**System Prompt:**
```
You are a helpful weather assistant for the Family Adventure Planner app.

Your role is to answer weather-related questions and provide travel recommendations 
for families planning trips. You have access to real-time weather data and forecasting 
tools.

Tools available:
1. get_current_weather(location) - Current conditions
2. get_forecast(location, days) - Multi-day forecast
3. predict_umbrella_needed(location, date) - Umbrella recommendation
4. get_travel_recommendation(location, date) - Comprehensive travel advice

Guidelines:
- Always call a tool to get weather data - NEVER guess or make up weather information
- If a location cannot be found, ask the user to clarify or try a different name
- When recommending activities, consider the age-appropriateness for families with children
- Explain your reasoning based on the weather data returned from tools
- If a tool call fails, say so clearly rather than hallucinating data
- For date-specific questions, use the YYYY-MM-DD format
- Be concise but friendly - you're helping families plan fun adventures

Example interactions:
- "Will it rain in Chicago tomorrow?" → Call predict_umbrella_needed
- "What's the weather like in Austin this weekend?" → Call get_forecast for 2-3 days
- "Should we bring jackets to Seattle next week?" → Call get_travel_recommendation
- "Is it a good day for outdoor activities in San Francisco?" → Call get_current_weather + get_travel_recommendation
```

### 4. Test the Agent

Try these natural-language questions:

**Test 1: Current conditions**
```
User: "What's the weather like in San Francisco right now?"

Expected: Agent calls get_current_weather("San Francisco") and reports 
temperature, conditions, and whether it's good for outdoor activities.
```

**Test 2: Forecast query**
```
User: "Will it rain in Chicago this weekend?"

Expected: Agent calls get_forecast("Chicago", days=3) or 
predict_umbrella_needed("Chicago", date=<Saturday>) and provides a clear answer.
```

**Test 3: Travel recommendation**
```
User: "We're planning a family trip to Austin next week. What should we pack?"

Expected: Agent calls get_travel_recommendation("Austin", date=<next week date>) 
and lists what to bring, suggested activities, and any warnings.
```

## Testing Locally (Optional)

Test the weather broker before deploying:

```python
from weather_broker import WeatherBroker

broker = WeatherBroker()

# Test geocoding
coords = broker.geocode_location("San Francisco")
print(coords)

# Test current weather
current = broker.get_current_weather(coords["latitude"], coords["longitude"])
print(f"Temperature: {current['temperature_f']}°F")
print(f"Conditions: {current['weather_description']}")

# Test forecast
forecast = broker.get_forecast(coords["latitude"], coords["longitude"], days=3)
for day in forecast:
    print(f"{day['date']}: {day['temp_max_f']}°F, {day['weather_description']}")
```

## Error Handling

The MCP server handles errors gracefully:

* **Location not found:** Returns `{"error": "Could not find location: X", "suggestion": "Try a different city name"}`
* **API failure:** Returns `{"error": "Failed to fetch weather: <reason>"}`
* **Date out of range:** Returns `{"error": "No forecast available for date: X", "available_dates": [...]}`

The Agent Bricks agent should react to these errors by:
1. Notifying the user of the issue
2. Asking for clarification or a different location
3. NOT guessing or making up data

## Deployment Checklist

- [x] MCP server code written (weather_mcp_server.py)
- [x] Weather broker module created (weather_broker.py)
- [x] requirements.txt defined
- [x] app.yaml configured
- [x] Local testing completed (broker works)
- [ ] MCP server deployed as Databricks App
- [ ] MCP server registered as external tool
- [ ] Agent Bricks agent created
- [ ] System prompt configured
- [ ] 3+ test queries demonstrated

## Submission Requirements

1. ✅ **MCP Server** - FastMCP with 4 tools, deployed as Databricks App
2. ✅ **Weather Broker** - Separate adapter module with all HTTP logic
3. ✅ **No API keys** - Using Open-Meteo (no credentials required)
4. ✅ **Prediction tools** - umbrella_needed and travel_recommendation apply logic, not just passthrough
5. ✅ **Error handling** - Clean error messages, no stack traces
6. ✅ **Clear docstrings** - Args/Returns documented for all tools
7. ✅ **README** - This file! Architecture, setup, testing instructions
8. [ ] **Agent demonstration** - 3+ natural-language Q&A examples

## App URLs

* **Weather MCP Server:** https://weather-mcp-server-7474644727314917.aws.databricksapps.com
* **Family Adventure Planner:** https://family-adventure-planner-7474644727314917.aws.databricksapps.com

## Repository

GitHub: https://github.com/[your-repo]/family-adventure-planner

## Time to Complete

Estimated: ~3-4 hours
* MCP server code: 1 hour
* Testing & debugging: 30 minutes
* Agent Bricks setup: 1 hour
* Documentation: 30 minutes
* Demonstration: 30 minutes

---

**Built with:** FastMCP, Open-Meteo API, Databricks Apps, Agent Bricks
**Date:** 2026-08-10
**Author:** anju.chinniah@gmail.com
