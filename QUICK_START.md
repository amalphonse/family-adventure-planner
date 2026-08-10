# 🚀 QUICK START - Weather MCP Server Testing

**⏰ Current Time:** 3:47pm  
**⏰ Deadline:** 6:00pm  
**⏰ Time Remaining:** 2 hours 13 minutes

---

## ✅ What's Already Done

- ✅ MCP Server code written
- ✅ Weather broker adapter implemented
- ✅ 4 tools created (2 with prediction logic)
- ✅ Deployed to: https://weather-mcp-server-7474644727314917.aws.databricksapps.com
- ✅ Server tested and responding
- ✅ Documentation complete
- ✅ All code on GitHub

---

## 📋 What You Need to Do (30 minutes)

### YOU ARE ALREADY ON THE RIGHT PAGE! (AI Playground)

### Step 1: Register MCP Server (5 min)
1. Look for "External Tools" or "+" button
2. Add MCP Server:
   - URL: `https://weather-mcp-server-7474644727314917.aws.databricksapps.com`
   - Name: `weather-mcp-server`
3. Test connection → Should see 4 tools

### Step 2: Create Agent (5 min)
1. Click "New Agent"
2. Select the 4 weather tools
3. Copy system prompt from `AGENT_BRICKS_TESTING.md`
4. Save

### Step 3: Test 3 Queries (15 min)
Copy these exactly:

**Query 1:**
```
What's the weather like in San Francisco right now?
```

**Query 2:**
```
Will it rain in Chicago tomorrow? Should I bring an umbrella?
```

**Query 3:**
```
We're planning a family trip to Austin this weekend. What should we pack?
```

### Step 4: Take Screenshots (5 min)
For each query, capture:
- Your question
- The tool call
- Agent's response

---

## 📁 Files Created for You

1. **AGENT_BRICKS_TESTING.md** - Detailed instructions
2. **HOMEWORK_SUBMISSION.md** - Template to fill in results
3. **QUICK_START.md** - This file!

---

## 🎯 Success Checklist

- [ ] MCP server registered in Agent Bricks
- [ ] Agent created with 4 tools
- [ ] Tested: "What's the weather in San Francisco?"
- [ ] Tested: "Will it rain in Chicago tomorrow?"
- [ ] Tested: "What should we pack for Austin?"
- [ ] Screenshots taken (9 total: 3 per test)
- [ ] Results filled in HOMEWORK_SUBMISSION.md

---

## 💡 Pro Tips

- The agent should CALL TOOLS, not guess weather
- Look for tool calls in the agent's response
- If agent hallucinates, check system prompt is included
- Each test should show the tool name and parameters

---

## 🆘 Emergency Contact

If stuck, check:
1. Server status: `databricks apps get weather-mcp-server`
2. Server logs: `databricks apps logs weather-mcp-server`
3. Full guide: `AGENT_BRICKS_TESTING.md`

---

**YOU'VE GOT THIS! 30 MINUTES TO COMPLETE! 🌟**
