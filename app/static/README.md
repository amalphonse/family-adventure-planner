# Family Adventure Planner - Frontend

Simple, modern web UI for searching family-friendly activities.

## Features

* **Semantic Search** - Natural language activity search
* **Smart Filters** - Age range, indoor/outdoor
* **Browse Destinations** - Click to see activities
* **Real-time Results** - Live API integration
* **Responsive Design** - Works on mobile and desktop

## Files

* `index.html` - Main UI structure
* `styles.css` - Modern gradient design
* `app.js` - API client logic

## How It Works

1. User enters search query (e.g., "indoor museum")
2. JavaScript calls Flask API `/activities/search` endpoint
3. pgvector performs semantic similarity search
4. Results displayed as cards with similarity scores

## Running Locally

1. Start Flask backend:
```bash
cd app/
python app.py
```

2. Open browser to:
```
http://localhost:8000
```

The Flask app serves both the API and the frontend!

## API Calls

The frontend makes these API calls:

* `GET /destinations` - Load destination cards
* `GET /activities/search?query=...&min_age=2` - Semantic search

## Customization

**Change colors:** Edit CSS variables in `styles.css`:
```css
:root {
    --primary-color: #2563eb;  /* Blue */
}
```

**Add more filters:** Update `index.html` + `app.js`

**Modify layout:** Grid sizes in `styles.css`