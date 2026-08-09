# Databricks App Deployment Guide

This guide walks you through deploying the Family Adventure Planner as a Databricks App.

## What is a Databricks App?

A Databricks App is a managed application that runs on Databricks infrastructure:
- **Automatic scaling** - Scales up/down based on traffic
- **Integrated auth** - Uses Databricks workspace authentication
- **Managed hosting** - No server management required
- **Built-in monitoring** - Logs and metrics automatically collected

## Prerequisites

1. **Databricks CLI installed:**
```bash
pip install databricks-cli
```

2. **Workspace configured:**
```bash
databricks configure
# Or set environment variables:
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"
```

3. **Files in place:**
```
app/
├── app.yaml              ✓ Configuration file
├── app.py                ✓ Flask application
├── requirements.txt      ✓ Python dependencies
└── static/
    ├── index.html        ✓ Frontend
    ├── styles.css        ✓ Styling
    └── app.js            ✓ Frontend logic
```

## Deployment Steps

### 1. Navigate to the app directory
```bash
cd /Workspace/Users/anju.chinniah@gmail.com/family-adventure-planner/app
```

### 2. Deploy the app
```bash
databricks apps deploy family-adventure-planner
```

This command:
- Reads `app.yaml` configuration
- Packages all files in the current directory
- Installs dependencies from `requirements.txt`
- Starts the Flask server
- Returns a public URL

### 3. Check deployment status
```bash
databricks apps get family-adventure-planner
```

Expected output:
```json
{
  "name": "family-adventure-planner",
  "status": {
    "state": "RUNNING",
    "message": "App is running"
  },
  "url": "https://your-workspace.cloud.databricks.com/apps/family-adventure-planner"
}
```

### 4. Access your app
Open the URL from step 3 in your browser. You should see the search UI.

## App Configuration Explained

### app.yaml Structure

```yaml
name: family-adventure-planner
description: AI-powered trip planning assistant

resources:
  - name: family-adventure-planner-app
    app:
      # Start command
      command:
        - python
        - app.py
      
      # Environment variables
      env:
        - name: FLASK_ENV
          value: production
        - name: PORT
          value: "8000"
        - name: LAKEBASE_PROJECT
          value: family-adventure-planner
      
      # Dependencies (from requirements.txt)
      dependencies:
        - flask
        - flask-cors
        - psycopg[binary]
        - requests
        - databricks-sdk
      
      # Include all files in app/ directory
      source_code_path: .

# Who can access the app
permissions:
  - level: CAN_USE
    group_name: users  # All workspace users
```

## Management Commands

### List all apps
```bash
databricks apps list
```

### Get app details
```bash
databricks apps get family-adventure-planner
```

### View app logs
```bash
databricks apps logs family-adventure-planner
```

### Update the app (after code changes)
```bash
databricks apps deploy family-adventure-planner
```

### Stop the app
```bash
databricks apps stop family-adventure-planner
```

### Start the app
```bash
databricks apps start family-adventure-planner
```

### Delete the app
```bash
databricks apps delete family-adventure-planner
```

## Troubleshooting

### App won't start

**Check logs:**
```bash
databricks apps logs family-adventure-planner --follow
```

**Common issues:**

1. **Missing dependencies**
   - Check `requirements.txt` includes all packages
   - Verify versions are compatible

2. **Lakebase connection errors**
   - Verify `LAKEBASE_PROJECT`, `LAKEBASE_BRANCH`, `LAKEBASE_DATABASE` are correct
   - Check Lakebase endpoint is running
   - Ensure app has permissions to access Lakebase

3. **Port conflicts**
   - Flask defaults to port 8000 (specified in app.yaml)
   - Databricks Apps automatically handle port mapping

### API returns 500 errors

**Check Flask logs:**
```bash
databricks apps logs family-adventure-planner | grep ERROR
```

**Common causes:**
- Lakebase connection failed (check credentials)
- Missing environment variables
- Database schema mismatch

### Frontend not loading

**Verify static files are included:**
```bash
databricks apps get family-adventure-planner --include-files
```

**Check Flask is serving static files:**
- Ensure `static_folder='static'` in `Flask(__name__, static_folder='static')`
- Verify `index.html` exists in `app/static/`

## Architecture

```
┌─────────────────────────────────────┐
│   Browser (User)                    │
└──────────────┬──────────────────────┘
               │ HTTPS
               ▼
┌─────────────────────────────────────┐
│   Databricks Apps Platform          │
│   ┌─────────────────────────────┐   │
│   │  Flask App (app.py)         │   │
│   │  ├── / → index.html         │   │
│   │  ├── /health → status       │   │
│   │  ├── /destinations          │   │
│   │  └── /activities/search     │   │
│   └─────────────┬───────────────┘   │
└─────────────────┼───────────────────┘
                  │ psycopg + OAuth token
                  ▼
┌─────────────────────────────────────┐
│   Lakebase Postgres                 │
│   ├── destinations (with vectors)   │
│   └── activities (with vectors)     │
└─────────────────────────────────────┘
```

## Testing the Deployed App

### 1. Health check
```bash
curl https://your-workspace.cloud.databricks.com/apps/family-adventure-planner/health
```

Expected:
```json
{
  "status": "healthy",
  "service": "family-adventure-planner-api",
  "version": "1.0.0"
}
```

### 2. List destinations
```bash
curl https://your-workspace.cloud.databricks.com/apps/family-adventure-planner/destinations
```

### 3. Search activities
```bash
curl "https://your-workspace.cloud.databricks.com/apps/family-adventure-planner/activities/search?query=indoor+museum&min_age=2"
```

### 4. Access frontend
Open in browser:
```
https://your-workspace.cloud.databricks.com/apps/family-adventure-planner/
```

## CI/CD Integration

You can automate deployments with GitHub Actions:

```yaml
name: Deploy Databricks App

on:
  push:
    branches: [main]
    paths:
      - 'app/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Databricks CLI
        run: pip install databricks-cli
      
      - name: Deploy app
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: |
          cd app
          databricks apps deploy family-adventure-planner
```

## Monitoring

### View real-time metrics
```bash
databricks apps metrics family-adventure-planner
```

### Set up alerts
Navigate to the Databricks UI:
1. Go to **Compute** → **Apps**
2. Select **family-adventure-planner**
3. Click **Monitoring** tab
4. Configure alerts for:
   - High error rate
   - High latency
   - App crashes

## Permissions

By default, the app is accessible to all workspace users (`group_name: users`).

**To restrict access:**

Edit `app.yaml`:
```yaml
permissions:
  - level: CAN_USE
    user_name: specific.user@company.com
  - level: CAN_MANAGE
    user_name: admin@company.com
```

**Permission levels:**
- `CAN_USE` - Can access the app
- `CAN_MANAGE` - Can update/stop/start the app
- `IS_OWNER` - Full control

## Cost Considerations

Databricks Apps use compute resources:
- **Auto-scaling** - Scales down to zero when idle
- **Per-second billing** - Only pay for active time
- **Shared resources** - Apps share infrastructure

**To minimize costs:**
1. Set appropriate idle timeout
2. Use serverless compute when available
3. Optimize API queries for speed

## Next Steps

After deploying:
1. ✅ Test all API endpoints
2. ✅ Verify frontend loads correctly
3. ✅ Ensure Lakebase connection works
4. 📊 Build AI agent with tools (requirement #5)
5. 🔄 Set up CDF → Delta sync (requirement #6)

## Support

For issues:
- Check logs: `databricks apps logs family-adventure-planner`
- Review docs: https://docs.databricks.com/apps/
- Ask in Slack: #databricks-apps