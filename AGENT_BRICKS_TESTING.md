# Agent Bricks Testing Guide - Weather MCP Server

**Date:** August 10, 2026  
**Time:** 3:44pm (2h 16min until 6pm deadline)  
**MCP Server URL:** https://weather-mcp-server-7474644727314917.aws.databricksapps.com

---

## ✅ Pre-Testing Checklist

- [x] Weather MCP Server deployed successfully
- [x] Server responding on https://weather-mcp-server-7474644727314917.aws.databricksapps.com
- [x] SSE endpoint accessible at /sse
- [x] 4 tools ready: get_current_weather, get_forecast, predict_umbrella_needed, get_travel_recommendation
- [ ] Registered in Agent Bricks as external tool
- [ ] Agent created with system prompt
- [ ] 3 test queries completed

---

## 📋 Step 1: Register MCP Server in Agent Bricks (5 minutes)

### You are already on the AI Playground page! Perfect!

1. **Look for "External Tools" or "Model Serving" section**
   - Should be in left sidebar or top menu
   
2. **Click "+ Add External Tool" or "+ Register MCP Server"**

3. **Fill in the registration form:**
   ```
   Name: weather-mcp-server
   
   Type: MCP Server (or HTTP/Streaming MCP)
   
   URL: https://weather-mcp-server-7474644727314917.aws.databricksapps.com
   
   Description: Weather forecasting and travel recommendations for family trips
   
   Authentication: None (Databricks Apps handles auth automatically)
   ```

4. **Click "Test Connection"**
   - Should see ✅ Success message
   - Should discover 4 tools automatically

5. **Click "Save" or "Register"**

---

## 📋 Step 2: Create Agent (5 minutes)

### In Agent Bricks / AI Playground:

1. **Click "+ New Agent" or "Create Agent"**

2. **Basic Info:**
   ```
   Agent Name: Family Adventure Weather Assistant
   
   Description: Helps families plan trips with real-time weather data and recommendations
   ```

3. **Select Model:**
   - Use any available model (GPT-4, Claude, etc.)

4. **Select Tools - CHECK ALL 4:**
   - ✅ get_current_weather
   - ✅ get_forecast  
   - ✅ predict_umbrella_needed
   - ✅ get_travel_recommendation

5. **System Prompt** (copy this exactly):

```
You are a helpful weather assistant for the Family Adventure Planner app.

Your role is to answer weather-related questions and provide travel recommendations 
for families planning trips. You have access to real-time weather data and forecasting 
tools.

Tools available:
1. get_current_weather(location) - Current conditions
2. get_forecast(location, days) - Multi-day forecast (up to 7 days)
3. predict_umbrella_needed(location, date) - Umbrella recommendation with reasoning
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

6. **Click "Create Agent" or "Save"**

---

## 📋 Step 3: Test with 3 Required Queries (15 minutes)

### Test Query 1: Current Weather

**Ask the agent:**
```
What's the weather like in San Francisco right now?
```

**Expected Behavior:**
1. Agent calls `get_current_weather("San Francisco")`
2. Reports actual temperature (e.g., "62°F")
3. Describes conditions (e.g., "Partly cloudy")
4. References the tool response (doesn't hallucinate)

**What to capture:**
- Screenshot of your question
- Screenshot showing the tool call
- Screenshot of the agent's response

---

### Test Query 2: Umbrella Prediction

**Ask the agent:**
```
Will it rain in Chicago tomorrow? Should I bring an umbrella?
```

**Expected Behavior:**
1. Agent calls `predict_umbrella_needed("Chicago", "2026-08-11")`
2. Gives clear Yes/No/Maybe recommendation
3. Explains reasoning (e.g., "40% chance of rain, so maybe bring one just in case")
4. Cites specific precipitation probability from tool

**What to capture:**
- Screenshot of your question
- Screenshot showing the tool call
- Screenshot of the recommendation with reasoning

---

### Test Query 3: Travel Recommendation

**Ask the agent:**
```
We're planning a family trip to Austin this weekend. What should we pack?
```

**Expected Behavior:**
1. Agent calls `get_travel_recommendation("Austin", "2026-08-12")`
2. Lists what to bring:
   - Sunscreen (if sunny)
   - Hat (if sunny)
   - Water bottles (if hot)
   - Rain jacket (if rainy)
   - Layers (if variable temps)
3. Suggests activities appropriate for weather
4. Mentions any warnings (heat advisory, storms, etc.)

**What to capture:**
- Screenshot of your question
- Screenshot showing the tool call
- Screenshot of the packing list and recommendations

---

## 📋 Step 4: Verify Tool Accuracy (Bonus - 5 minutes)

### Additional Test (Optional but Impressive):

**Ask the agent:**
```
Compare the weather in Miami and Seattle today. Which is better for outdoor family activities?
```

**Expected Behavior:**
1. Agent calls `get_current_weather("Miami")`
2. Agent calls `get_current_weather("Seattle")`
3. Compares both locations
4. Makes family-friendly recommendation based on data

---

## 📸 What to Capture for Submission

### For Each Test Query, Take 3 Screenshots:

1. **Your Question** - Show what you asked
2. **Tool Call** - Show the tool being invoked with parameters
3. **Agent Response** - Show the full answer

### Organize Like This:

```
HOMEWORK_SUBMISSION/
├── test1_current_weather/
│   ├── 1_question.png
│   ├── 2_tool_call.png
│   └── 3_response.png
├── test2_umbrella_prediction/
│   ├── 1_question.png
│   ├── 2_tool_call.png
│   └── 3_response.png
├── test3_travel_recommendation/
│   ├── 1_question.png
│   ├── 2_tool_call.png
│   └── 3_response.png
└── SUBMISSION.md (include written description of results)
```

---

## ✅ Success Criteria

Your agent passes if:

1. ✅ All 4 tools are available to the agent
2. ✅ Agent successfully calls tools (doesn't hallucinate weather data)
3. ✅ Tool responses contain real data from Open-Meteo API
4. ✅ Agent explains reasoning based on tool outputs
5. ✅ Umbrella prediction includes clear Yes/No/Maybe + reasoning
6. ✅ Travel recommendation includes packing list + activities
7. ✅ Agent handles errors gracefully (location not found, etc.)

---

## 🐛 Troubleshooting

### "Tool not found" or "Connection failed"
- Check MCP server URL is correct
- Verify app is RUNNING (not stopped)
- Try re-registering the MCP server

### "Agent doesn't call tools" or "Hallucinating weather data"
- Check system prompt is included correctly
- Verify tools are selected in agent configuration
- Try rephrasing question to be more explicit

### "Tool returns error"
- Location name might be invalid - try major cities
- Date format must be YYYY-MM-DD
- Check MCP server logs: `databricks apps logs weather-mcp-server`

---

## 🎯 Time Estimate

- Register MCP Server: 5 minutes
- Create Agent: 5 minutes
- Test 3 queries: 15 minutes (5 min each)
- Take screenshots: 5 minutes
- Organize submission: 5 minutes

**Total: 35 minutes**

**Current time:** 3:44pm  
**Deadline:** 6:00pm  
**Time remaining:** 2 hours 16 minutes ✅ Plenty of time!

---

## 📝 Quick Notes for Write-Up

**What this homework demonstrates:**
1. Building an MCP (Model Context Protocol) server
2. Integrating external APIs (Open-Meteo weather API)
3. Creating logic-based prediction tools (umbrella needed)
4. Providing actionable recommendations (travel advice)
5. Connecting MCP server to Agent Bricks
6. Testing agent behavior with real-world queries

**Key Technical Achievements:**
- FastMCP framework for server implementation
- Weather broker adapter pattern for API calls
- Threshold-based logic for predictions (precipitation > 30% = umbrella)
- Comprehensive recommendations based on conditions
- Error handling and geocoding fallbacks
- No API key required (using free Open-Meteo service)

---

Good luck! You've got this! 🌟
