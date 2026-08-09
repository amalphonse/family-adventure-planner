// Family Adventure Planner - Frontend JavaScript

// Use relative URLs so it works in both local dev and production
const API_BASE_URL = '';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadDestinations();
    
    // Add enter key support for search
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchActivities();
        }
    });
});

// Fetch weather forecast for a destination
async function fetchWeather(destinationId, destinationName) {
    try {
        const response = await fetch(`${API_BASE_URL}/destinations/${destinationId}/weather?days=5`);
        const data = await response.json();
        
        if (response.ok) {
            displayWeatherModal(destinationName, data);
        } else {
            alert(`❌ Error fetching weather: ${data.error || 'Unknown error'}`);
        }
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
}

// Display weather in a modal
function displayWeatherModal(destinationName, weatherData) {
    const dest = weatherData.destination;
    const forecasts = weatherData.forecasts.slice(0, 5);
    
    let forecastHTML = forecasts.map(f => `
        <div style="padding:12px;margin:8px 0;background:#f8f9fa;border-radius:6px;">
            <div style="font-weight:600;margin-bottom:4px;">${f.date}</div>
            <div>🌡️ ${f.temp_max_f}°F / ${f.temp_min_f}°F</div>
            <div>☁️ ${f.weather_condition}</div>
            <div>💧 Rain: ${f.precipitation_prob}% | 🌞 UV: ${f.uv_index} | 💨 ${f.wind_speed_mph} mph</div>
        </div>
    `).join('');
    
    const modal = document.createElement('div');
    modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:1000;';
    modal.innerHTML = `
        <div style="background:white;padding:24px;border-radius:12px;max-width:500px;max-height:80vh;overflow-y:auto;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <h2 style="margin:0;">🌦️ ${dest.name}, ${dest.country}</h2>
                <button onclick="this.parentElement.parentElement.parentElement.remove()" style="border:none;background:none;font-size:24px;cursor:pointer;">&times;</button>
            </div>
            <p style="color:#666;margin-bottom:16px;">5-Day Forecast (Open-Meteo API)</p>
            ${forecastHTML}
        </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

// Search activities with semantic search
async function searchActivities() {
    const query = document.getElementById('searchInput').value.trim();
    
    if (!query) {
        alert('Please enter a search query');
        return;
    }
    
    // Get filter values
    const minAge = document.getElementById('minAge').value;
    const maxAge = document.getElementById('maxAge').value;
    const indoor = document.getElementById('indoorFilter').value;
    
    // Build query params
    const params = new URLSearchParams({
        query: query,
        limit: 10
    });
    
    if (minAge) params.append('min_age', minAge);
    if (maxAge) params.append('max_age', maxAge);
    if (indoor) params.append('indoor', indoor);
    
    // Show loading
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/activities/search?${params}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update stats
        document.getElementById('resultCount').textContent = data.count;
        document.getElementById('stats').style.display = 'flex';
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        console.error('Search error:', error);
        showError('Failed to search activities. Please try again or contact support if the issue persists.');
    }
}

// Display search results
function displayResults(data) {
    const resultsContainer = document.getElementById('results');
    
    if (data.count === 0) {
        resultsContainer.innerHTML = `
            <div class="welcome">
                <h2>No Results Found</h2>
                <p>Try adjusting your search or filters.</p>
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="results-header">
            <h2>Found ${data.count} Activities</h2>
        </div>
        <div class="results-grid">
    `;
    
    data.results.forEach(activity => {
        const similarityPercent = Math.round(activity.similarity_score * 100);
        const ageRange = activity.max_age 
            ? `Ages ${activity.min_age}-${activity.max_age}`
            : `Ages ${activity.min_age}+`;
        
        html += `
            <div class="activity-card">
                <div class="activity-header">
                    <div>
                        <div class="activity-name">${escapeHtml(activity.activity_name)}</div>
                        <div class="activity-destination">📍 ${escapeHtml(activity.destination_name)}</div>
                    </div>
                    <div class="similarity-badge">${similarityPercent}%</div>
                </div>
                
                <div class="activity-description">
                    ${truncateText(escapeHtml(activity.description), 150)}
                </div>
                
                <div class="activity-meta">
                    <span class="meta-tag ${activity.indoor ? 'indoor' : 'outdoor'}">
                        ${activity.indoor ? '🏠 Indoor' : '⛅ Outdoor'}
                    </span>
                    <span class="meta-tag">
                        👶 ${ageRange}
                    </span>
                    <span class="meta-tag">
                        ⏱️ ${activity.duration_minutes} min
                    </span>
                    <span class="meta-tag">
                        🎯 ${activity.activity_type}
                    </span>
                    ${activity.weather_dependent ? '<span class="meta-tag">🌦️ Weather dependent</span>' : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    resultsContainer.innerHTML = html;
}

// Load and display all destinations
async function loadDestinations() {
    try {
        const response = await fetch(`${API_BASE_URL}/destinations`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const destinations = await response.json();
        
        // Update destination count
        document.getElementById('destinationCount').textContent = destinations.length;
        
        // Hide seed button if destinations exist
        const seedBtn = document.getElementById('seedBtn');
        if (destinations.length > 0) {
            seedBtn.style.display = 'none';
        } else {
            seedBtn.style.display = 'inline-block';
        }
        
        // Populate destination filter dropdown
        populateDestinationFilter(destinations);
        
        // Display destinations
        displayDestinations(destinations);
        
    } catch (error) {
        console.error('Load destinations error:', error);
        document.getElementById('destinations').innerHTML = `
            <div style="padding: 20px; text-align: center; color: #666;">
                Unable to load destinations. Please refresh the page or contact support if the issue persists.
            </div>
        `;
    }
}

// Display destinations grid
function displayDestinations(destinations) {
    const container = document.getElementById('destinations');
    
    if (destinations.length === 0) {
        container.innerHTML = '<p>No destinations found.</p>';
        return;
    }
    
    let html = '';
    
    destinations.forEach(dest => {
        html += `
            <div class="destination-card">
                <div class="destination-name">${escapeHtml(dest.name)}</div>
                <div class="destination-country">🌍 ${escapeHtml(dest.country)}</div>
                <div class="destination-description">
                    ${truncateText(escapeHtml(dest.description), 120)}
                </div>
                <div style="margin-top:12px;display:flex;gap:8px;">
                    <button onclick="fetchWeather(${dest.destination_id}, '${escapeHtml(dest.name)}'); event.stopPropagation();" 
                            style="flex:1;padding:8px;background:#007bff;color:white;border:none;border-radius:4px;cursor:pointer;font-size:13px;">
                        🌦️ Weather
                    </button>
                    <button onclick="searchDestinationActivities('${escapeHtml(dest.name)}'); event.stopPropagation();" 
                            style="flex:1;padding:8px;background:#28a745;color:white;border:none;border-radius:4px;cursor:pointer;font-size:13px;">
                        🎯 Activities
                    </button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Populate destination filter dropdown
function populateDestinationFilter(destinations) {
    const select = document.getElementById('destinationFilter');
    
    // Clear existing options (except "All Destinations")
    select.innerHTML = '<option value="">All Destinations</option>';
    
    // Add destination options
    destinations.forEach(dest => {
        const option = document.createElement('option');
        option.value = dest.destination_id;
        option.textContent = dest.name;
        select.appendChild(option);
    });
}

// Search activities for a specific destination
function searchDestinationActivities(destinationName) {
    document.getElementById('searchInput').value = destinationName;
    document.getElementById('searchInput').scrollIntoView({ behavior: 'smooth' });
    searchActivities();
}

// Clear all filters
function clearFilters() {
    document.getElementById('minAge').value = '';
    document.getElementById('maxAge').value = '';
    document.getElementById('indoorFilter').value = '';
}

// Show loading state
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    document.getElementById('stats').style.display = 'none';
}

// Show error message
function showError(message) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').innerHTML = `
        <div class="error">
            <h3>⚠️ Error</h3>
            <p>${escapeHtml(message)}</p>
        </div>
    `;
    document.getElementById('results').style.display = 'block';
}

// Utility: Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility: Truncate text with ellipsis
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}