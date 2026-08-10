# Quick Deployment Guide - Weather MCP Server

**Goal:** Get the Weather MCP Server + Agent Bricks agent running in < 30 minutes

**Status:** Code complete ✅ | Testing complete ✅ | Deploy in progress 🚀

---

## Step 1: Deploy the MCP Server App (5 minutes)

The app is already created: `weather-mcp-server`

**Using Databricks Apps UI:**

1. Navigate to: **Databricks Workspace → Apps**
2. Find: `weather-mcp-server`
3. Click: **"Deploy"** button
4. Source path: `/Workspace/Users/anju.chinniah@gmail.com/family-adventure-planner/mcp_server`
5. Wait ~2-3 minutes for deployment (installs fastmcp + requests)

**Or using CLI (if unblocked):**
```bash
databricks apps deploy weather-mcp-server \
  --source-code-path /Workspace/Users/anju.chinniah@gmail.com/family-adventure-planner/mcp_server
```

**Verify deployment:**
```bash
databricks apps get weather-mcp-server | grep -E "state|message"
```

Expected: `"state": "RUNNING"`

**App URL:** https://weather-mcp-server-7474644727314917.aws.databricksapps.com

---

## Step 2: Register MCP Server in Agent Bricks (5 minutes)

1. Navigate to: **Databricks Workspace → Agents** (or **Agent Bricks**)
2. Click: **"External Tools"** or **"MCP Servers"** tab
3. Click: **"+ Add MCP Server"**
4. Fill in:
   * **Name:** `weather-mcp-server`
   * **URL:** `https://weather-mcp-server-7474644727314917.aws.databricksapps.com`
   * **Type:** HTTP/Streaming MCP
   * **Description:** "Weather forecasting for Family Adventure Planner"
5. Click: **"Test Connection"** → Should see ✅ success
6. Click: **"Save"**

**Tools should appear:**
* get_current_weather
* get_forecast
* predict_umbrella_needed
* get_travel_recommendation

---

## Step 3: Create the Agent (10 minutes)

1. Navigate to: **Agents → Create Agent**
2. Fill in:
   * **Name:** `Family Adventure Weather Agent`
   * **Description:** `Weather forecasting and travel recommendations`
   
3. **Select Tools:**
   * Check **all 4 tools** from `weather-mcp-server`

4. **System Prompt:** (copy from below)

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

5. Click: **"Create Agent"**

---

## Step 4: Test the Agent (10 minutes)

**Test these 3 queries (required for homework):**

### Test 1: Current Weather
```
What's the weather like in San Francisco right now?
```

**Expected:**
* Agent calls `get_current_weather("San Francisco")`
* Reports actual temperature, conditions
* References the tool response data

---

### Test 2: Rain Prediction
```
Will it rain in Chicago tomorrow? Should I bring an umbrella?
```

**Expected:**
* Agent calls `predict_umbrella_needed("Chicago")`
* Gives clear Yes/No/Maybe recommendation
* Explains the reasoning (precipitation probability)

---

### Test 3: Travel Recommendation
```
We're planning a family trip to Austin this weekend. What should we pack?
```

**Expected:**
* Agent calls `get_travel_recommendation("Austin")`
* Lists what to bring (sunscreen, hat, etc.)
* Suggests activities
* Mentions any warnings (hot weather, rain, etc.)

---

## Bonus Test (Optional)

```
Compare the weather in San Francisco and Seattle for next Tuesday.
```

**Expected:**
* Agent calls `get_forecast` for both cities
* Compares conditions, temperatures
* Recommends which is better for outdoor activities

---

## Submission Checklist

- [ ] MCP server deployed and running
- [ ] MCP server registered in Agent Bricks
- [ ] Agent created with correct system prompt
- [ ] Test 1 completed (current weather)
- [ ] Test 2 completed (umbrella prediction)
- [ ] Test 3 completed (travel recommendation)
- [ ] Screenshots or paste of agent responses
- [ ] README.md shared (already in repo)
- [ ] GitHub repo pushed (already done ✅)

---

## Troubleshooting

**Problem:** App won't deploy
* Check: `/mcp_server/` folder exists at source path
* Check: `requirements.txt` and `app.yaml` are present
* Try: Restart app compute, then deploy again

**Problem:** MCP server connection test fails
* Check: App is in RUNNING state
* Check: URL is correct (ends with `.databricksapps.com`)
* Wait: 2-3 minutes after deployment before testing

**Problem:** Agent doesn't call tools
* Check: Tools are selected in agent configuration
* Check: System prompt includes tool descriptions
* Try: Rephrase question more explicitly (e.g., "Check the weather in..." instead of "weather?")

**Problem:** Tools return errors
* Check: Location names are valid cities (not fictional places)
* Check: Dates are in YYYY-MM-DD format
* Check: Dates are within 16 days (Open-Meteo limit)

---

## Time Remaining

**Started:** 12:34pm
**Due:** 6:00pm
**Remaining:** ~5.5 hours

**Estimated completion time:** 30 minutes (deployment + testing)

You have **plenty of time!** 🎉

---

## What's Already Done ✅

- [x] MCP server code (weather_mcp_server.py)
- [x] Weather broker (weather_broker.py)
- [x] requirements.txt
- [x] app.yaml
- [x] README.md with architecture
- [x] TEST_EXAMPLES.md with 6 test cases
- [x] Local testing (broker verified working)
- [x] Git commit + push to GitHub
- [x] App created (weather-mcp-server)

**Only left:** Deploy app → Register in Agent Bricks → Test 3 queries → Done!

---

**Good luck! You've got this! 🚀**
