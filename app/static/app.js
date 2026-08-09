// Family Adventure Planner - Frontend JavaScript

const API_BASE_URL = 'http://localhost:8000';

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
        showError('Failed to search activities. Make sure the Flask API is running on localhost:8000.');
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
        
        // Display destinations
        displayDestinations(destinations);
        
    } catch (error) {
        console.error('Load destinations error:', error);
        document.getElementById('destinations').innerHTML = `
            <div style="padding: 20px; text-align: center; color: #666;">
                Unable to load destinations. Make sure the Flask API is running.
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
            <div class="destination-card" onclick="searchDestinationActivities('${escapeHtml(dest.name)}')">
                <div class="destination-name">${escapeHtml(dest.name)}</div>
                <div class="destination-country">🌍 ${escapeHtml(dest.country)}</div>
                <div class="destination-description">
                    ${truncateText(escapeHtml(dest.description), 120)}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
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