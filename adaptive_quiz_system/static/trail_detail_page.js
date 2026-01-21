/**
 * Trail Detail Page JavaScript
 * Handles rendering trail details on a dedicated page
 */

const TrailDetailPage = (function() {
    'use strict';
    
    let currentTrail = null;
    let currentUserId = null;
    let currentUserProfile = null;
    let completedTrailData = null;
    let loadedCompletions = {}; // Store loaded completion data: {completionId: {data, date, color}}
    let currentMetric = 'heart_rate'; // Currently selected metric
    let performanceChart = null; // Chart.js instance
    
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function renderEnhancedHeader(trail) {
        const nameEl = document.getElementById('trail-detail-name');
        const statsBadgesEl = document.getElementById('trail-detail-stats-badges');
        const actionButtonsEl = document.getElementById('trail-detail-action-buttons');
        
        if (nameEl) {
            nameEl.innerHTML = `${escapeHtml(trail.name || trail.trail_id || 'Unknown Trail')} <span class="edit-icon">✏️</span>`;
        }
        
        if (statsBadgesEl) {
            let badgesHTML = '';
            
            // Difficulty badge (color-coded)
            if (trail.difficulty !== undefined && trail.difficulty !== null) {
                const diff = parseFloat(trail.difficulty);
                let diffClass = 'difficulty-medium';
                let diffText = 'Medium';
                if (diff >= 7) {
                    diffClass = 'difficulty-hard';
                    diffText = 'Hard';
                } else if (diff <= 4) {
                    diffClass = 'difficulty-easy';
                    diffText = 'Easy';
                }
                badgesHTML += `<span class="trail-stat-badge ${diffClass}">${diffText}</span>`;
            }
            
            // Duration
            if (trail.duration) {
                const hours = Math.floor(trail.duration / 60);
                const mins = trail.duration % 60;
                badgesHTML += `<span class="trail-stat-badge">${hours}:${mins.toString().padStart(2, '0')}</span>`;
            }
            
            // Distance
            if (trail.distance !== undefined && trail.distance !== null) {
                badgesHTML += `<span class="trail-stat-badge">${trail.distance} km</span>`;
            }
            
            // Elevation gain
            if (trail.elevation_gain !== undefined && trail.elevation_gain !== null) {
                badgesHTML += `<span class="trail-stat-badge">${trail.elevation_gain} m</span>`;
            }
            
            // Max elevation
            if (trail.elevation_profile && trail.elevation_profile.length > 0) {
                const maxElevation = Math.max(...trail.elevation_profile.map(p => p.elevation || 0));
                badgesHTML += `<span class="trail-stat-badge">${maxElevation} m</span>`;
            }
            
            statsBadgesEl.innerHTML = badgesHTML;
        }
        
        if (actionButtonsEl) {
            let buttonsHTML = '';
            buttonsHTML += `<button class="trail-action-btn">👍 Like</button>`;
            buttonsHTML += `<button class="trail-action-btn">🔗 Share</button>`;
            buttonsHTML += `<button class="trail-action-btn">💬 Comments</button>`;
            buttonsHTML += `<button class="trail-action-btn primary">🧭 Navigate</button>`;
            buttonsHTML += `<button class="trail-action-btn">✏️ Edit</button>`;
            buttonsHTML += `<button class="trail-action-btn">⋯</button>`;
            actionButtonsEl.innerHTML = buttonsHTML;
        }
    }
    
    function renderImageGallery(trail, photos) {
        const galleryEl = document.getElementById('trail-detail-image-gallery');
        if (!galleryEl) return;
        
        const mainImageEl = document.getElementById('trail-gallery-main-image');
        const thumbnailsEl = document.getElementById('trail-gallery-thumbnails');
        
        if (!mainImageEl || !thumbnailsEl) return;
        
        // Get photos from performance data or use placeholder
        let photoList = [];
        if (photos && photos.length > 0) {
            photoList = photos.map(p => p.path || p);
        } else if (trail.photos && trail.photos.length > 0) {
            photoList = trail.photos.map(p => p.path || p);
        }
        
        // If no photos, hide gallery
        if (photoList.length === 0) {
            galleryEl.style.display = 'none';
            return;
        }
        
        galleryEl.style.display = 'grid';
        let currentIndex = 0;
        
        // Set main image
        function updateMainImage(index) {
            if (photoList[index]) {
                mainImageEl.src = `/static/${photoList[index]}`;
                mainImageEl.alt = `Trail photo ${index + 1}`;
            }
        }
        
        // Render thumbnails (2x2 grid, max 4 visible)
        let thumbnailsHTML = '';
        const visibleThumbnails = Math.min(4, photoList.length);
        for (let i = 0; i < visibleThumbnails; i++) {
            const isLast = i === visibleThumbnails - 1 && photoList.length > 4;
            thumbnailsHTML += `
                <div class="trail-gallery-thumbnail ${i === 0 ? 'active' : ''}" data-index="${i}">
                    <img src="/static/${photoList[i]}" alt="Thumbnail ${i + 1}" />
                    ${isLast ? `<div class="image-count-overlay">+${photoList.length - 4} images</div>` : ''}
                </div>
            `;
        }
        thumbnailsEl.innerHTML = thumbnailsHTML;
        
        // Set initial main image
        updateMainImage(0);
        
        // Thumbnail click handlers
        thumbnailsEl.querySelectorAll('.trail-gallery-thumbnail').forEach((thumb, idx) => {
            thumb.addEventListener('click', () => {
                currentIndex = idx;
                updateMainImage(idx);
                thumbnailsEl.querySelectorAll('.trail-gallery-thumbnail').forEach(t => t.classList.remove('active'));
                thumb.classList.add('active');
            });
        });
        
        // Set initial active thumbnail
        const firstThumb = thumbnailsEl.querySelector('.trail-gallery-thumbnail');
        if (firstThumb) {
            firstThumb.classList.add('active');
        }
        
        // Navigation buttons
        const prevBtn = document.getElementById('gallery-prev');
        const nextBtn = document.getElementById('gallery-next');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                currentIndex = (currentIndex - 1 + photoList.length) % photoList.length;
                updateMainImage(currentIndex);
                thumbnailsEl.querySelectorAll('.trail-gallery-thumbnail').forEach(t => t.classList.remove('active'));
                const thumbIndex = Math.min(currentIndex, 3);
                thumbnailsEl.querySelectorAll('.trail-gallery-thumbnail')[thumbIndex]?.classList.add('active');
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                currentIndex = (currentIndex + 1) % photoList.length;
                updateMainImage(currentIndex);
                thumbnailsEl.querySelectorAll('.trail-gallery-thumbnail').forEach(t => t.classList.remove('active'));
                const thumbIndex = Math.min(currentIndex, 3);
                thumbnailsEl.querySelectorAll('.trail-gallery-thumbnail')[thumbIndex]?.classList.add('active');
            });
        }
    }
    
    function renderMapAndElevation(trail) {
        const mapContainer = document.getElementById('trail-map-container');
        if (!mapContainer) {
            return;
        }
        
        if (!trail.coordinates) {
            mapContainer.innerHTML = '<p>No route data available for this trail.</p>';
        } else {
            // Ensure container has proper dimensions
            if (!mapContainer.style.height) {
                mapContainer.style.height = '500px';
            }
            if (!mapContainer.style.width) {
                mapContainer.style.width = '100%';
            }
            
            mapContainer.innerHTML = '';
            
            // Create unique map ID
            const mapId = 'trail-detail-map-' + Date.now();
            const mapDiv = document.createElement('div');
            mapDiv.id = mapId;
            mapDiv.style.width = '100%';
            mapDiv.style.height = '500px';
            mapContainer.appendChild(mapDiv);
            
            if (typeof MapManager === 'undefined') {
                mapDiv.innerHTML = '<p>Map functionality requires MapManager. Please ensure app.js is loaded.</p>';
                return;
            }
            
            if (typeof L === 'undefined') {
                mapDiv.innerHTML = '<p>Leaflet.js not loaded. Please refresh the page.</p>';
                return;
            }
            
            const mapManager = new MapManager();
            setTimeout(() => {
                try {
                    let coordinates = [];
                    
                    // Parse coordinates from various formats
                    if (typeof trail.coordinates === 'string') {
                        try {
                            const geoJson = JSON.parse(trail.coordinates);
                            if (geoJson.type === 'LineString' && geoJson.coordinates && Array.isArray(geoJson.coordinates)) {
                                coordinates = geoJson.coordinates.map(coord => [coord[1], coord[0]]);
                            }
                        } catch (e) {
                            console.warn('Could not parse coordinates as GeoJSON string:', e);
                        }
                    } else if (trail.coordinates && typeof trail.coordinates === 'object') {
                        // Already parsed GeoJSON object
                        if (trail.coordinates.type === 'LineString' && trail.coordinates.coordinates && Array.isArray(trail.coordinates.coordinates)) {
                            coordinates = trail.coordinates.coordinates.map(coord => [coord[1], coord[0]]);
                        } else if (Array.isArray(trail.coordinates)) {
                            // Already an array of [lat, lng] pairs
                            coordinates = trail.coordinates;
                        }
                    }
                    
                    if (coordinates.length === 0) {
                        mapDiv.innerHTML = '<p>No route data available</p>';
                        return;
                    }
                    
                    const center = coordinates[Math.floor(coordinates.length / 2)];
                    const map = mapManager.initMap(mapId, {
                        zoom: 10,
                        center: center
                    });
                    
                    if (!map) {
                        mapDiv.innerHTML = '<p>Failed to initialize map</p>';
                        return;
                    }
                    
                    // Add trail polyline
                    const polyline = L.polyline(coordinates, {
                        color: '#6366f1',
                        weight: 4,
                        opacity: 0.8
                    }).addTo(map);
                    
                    // Add start marker
                    L.marker(coordinates[0], {
                        icon: L.divIcon({
                            className: 'trail-start-marker',
                            html: '<div style="background: #10b981; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-weight: bold;">S</div>',
                            iconSize: [24, 24]
                        })
                    }).addTo(map).bindPopup('Start');
                    
                    // Add end marker
                    L.marker(coordinates[coordinates.length - 1], {
                        icon: L.divIcon({
                            className: 'trail-end-marker',
                            html: '<div style="background: #ef4444; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-weight: bold;">E</div>',
                            iconSize: [24, 24]
                        })
                    }).addTo(map).bindPopup('End');
                    
                    map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
                } catch (e) {
                    mapDiv.innerHTML = '<p>Error loading map: ' + escapeHtml(e.message) + '</p>';
                }
            }, 300);
        }
        
        const elevationSection = document.querySelector('.trail-elevation-section');
        if (!elevationSection) {
            return;
        }
        
        if (!trail.elevation_profile || !Array.isArray(trail.elevation_profile) || trail.elevation_profile.length === 0) {
            const elevationSummary = elevationSection.querySelector('#elevation-summary');
            if (elevationSummary) {
                elevationSummary.innerHTML = '<p>No elevation profile data available for this trail.</p>';
            }
        } else {
            const elevationSummary = elevationSection.querySelector('#elevation-summary');
            if (elevationSummary) {
                try {
                    const elevations = trail.elevation_profile.map(p => {
                        if (typeof p === 'object' && p !== null) {
                            return p.elevation || p.elevation_m || 0;
                        }
                        return 0;
                    });
                    
                    const maxElevation = Math.max(...elevations);
                    const minElevation = Math.min(...elevations);
                    const elevationGain = maxElevation - minElevation;
                    
                    elevationSummary.innerHTML = `
                        <div class="elevation-summary-cards">
                            <div class="elevation-card">
                                <span class="elevation-label">Max Elevation</span>
                                <span class="elevation-value">${maxElevation}m</span>
                            </div>
                            <div class="elevation-card">
                                <span class="elevation-label">Elevation Gain</span>
                                <span class="elevation-value">${elevationGain}m</span>
                            </div>
                            <div class="elevation-card">
                                <span class="elevation-label">Min Elevation</span>
                                <span class="elevation-value">${minElevation}m</span>
                            </div>
                        </div>
                    `;
                } catch (e) {
                    elevationSummary.innerHTML = '<p>Error calculating elevation statistics</p>';
                }
            }
            
            const chartContainer = elevationSection.querySelector('.chart-container');
            if (chartContainer) {
                let canvas = chartContainer.querySelector('#elevation-chart');
                if (!canvas) {
                    canvas = document.createElement('canvas');
                    canvas.id = 'elevation-chart';
                    chartContainer.appendChild(canvas);
                }
                
                // Ensure canvas has proper dimensions
                if (!canvas.style.width) {
                    canvas.style.width = '100%';
                }
                if (!canvas.style.height) {
                    canvas.style.height = '300px';
                }
                
                setTimeout(() => {
                    if (typeof Chart === 'undefined') {
                        canvas.parentElement.innerHTML = '<p>Chart.js library not loaded. Please refresh the page.</p>';
                        return;
                    }
                    
                    if (!canvas) {
                        return;
                    }
                    
                    try {
                        if (canvas.chart) {
                            canvas.chart.destroy();
                        }
                        
                        const ctx = canvas.getContext('2d');
                        if (!ctx) {
                            return;
                        }
                        
                        // Extract elevation data
                        const elevationData = trail.elevation_profile.map(p => {
                            if (typeof p === 'object' && p !== null) {
                                return p.elevation || p.elevation_m || 0;
                            }
                            return 0;
                        });
                        
                        // Calculate distance data
                        let distanceData = [];
                        if (trail.elevation_profile[0] && trail.elevation_profile[0].distance_m !== undefined) {
                            // Use distance_m from elevation profile if available
                            distanceData = trail.elevation_profile.map(p => (p.distance_m || 0) / 1000); // Convert to km
                        } else if (trail.distance) {
                            // Calculate evenly spaced distances
                            distanceData = trail.elevation_profile.map((p, i) => {
                                return (i / trail.elevation_profile.length) * trail.distance;
                            });
                        } else {
                            // Fallback: use index as distance
                            distanceData = trail.elevation_profile.map((p, i) => i);
                        }
                        
                        // Create labels (show only some to avoid clutter)
                        const labelInterval = Math.max(1, Math.floor(distanceData.length / 10));
                        const labels = distanceData.map((d, i) => 
                            (i === 0 || i === distanceData.length - 1 || i % labelInterval === 0) 
                                ? d.toFixed(1) + ' km' 
                                : ''
                        );
                        
                        canvas.chart = new Chart(ctx, {
                            type: 'line',
                            data: {
                                labels: labels,
                                datasets: [{
                                    label: 'Elevation (m)',
                                    data: elevationData,
                                    borderColor: 'rgb(99, 102, 241)',
                                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                                    fill: true,
                                    tension: 0.4,
                                    pointRadius: 0
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    title: {
                                        display: true,
                                        text: 'Elevation Profile'
                                    },
                                    legend: {
                                        display: true
                                    }
                                },
                                scales: {
                                    x: {
                                        title: {
                                            display: true,
                                            text: 'Distance (km)'
                                        },
                                        grid: {
                                            display: true
                                        }
                                    },
                                    y: {
                                        title: {
                                            display: true,
                                            text: 'Elevation (m)'
                                        },
                                        grid: {
                                            display: true
                                        }
                                    }
                                }
                            }
                        });
                    } catch (e) {
                        canvas.parentElement.innerHTML = '<p>Error creating elevation chart: ' + escapeHtml(e.message) + '</p>';
                    }
                }, 300);
            }
        }
    }
    
    function renderOverviewSection(trail) {
        const overviewSection = document.getElementById('trail-overview-section');
        if (!overviewSection) {
            return;
        }
        
        const descSummary = overviewSection.querySelector('#trail-description-summary');
        const keyStatsGrid = overviewSection.querySelector('#trail-key-stats-grid');
        const landscapesSummary = overviewSection.querySelector('#trail-landscapes-summary');
        const fullDescContent = overviewSection.querySelector('#trail-description-full');
        const detailsExpanded = overviewSection.querySelector('#trail-details-expanded');
        
        if (descSummary) {
            const firstParagraph = trail.description ? trail.description.split('\n')[0] : 'No description available';
            descSummary.innerHTML = `<p class="trail-description-summary">${escapeHtml(firstParagraph)}</p>`;
        }
        
        if (keyStatsGrid) {
            const distance = trail.distance !== undefined && trail.distance !== null ? trail.distance : 'N/A';
            const elevation = trail.elevation_gain !== undefined && trail.elevation_gain !== null ? trail.elevation_gain : 'N/A';
            const difficulty = trail.difficulty !== undefined && trail.difficulty !== null ? trail.difficulty : 'N/A';
            const trailType = trail.trail_type || 'N/A';
            const durationHtml = trail.duration ? `<div class="key-stat"><span class="key-stat-label">Duration</span><span class="key-stat-value">${Math.floor(trail.duration / 60)}h ${trail.duration % 60}m</span></div>` : '';
            
            keyStatsGrid.innerHTML = `
                <div class="key-stats-grid">
                    <div class="key-stat"><span class="key-stat-label">Distance</span><span class="key-stat-value">${distance}${distance !== 'N/A' ? ' km' : ''}</span></div>
                    <div class="key-stat"><span class="key-stat-label">Elevation</span><span class="key-stat-value">${elevation}${elevation !== 'N/A' ? 'm' : ''}</span></div>
                    <div class="key-stat"><span class="key-stat-label">Difficulty</span><span class="key-stat-value">${difficulty}${difficulty !== 'N/A' ? '/10' : ''}</span></div>
                    <div class="key-stat"><span class="key-stat-label">Type</span><span class="key-stat-value">${escapeHtml(trailType)}</span></div>
                    ${durationHtml}
                </div>
            `;
        }
        
        if (landscapesSummary) {
            if (trail.landscapes) {
                const landscapeTags = trail.landscapes.split(',').map(l => l.trim()).filter(l => l);
                landscapesSummary.innerHTML = `
                    <div class="landscape-tags">
                        ${landscapeTags.map(tag => `<span class="landscape-tag">${escapeHtml(tag)}</span>`).join('')}
                    </div>
                `;
            } else {
                landscapesSummary.innerHTML = '';
            }
        }
        
        if (fullDescContent) {
            if (trail.description) {
                fullDescContent.innerHTML = `<p>${escapeHtml(trail.description).replace(/\n/g, '</p><p>')}</p>`;
            } else {
                fullDescContent.innerHTML = '<p>No description available for this trail.</p>';
            }
        }
        
        if (detailsExpanded) {
            let detailsHTML = '<div class="trail-details-expanded-grid">';
            if (trail.region) detailsHTML += `<div><strong>Region:</strong> ${escapeHtml(trail.region)}</div>`;
            if (trail.popularity !== undefined && trail.popularity !== null) detailsHTML += `<div><strong>Popularity:</strong> ${trail.popularity}/100</div>`;
            if (trail.safety_risks) detailsHTML += `<div><strong>Safety:</strong> ${escapeHtml(trail.safety_risks)}</div>`;
            if (trail.accessibility) detailsHTML += `<div><strong>Accessibility:</strong> ${escapeHtml(trail.accessibility)}</div>`;
            if (trail.closed_seasons) detailsHTML += `<div><strong>Closed Seasons:</strong> ${escapeHtml(trail.closed_seasons)}</div>`;
            detailsHTML += '</div>';
            detailsExpanded.innerHTML = detailsHTML;
        }
    }
    
    function renderPerformanceSection(performance, showPredicted = false) {
        const performanceSection = document.getElementById('trail-performance-section');
        if (!performanceSection) {
            return;
        }
        
        // Handle both data structures: {completed: true, performance: {...}} or direct performance object
        let perf = null;
        if (performance && performance.completed && performance.performance) {
            perf = performance.performance;
        } else if (performance && performance.completed) {
            perf = performance;
        } else if (performance && !performance.completed) {
            const summaryCards = performanceSection.querySelector('#performance-summary-cards');
            if (summaryCards) {
                summaryCards.innerHTML = '<p>No performance data available. Complete this trail to see your metrics.</p>';
            }
            return;
        } else {
            const summaryCards = performanceSection.querySelector('#performance-summary-cards');
            if (summaryCards) {
                summaryCards.innerHTML = '<p>No performance data available. Complete this trail to see your metrics.</p>';
            }
            return;
        }
        
        if (perf) {
            // Summary cards (always visible)
            const summaryCards = performanceSection.querySelector('#performance-summary-cards');
            if (summaryCards) {
                let summaryHTML = '<div class="performance-summary-grid">';
                
                // Show predicted or actual duration
                const duration = showPredicted ? perf.predicted_duration : perf.actual_duration;
                if (duration !== undefined && duration !== null) {
                    const hours = Math.floor(duration / 60);
                    const minutes = duration % 60;
                    summaryHTML += `<div class="performance-summary-card"><span class="summary-label">Duration</span><span class="summary-value">${hours}h ${minutes}m</span></div>`;
                }
                
                if (perf.rating !== undefined && perf.rating !== null && !showPredicted) {
                    summaryHTML += `<div class="performance-summary-card"><span class="summary-label">Rating</span><span class="summary-value">${perf.rating.toFixed(1)}/5 ⭐</span></div>`;
                }
                
                // Show predicted or actual heart rate
                const avgHeartRate = showPredicted ? perf.predicted_avg_heart_rate : perf.avg_heart_rate;
                if (avgHeartRate !== undefined && avgHeartRate !== null) {
                    summaryHTML += `<div class="performance-summary-card"><span class="summary-label">Avg Heart Rate</span><span class="summary-value">${avgHeartRate} bpm</span></div>`;
                }
                
                if (perf.difficulty_rating !== undefined && perf.difficulty_rating !== null) {
                    summaryHTML += `<div class="performance-summary-card"><span class="summary-label">Difficulty</span><span class="summary-value">${perf.difficulty_rating}/10</span></div>`;
                }
                
                summaryHTML += '</div>';
                summaryCards.innerHTML = summaryHTML;
            }
            
            // Detailed metrics (always visible)
            const detailedMetrics = performanceSection.querySelector('#performance-metrics-detailed');
            if (detailedMetrics) {
                let html = '<div class="performance-metrics-grid">';
                let hasMetrics = false;
                
                if (perf.completion_date) {
                    html += `<div class="metric-item"><strong>Completed:</strong> ${new Date(perf.completion_date).toLocaleDateString()}</div>`;
                    hasMetrics = true;
                }
                
                if (perf.difficulty_rating !== undefined && perf.difficulty_rating !== null) {
                    html += `<div class="metric-item"><strong>Difficulty Rating:</strong> ${perf.difficulty_rating}/10</div>`;
                    hasMetrics = true;
                }
                
                // Show predicted or actual metrics
                const maxHeartRate = showPredicted ? perf.predicted_max_heart_rate : perf.max_heart_rate;
                if (maxHeartRate !== undefined && maxHeartRate !== null) {
                    html += `<div class="metric-item"><strong>Max Heart Rate:</strong> ${maxHeartRate} bpm</div>`;
                    hasMetrics = true;
                }
                
                const avgHeartRate = showPredicted ? perf.predicted_avg_heart_rate : perf.avg_heart_rate;
                if (avgHeartRate !== undefined && avgHeartRate !== null) {
                    html += `<div class="metric-item"><strong>Avg Heart Rate:</strong> ${avgHeartRate} bpm</div>`;
                    hasMetrics = true;
                }
                
                const avgSpeed = showPredicted ? perf.predicted_avg_speed : perf.avg_speed;
                if (avgSpeed !== undefined && avgSpeed !== null) {
                    html += `<div class="metric-item"><strong>Avg Speed:</strong> ${avgSpeed.toFixed(2)} km/h</div>`;
                    hasMetrics = true;
                }
                
                const maxSpeed = showPredicted ? perf.predicted_max_speed : perf.max_speed;
                if (maxSpeed !== undefined && maxSpeed !== null) {
                    html += `<div class="metric-item"><strong>Max Speed:</strong> ${maxSpeed.toFixed(2)} km/h</div>`;
                    hasMetrics = true;
                }
                
                if (perf.photos && perf.photos.length > 0) {
                    html += `<div class="metric-item"><strong>Photos:</strong> ${perf.photos.length} photo(s)</div>`;
                    hasMetrics = true;
                }
                
                html += '</div>';
                
                // If no additional metrics beyond completion date, show a helpful message
                if (!hasMetrics && perf.completion_date) {
                    html += '<p class="text-muted" style="margin-top: var(--space-md);">Upload smartwatch data or complete more trails to see detailed performance metrics.</p>';
                }
                
                detailedMetrics.innerHTML = html;
            }
            
            // Performance chart (only if time series data exists)
            const chartContainer = performanceSection.querySelector('.chart-container');
            const canvas = performanceSection.querySelector('#performance-chart');
            if (chartContainer && canvas) {
                if (perf.time_series && perf.time_series.length > 0) {
                    setTimeout(() => {
                        renderPerformanceChart(perf.time_series);
                    }, 100);
                } else {
                    // Hide chart container if no time series data
                    chartContainer.style.display = 'none';
                }
            }
        }
    }
    
    function renderWeatherSection(weather) {
        const weatherSection = document.getElementById('trail-weather-section');
        if (!weatherSection) {
            return;
        }
        
        // Hide/remove the full forecast section
        const fullForecast = weatherSection.querySelector('#weather-forecast-full');
        if (fullForecast) {
            fullForecast.style.display = 'none';
            fullForecast.innerHTML = '';
        }
        
        if (weather && weather.forecast && weather.forecast.length > 0) {
            // Summary cards (today + next 3 days) - keep only the 4 cards
            const summaryCards = weatherSection.querySelector('#weather-summary-cards');
            if (summaryCards) {
                const todayPlus3 = weather.forecast.slice(0, 4);
                let summaryHTML = '<div class="weather-summary-grid">';
                todayPlus3.forEach(day => {
                    const date = new Date(day.date);
                    const isToday = date.toDateString() === new Date().toDateString();
                    const weatherIcon = getWeatherIcon(day.weather || '');
                    summaryHTML += `
                        <div class="weather-summary-card ${isToday ? 'weather-today' : ''}">
                            <div class="weather-date">${isToday ? 'Today' : date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</div>
                            <div class="weather-icon">${weatherIcon}</div>
                            <div class="weather-condition">${escapeHtml(day.weather || 'N/A')}</div>
                            ${day.temperature ? `<div class="weather-temp">${day.temperature}°C</div>` : ''}
                        </div>
                    `;
                });
                summaryHTML += '</div>';
                summaryCards.innerHTML = summaryHTML;
            }
        } else {
            const summaryCards = weatherSection.querySelector('#weather-summary-cards');
            if (summaryCards) {
                summaryCards.innerHTML = '<p>No weather forecast available</p>';
            }
        }
    }
    
    function getWeatherIcon(weather) {
        const w = weather.toLowerCase();
        if (w.includes('sun') || w.includes('clear')) return '☀️';
        if (w.includes('cloud')) return '☁️';
        if (w.includes('rain')) return '🌧️';
        if (w.includes('snow')) return '❄️';
        if (w.includes('storm')) return '⛈️';
        if (w.includes('wind')) return '💨';
        return '🌤️';
    }
    
    function renderRecommendationsSection(recommendations) {
        const recommendationsSection = document.getElementById('trail-recommendations-section');
        if (!recommendationsSection) {
            console.error('Recommendations section element not found');
            return;
        }
        
        if (recommendations) {
            // Key tips (always visible - top 3-5)
            const keyTips = recommendationsSection.querySelector('#recommendations-key-tips');
            if (keyTips) {
                let tipsHTML = '<div class="key-tips-section"><h4>Key Tips</h4><ul class="key-tips-list">';
                
                // Get tips from profile_recommendations or ai_explanation
                let tips = [];
                if (recommendations.profile_recommendations && recommendations.profile_recommendations.tips) {
                    tips = recommendations.profile_recommendations.tips;
                } else if (recommendations.ai_explanation && recommendations.ai_explanation.key_factors) {
                    tips = recommendations.ai_explanation.key_factors;
                }
                
                // Show top 5 tips
                tips.slice(0, 5).forEach(tip => {
                    tipsHTML += `<li class="key-tip-item">${escapeHtml(tip)}</li>`;
                });
                
                tipsHTML += '</ul></div>';
                keyTips.innerHTML = tipsHTML;
            }
            
            // Full recommendations (always visible)
            const fullRecommendations = recommendationsSection.querySelector('#ai-recommendations-full');
            if (fullRecommendations) {
                let html = '';
                let hasContent = false;
                
                if (recommendations.ai_explanation && recommendations.ai_explanation.explanation_text) {
                    html += `<div class="ai-explanation-full"><h5>Full Explanation</h5><p>${escapeHtml(recommendations.ai_explanation.explanation_text)}</p></div>`;
                    hasContent = true;
                }
                
                if (recommendations.ai_explanation && recommendations.ai_explanation.key_factors && recommendations.ai_explanation.key_factors.length > 0) {
                    html += '<div class="key-factors-section"><h5>Key Factors</h5><ul>';
                    recommendations.ai_explanation.key_factors.forEach(factor => {
                        html += `<li>${escapeHtml(factor)}</li>`;
                    });
                    html += '</ul></div>';
                    hasContent = true;
                }
                
                if (recommendations.profile_recommendations && recommendations.profile_recommendations.tips && recommendations.profile_recommendations.tips.length > 0) {
                    html += '<div class="all-tips-section"><h5>All Tips</h5><ul>';
                    recommendations.profile_recommendations.tips.forEach(tip => {
                        html += `<li>${escapeHtml(tip)}</li>`;
                    });
                    html += '</ul></div>';
                    hasContent = true;
                }
                
                if (recommendations.performance_tips && recommendations.performance_tips.length > 0) {
                    html += '<div class="performance-tips-section"><h5>Performance Tips</h5><ul>';
                    recommendations.performance_tips.forEach(tip => {
                        html += `<li>${escapeHtml(tip)}</li>`;
                    });
                    html += '</ul></div>';
                    hasContent = true;
                }
                
                if (recommendations.safety_tips && recommendations.safety_tips.length > 0) {
                    html += '<div class="safety-tips-section"><h5>Safety Tips</h5><ul>';
                    recommendations.safety_tips.forEach(tip => {
                        html += `<li>${escapeHtml(tip)}</li>`;
                    });
                    html += '</ul></div>';
                    hasContent = true;
                }
                
                if (recommendations.weather_recommendations && recommendations.weather_recommendations.tips && recommendations.weather_recommendations.tips.length > 0) {
                    html += '<div class="weather-tips-section"><h5>Weather Tips</h5><ul>';
                    recommendations.weather_recommendations.tips.forEach(tip => {
                        html += `<li>${escapeHtml(tip)}</li>`;
                    });
                    html += '</ul></div>';
                    hasContent = true;
                }
                
                if (!hasContent) {
                    html = '<p class="text-muted">Complete this trail to see personalized recommendations based on your performance and profile.</p>';
                }
                
                fullRecommendations.innerHTML = html;
            }
        } else {
            const keyTips = recommendationsSection.querySelector('#recommendations-key-tips');
            if (keyTips) {
                keyTips.innerHTML = '<p>No recommendations available</p>';
            }
        }
    }
    
    function getMetricLabel(metric) {
        const labels = {
            'heart_rate': 'Heart Rate (bpm)',
            'speed': 'Speed (km/h)',
            'calories': 'Calories',
            'cadence': 'Cadence (steps/min)'
        };
        return labels[metric] || metric;
    }
    
    function getMetricColor(metric) {
        const colors = {
            'heart_rate': 'rgb(239, 68, 68)',
            'speed': 'rgb(59, 130, 246)',
            'calories': 'rgb(34, 197, 94)',
            'cadence': 'rgb(168, 85, 247)'
        };
        return colors[metric] || 'rgb(100, 100, 100)';
    }
    
    function generateCompletionColor(index) {
        const colors = [
            'rgb(239, 68, 68)',   // Red
            'rgb(59, 130, 246)',  // Blue
            'rgb(34, 197, 94)',    // Green
            'rgb(168, 85, 247)',  // Purple
            'rgb(245, 158, 11)',   // Orange
            'rgb(236, 72, 153)',   // Pink
            'rgb(14, 165, 233)',   // Cyan
            'rgb(251, 146, 60)'    // Orange-red
        ];
        return colors[index % colors.length];
    }
    
    function normalizeTimeSeries(timeSeries) {
        // Normalize timestamps to start from 0 and convert to minutes
        if (!timeSeries || timeSeries.length === 0) return [];
        const startTime = timeSeries[0].timestamp || 0;
        return timeSeries.map(p => ({
            ...p,
            timeMinutes: ((p.timestamp || 0) - startTime) / 60
        })).filter(p => p.timeMinutes !== null && p.timeMinutes !== undefined); // Filter out invalid points
    }
    
    function renderPerformanceChart() {
        const canvas = document.getElementById('performance-chart');
        if (!canvas || typeof Chart === 'undefined') return;
        
        // Destroy existing chart
        if (performanceChart) {
            performanceChart.destroy();
            performanceChart = null;
        }
        
        // Get all loaded completions
        const completionEntries = Object.values(loadedCompletions);
        
        if (completionEntries.length === 0) {
            canvas.parentElement.style.display = 'none';
            return;
        }
        
        canvas.parentElement.style.display = 'block';
        
        // Normalize all time series to start from 0
        const normalizedCompletions = completionEntries.map(comp => ({
            ...comp,
            normalizedData: normalizeTimeSeries(comp.data.time_series || [])
        })).filter(comp => comp.normalizedData.length > 0); // Filter out empty data
        
        if (normalizedCompletions.length === 0) {
            canvas.parentElement.style.display = 'none';
            return;
        }
        
        // Find max duration for x-axis
        const maxDuration = Math.max(...normalizedCompletions.map(c => {
            const data = c.normalizedData;
            return data.length > 0 ? data[data.length - 1].timeMinutes : 0;
        }));
        
        // Create labels (time in minutes, every 10 minutes or so)
        const labelStep = Math.max(10, Math.floor(maxDuration / 10));
        const labels = [];
        for (let i = 0; i <= maxDuration; i += labelStep) {
            const hours = Math.floor(i / 60);
            const mins = Math.floor(i % 60);
            labels.push(`${hours}:${mins.toString().padStart(2, '0')}`);
        }
        
        const datasets = [];
        
        // Add completion datasets
        normalizedCompletions.forEach((comp, index) => {
            const timeSeries = comp.normalizedData;
            if (timeSeries.length === 0) return;
            
            const metricData = timeSeries.map(p => ({
                x: p.timeMinutes,
                y: p[currentMetric] || 0
            }));
            
            const date = new Date(comp.data.completion_date);
            const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const label = comp.isPredicted ? 
                `Predicted ${getMetricLabel(currentMetric)}` : 
                `Actual ${getMetricLabel(currentMetric)} - ${dateStr}`;
            
            datasets.push({
                label: label,
                data: metricData,
                borderColor: comp.color,
                backgroundColor: comp.color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
                fill: false,
                tension: 0.4,
                yAxisID: 'y',
                order: comp.isPredicted ? 0 : 1, // Predicted behind actual
                pointRadius: 0,
                borderWidth: comp.isPredicted ? 1.5 : 2,
                borderDash: comp.isPredicted ? [5, 5] : [] // Dashed line for predicted
            });
        });
        
        const ctx = canvas.getContext('2d');
        performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    title: {
                        display: true,
                        text: `${getMetricLabel(currentMetric)}: Actual vs Predicted`
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y.toFixed(1);
                                    if (currentMetric === 'heart_rate') label += ' bpm';
                                    else if (currentMetric === 'speed') label += ' km/h';
                                    else if (currentMetric === 'cadence') label += ' steps/min';
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: {
                            display: true,
                            text: 'Time (minutes)'
                        },
                        min: 0,
                        max: maxDuration
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: getMetricLabel(currentMetric)
                        },
                        grid: {
                            drawOnChartArea: true
                        }
                    },
                }
            }
        });
    }
    
    function updateCompletionLegend() {
        const legendContainer = document.getElementById('loaded-completions-legend');
        if (!legendContainer) return;
        
        const completionEntries = Object.values(loadedCompletions);
        if (completionEntries.length === 0) {
            legendContainer.innerHTML = '';
            return;
        }
        
        let html = '<div style="font-weight: 600; margin-right: 0.5rem;">Comparison:</div>';
        const completionIds = Object.keys(loadedCompletions);
        completionEntries.forEach((comp, index) => {
            const completionId = comp.data.id || completionIds[index];
            const label = comp.isPredicted ? 'Predicted' : 
                new Date(comp.data.completion_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            html += `
                <div style="display: flex; align-items: center; gap: 0.5rem;" data-completion-id="${completionId}">
                    <div style="width: 20px; height: 3px; background-color: ${comp.color}; ${comp.isPredicted ? 'border-top: 1px dashed rgba(150,150,150,0.5);' : ''}"></div>
                    <span style="font-size: 0.9rem;">${label}</span>
                </div>
            `;
        });
        
        legendContainer.innerHTML = html;
    }
    
    function addCompletionToChart(completionData, completionId, isPredicted = false) {
        // Use a unique ID for predicted vs actual
        const uniqueId = isPredicted ? 'predicted' : (completionData.id || completionId || 'actual');
        
        // Always allow adding predicted, and allow replacing actual if needed
        if (loadedCompletions[uniqueId] && !isPredicted && uniqueId !== 'actual') {
            // Don't add duplicate actual completions (but allow predicted)
            return;
        }
        
        const date = new Date(completionData.completion_date || new Date().toISOString());
        const index = Object.keys(loadedCompletions).length;
        // Predicted always gets grey, actual gets colored
        const color = isPredicted ? 'rgba(150, 150, 150, 0.8)' : generateCompletionColor(0);
        
        loadedCompletions[uniqueId] = {
            data: completionData,
            date: date,
            color: color,
            isPredicted: isPredicted
        };
        
        updateCompletionLegend();
        // Use setTimeout to batch chart updates
        if (window._chartUpdateTimeout) {
            clearTimeout(window._chartUpdateTimeout);
        }
        window._chartUpdateTimeout = setTimeout(() => {
            renderPerformanceChart();
        }, 50);
    }
    
    function removeCompletion(completionId) {
        delete loadedCompletions[completionId];
        updateCompletionLegend();
        renderPerformanceChart();
    }
    
    function loadCompletionsList(trailId, userId) {
        return fetch(`/api/profile/${userId}/trail/${trailId}/completions`)
            .then(r => {
                if (!r.ok) {
                    console.warn('Completions API returned', r.status);
                    return { completions: [] };
                }
                return r.json();
            })
            .catch(e => {
                console.warn('Error loading completions:', e);
                return { completions: [] };
            });
    }
    
    function loadCompletionPerformance(trailId, userId, completionId) {
        const url = `/api/profile/${userId}/trail/${trailId}/performance${completionId ? `?completion_id=${completionId}` : ''}`;
        return fetch(url)
            .then(r => {
                if (!r.ok) {
                    console.warn('Performance API returned', r.status);
                    return { completed: false };
                }
                return r.json();
            })
            .catch(e => {
                console.warn('Error loading performance:', e);
                return { completed: false };
            });
    }
    
    function renderPerformanceVisualizations(performanceData, showPredicted = false) {
        if (!performanceData || !performanceData.completed) {
            return;
        }
        
        const perf = performanceData.performance;
        
        // Clear previous completions - only show one at a time (actual vs predicted)
        loadedCompletions = {};
        
        // When showing actual completion, always show both actual and predicted lines for comparison
        if (!showPredicted && perf.time_series && perf.time_series.length > 0) {
            // Generate predicted time series FIRST (before adding actual)
            // Use predicted metrics if available, otherwise generate from actual data
            const predictedTimeSeries = generatePredictedTimeSeries(perf);
            
            // Prepare both completions before adding to avoid race conditions
            const completionId = perf.id || 'actual';
            const predictedData = predictedTimeSeries && predictedTimeSeries.length > 0 ? {
                ...perf,
                time_series: predictedTimeSeries,
                completion_date: perf.completion_date || new Date().toISOString(),
                id: 'predicted' // Use unique ID so it doesn't conflict with actual
            } : null;
            
            // Add actual completion data
            addCompletionToChart(perf, completionId, false); // false = actual data
            
            // Always add predicted line if we have predicted time series
            if (predictedData) {
                addCompletionToChart(predictedData, 'predicted', true); // true = predicted data
            }
            
            // Render GPS route overlay on map if GPS data available
            if (perf.time_series.some(p => p.latitude && p.longitude)) {
                renderGPSRouteOnMap(perf.time_series);
            }
        } else if (showPredicted) {
            // When showing predicted only, generate predicted time series and show it
            // Generate predicted time series even if no actual time series exists
            const predictedTimeSeries = generatePredictedTimeSeries(perf);
            if (predictedTimeSeries && predictedTimeSeries.length > 0) {
                addCompletionToChart({
                    ...perf,
                    time_series: predictedTimeSeries,
                    completion_date: perf.completion_date || new Date().toISOString()
                }, 'predicted', true); // true = predicted data
            }
        }
        
        // Render comparison with predicted metrics if available (only when showing actual)
        if (!showPredicted && (perf.predicted_avg_heart_rate || perf.predicted_duration || perf.predicted_avg_speed)) {
            renderPredictedComparison(perf, showPredicted);
        }
    }
    
    function generatePredictedTimeSeries(perf) {
        // Generate predicted time series based on predicted metrics
        // Use actual time series structure if available, otherwise generate from predicted duration
        const predictedDuration = perf.predicted_duration || perf.actual_duration || 120;
        const predictedAvgHR = perf.predicted_avg_heart_rate || perf.avg_heart_rate || 140;
        const predictedMaxHR = perf.predicted_max_heart_rate || perf.max_heart_rate || predictedAvgHR * 1.2;
        const predictedAvgSpeed = perf.predicted_avg_speed || perf.avg_speed || 4.0;
        const predictedMaxSpeed = perf.predicted_max_speed || perf.max_speed || predictedAvgSpeed * 1.3;
        
        // Determine interval and number of points
        let interval = 60; // Default: 1 point per minute (60 seconds)
        let numPoints = Math.max(predictedDuration, 10); // At least 10 points, or one per minute
        
        if (perf.time_series && perf.time_series.length > 0) {
            // Use same time intervals as actual data for better comparison
            const lastTimestamp = perf.time_series[perf.time_series.length - 1].timestamp;
            const firstTimestamp = perf.time_series[0].timestamp;
            const actualDuration = lastTimestamp - firstTimestamp;
            if (actualDuration > 0 && perf.time_series.length > 0) {
                interval = actualDuration / perf.time_series.length;
                numPoints = Math.floor((predictedDuration * 60) / interval);
                if (numPoints === 0 || numPoints < 10) {
                    // Fallback: use actual data point count if predicted duration is similar or too few points
                    numPoints = perf.time_series.length;
                    interval = (predictedDuration * 60) / numPoints;
                }
            } else {
                // If timestamps are invalid, use actual data point count
                numPoints = perf.time_series.length;
                interval = (predictedDuration * 60) / numPoints;
            }
        }
        
        // Ensure we have at least some points
        if (numPoints === 0) {
            numPoints = Math.max(10, predictedDuration);
            interval = 60;
        }
        
        const predictedSeries = [];
        
        for (let i = 0; i < numPoints; i++) {
            const timestamp = i * interval;
            const progress = numPoints > 1 ? i / (numPoints - 1) : 0;
            
            // Heart rate: starts lower, peaks in middle, decreases slightly at end
            const hrProgression = progress * (1.2 - progress * 0.4);
            const heartRate = Math.round(predictedAvgHR * (0.7 + hrProgression * 0.6));
            
            // Speed: relatively constant with small variations around predicted average
            const speedVariation = 0.9 + (Math.sin(progress * Math.PI * 2) * 0.1); // Smooth variation
            const speed = predictedAvgSpeed * speedVariation;
            
            // Cadence: relatively constant
            const cadence = 120;
            
            predictedSeries.push({
                timestamp: timestamp,
                heart_rate: Math.min(predictedMaxHR, Math.max(60, heartRate)),
                speed: Math.max(1.0, Math.min(predictedMaxSpeed || 10.0, speed)),
                calories: 0,
                cadence: cadence
            });
        }
        
        return predictedSeries.length > 0 ? predictedSeries : null;
    }
    
    function renderGPSRouteOnMap(timeSeries) {
        const mapContainer = document.getElementById('trail-map-container');
        if (!mapContainer || typeof L === 'undefined') return;
        
        // Get GPS points
        const gpsPoints = timeSeries
            .filter(p => p.latitude && p.longitude)
            .map(p => [p.latitude, p.longitude]);
        
        if (gpsPoints.length === 0) return;
        
        // Check if map already exists
        let map = mapContainer._map;
        if (!map) {
            // Map should already be initialized by renderMapAndElevation
            return;
        }
        
        // Add GPS route polyline
        if (map._gpsRoute) {
            map.removeLayer(map._gpsRoute);
        }
        
        const gpsRoute = L.polyline(gpsPoints, {
            color: '#3b82f6',
            weight: 4,
            opacity: 0.8
        }).addTo(map);
        
        map._gpsRoute = gpsRoute;
        
        // Fit bounds to include GPS route
        if (gpsPoints.length > 0) {
            map.fitBounds(gpsRoute.getBounds(), { padding: [20, 20] });
        }
    }
    
    function renderSpeedElevationCharts(timeSeries) {
        // This could be enhanced to show speed and elevation charts separately
        // For now, we'll add elevation to the existing performance chart if Chart.js supports multiple datasets
        const canvas = document.getElementById('performance-chart');
        if (!canvas || !canvas.chart || typeof Chart === 'undefined') return;
        
        const chart = canvas.chart;
        
        // Add elevation dataset if not already present
        if (chart.data.datasets.length === 1 && timeSeries.some(p => p.elevation)) {
            chart.data.datasets.push({
                label: 'Elevation (m)',
                data: timeSeries.map(p => p.elevation || 0),
                borderColor: 'rgb(34, 197, 94)',
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                fill: true,
                tension: 0.4,
                yAxisID: 'y1'
            });
            
            chart.options.scales.y1 = {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                    display: true,
                    text: 'Elevation (m)'
                },
                grid: {
                    drawOnChartArea: false
                }
            };
            
            chart.update();
        }
    }
    
    function renderPredictedComparison(perf, showPredicted = false) {
        // Only show comparison when viewing actual completion (not when viewing predicted only)
        if (showPredicted) return;
        
        const detailedMetrics = document.getElementById('performance-metrics-detailed');
        if (!detailedMetrics) return;
        
        // Check if comparison section already exists and remove it
        const existingComparison = detailedMetrics.querySelector('.predicted-comparison');
        if (existingComparison) {
            existingComparison.remove();
        }
        
        let comparisonHTML = '<div class="predicted-comparison" style="margin-top: 1.5rem; padding: 1rem; background: #f3f4f6; border-radius: 8px;"><h5>Predicted vs Actual</h5><div class="comparison-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">';
        
        if (perf.predicted_duration && perf.actual_duration) {
            const diff = perf.actual_duration - perf.predicted_duration;
            const diffPct = ((diff / perf.predicted_duration) * 100).toFixed(1);
            const diffClass = diff > 0 ? 'text-red' : 'text-green';
            comparisonHTML += `
                <div class="comparison-item">
                    <strong>Duration:</strong><br>
                    Predicted: ${Math.floor(perf.predicted_duration / 60)}h ${perf.predicted_duration % 60}m<br>
                    Actual: ${Math.floor(perf.actual_duration / 60)}h ${perf.actual_duration % 60}m<br>
                    <span class="${diffClass}">${diff > 0 ? '+' : ''}${diffPct}%</span>
                </div>
            `;
        }
        
        if (perf.predicted_avg_heart_rate && perf.avg_heart_rate) {
            const diff = perf.avg_heart_rate - perf.predicted_avg_heart_rate;
            const diffPct = ((diff / perf.predicted_avg_heart_rate) * 100).toFixed(1);
            comparisonHTML += `
                <div class="comparison-item">
                    <strong>Avg Heart Rate:</strong><br>
                    Predicted: ${perf.predicted_avg_heart_rate} bpm<br>
                    Actual: ${perf.avg_heart_rate} bpm<br>
                    <span>${diff > 0 ? '+' : ''}${diffPct}%</span>
                </div>
            `;
        }
        
        if (perf.predicted_avg_speed && perf.avg_speed) {
            const diff = perf.avg_speed - perf.predicted_avg_speed;
            const diffPct = ((diff / perf.predicted_avg_speed) * 100).toFixed(1);
            comparisonHTML += `
                <div class="comparison-item">
                    <strong>Avg Speed:</strong><br>
                    Predicted: ${perf.predicted_avg_speed.toFixed(2)} km/h<br>
                    Actual: ${perf.avg_speed.toFixed(2)} km/h<br>
                    <span>${diff > 0 ? '+' : ''}${diffPct}%</span>
                </div>
            `;
        }
        
        comparisonHTML += '</div></div>';
        
        detailedMetrics.innerHTML += comparisonHTML;
    }
    
    function init(trail, userId, userProfile, completedData) {
        if (!trail || !trail.trail_id) {
            alert('Error: Invalid trail data. Please try again.');
            return;
        }
        
        currentTrail = trail;
        currentUserId = userId;
        currentUserProfile = userProfile;
        completedTrailData = completedData;
        
        // Hide loading indicator if it exists
        const loadingEl = document.getElementById('trail-detail-loading');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
        
        // Render all sections immediately
        try {
            renderEnhancedHeader(trail);
        } catch (e) {
            // Silently handle rendering errors
        }
        
        try {
            renderMapAndElevation(trail);
        } catch (e) {
            // Silently handle rendering errors
        }
        
        try {
            renderOverviewSection(trail);
        } catch (e) {
            // Silently handle rendering errors
        }
        
        // Render image gallery with photos from completed data if available
        let photos = [];
        if (completedTrailData && completedTrailData.photos) {
            photos = completedTrailData.photos;
        }
        renderImageGallery(trail, photos);
        
        // Load weather and performance data asynchronously
        const trailId = trail.trail_id;
        
        // Load completions list and set up dropdown
        loadCompletionsList(trailId, userId).then(result => {
            const completions = result.completions || [];
            const selectorContainer = document.getElementById('completion-selector-container');
            const selector = document.getElementById('completion-selector');
            
            if (selectorContainer && selector && completions.length > 0) {
                // Show selector if there are any completions
                selectorContainer.style.display = 'block';
                
                // Populate dropdown with "Predicted" as first option, then actual completions
                selector.innerHTML = '<option value="predicted" selected>Predicted</option>';
                completions.forEach(completion => {
                    const date = new Date(completion.completion_date);
                    const dateStr = date.toLocaleDateString('en-US', { 
                        year: 'numeric', 
                        month: 'short', 
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                    selector.innerHTML += `<option value="${completion.id}">${dateStr}</option>`;
                });
                
                // Load predicted data by default
                if (completions.length > 0) {
                    // Load the most recent completion to get predicted data
                    loadCompletionPerformance(trailId, userId, completions[0].id)
                        .then(performance => {
                            if (performance.completed && performance.performance) {
                                renderPerformanceSection(performance, true); // true = show predicted
                                renderPerformanceVisualizations(performance, true); // true = predicted mode
                            }
                        });
                }
                
                // Set up change handler - when a completion is selected, show actual vs predicted
                selector.addEventListener('change', (e) => {
                    const selectedValue = e.target.value;
                    if (selectedValue === 'predicted') {
                        // Show predicted metrics
                        if (completions.length > 0) {
                            loadCompletionPerformance(trailId, userId, completions[0].id)
                                .then(performance => {
                                    if (performance.completed && performance.performance) {
                                        renderPerformanceSection(performance, true); // true = show predicted
                                        renderPerformanceVisualizations(performance, true); // true = predicted mode
                                    }
                                });
                        }
                    } else if (selectedValue) {
                        // Show actual completion with predicted comparison
                        loadCompletionPerformance(trailId, userId, parseInt(selectedValue))
                            .then(performance => {
                                if (performance.completed && performance.performance) {
                                    renderPerformanceSection(performance, false); // false = show actual
                                    renderPerformanceVisualizations(performance, false); // false = actual mode
                                }
                            });
                    }
                });
                
                // Set up metric selector change handler
                const metricSelector = document.getElementById('metric-selector');
                if (metricSelector) {
                    metricSelector.addEventListener('change', (e) => {
                        currentMetric = e.target.value;
                        renderPerformanceChart();
                    });
                }
            }
        });
        
        // Load weather and performance in parallel
        Promise.all([
            fetch(`/api/trail/${trailId}/weather/weekly`)
                .then(r => {
                    if (!r.ok) {
                        console.warn('Weather API returned', r.status);
                        return { forecast: [] };
                    }
                    return r.json();
                })
                .catch(e => {
                    console.warn('Error loading weather:', e);
                    return { forecast: [] };
                }),
            // Use completed trail data if available, otherwise fetch from API
            completedTrailData ? Promise.resolve({
                completed: true,
                performance: {
                    actual_duration: completedTrailData.actual_duration,
                    rating: completedTrailData.rating,
                    difficulty_rating: completedTrailData.difficulty_rating,
                    avg_heart_rate: completedTrailData.avg_heart_rate,
                    max_heart_rate: completedTrailData.max_heart_rate,
                    avg_speed: completedTrailData.avg_speed,
                    max_speed: completedTrailData.max_speed,
                    total_calories: completedTrailData.total_calories,
                    completion_date: completedTrailData.completion_date,
                    photos: completedTrailData.photos || []
                }
            }) : loadCompletionPerformance(trailId, userId, null)
        ]).then(([weather, performance]) => {
            // Render Performance and Weather sections
            // Don't render performance here - it will be rendered when completion selector loads
            renderWeatherSection(weather);
            
            // Update image gallery with photos from performance data if available
            if (performance && performance.completed && performance.performance && performance.performance.photos) {
                renderImageGallery(trail, performance.performance.photos);
            }
            
            // Load recommendations
            let recommendationsUrl = `/api/profile/${userId}/trail/${trailId}/recommendations`;
            if (weather && weather.forecast && weather.forecast.length > 0) {
                try {
                    const weatherParam = encodeURIComponent(JSON.stringify(weather.forecast));
                    recommendationsUrl += `?weather_forecast=${weatherParam}`;
                } catch (e) {
                    console.warn('Error encoding weather parameter:', e);
                }
            }
            
            return fetch(recommendationsUrl)
                .then(r => {
                    if (!r.ok) {
                        console.warn('Recommendations API returned', r.status);
                        return null;
                    }
                    return r.json();
                })
                .catch(e => {
                    console.warn('Error loading recommendations:', e);
                    return null;
                })
                .then(recommendations => {
                    renderRecommendationsSection(recommendations);
                });
        });
    }
    
    return {
        init: init,
        removeCompletion: removeCompletion
    };
})();
