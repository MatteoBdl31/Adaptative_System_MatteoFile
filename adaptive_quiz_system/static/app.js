/**
 * Modern Adaptive Trail Recommender - Main Application
 * ES6+ Module-based architecture for better maintainability
 */

// ============================================
// State Management
// ============================================

class AppState {
    constructor() {
        this.state = {
            loading: false,
            error: null,
            data: null,
            viewMode: 'list', // 'list', 'map', 'cards'
            compareMode: false,
            users: []
        };
        this.listeners = [];
    }

    setState(updates) {
        this.state = { ...this.state, ...updates };
        this.notifyListeners();
    }

    getState() {
        return { ...this.state };
    }

    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    notifyListeners() {
        this.listeners.forEach(listener => listener(this.state));
    }
}

// ============================================
// API Client
// ============================================

class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return { data, error: null };
        } catch (error) {
            console.error('API request failed:', error);
            return { data: null, error: error.message };
        }
    }

    async getDemoResults(params) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/api/demo/results?${queryString}`);
    }

    async getTrails() {
        return this.request('/api/trails');
    }

    async getTrailDetail(trailId) {
        return this.request(`/api/trail/${trailId}`);
    }
}

// ============================================
// Map Manager
// ============================================

class MapManager {
    constructor() {
        this.maps = new Map();
    }

    initMap(containerId, options = {}) {
        if (typeof L === 'undefined') {
            console.warn('Leaflet not loaded');
            return null;
        }

        // Remove existing map if it exists
        if (this.maps.has(containerId)) {
            this.removeMap(containerId);
        }

        // Get container element and check if it has a Leaflet instance
        const container = typeof containerId === 'string' 
            ? document.getElementById(containerId) 
            : containerId;
        
        if (container) {
            // If container has a Leaflet map instance attached, clean it up
            if (container._leaflet_id) {
                // Clear container content and remove Leaflet ID to allow fresh initialization
                container.innerHTML = '';
                delete container._leaflet_id;
            }
        }

        const defaultOptions = {
            zoom: 8,
            center: [45.8, 6.5],
            ...options
        };

        const map = L.map(containerId, defaultOptions);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);

        this.maps.set(containerId, map);
        return map;
    }

    addTrailMarkers(map, trails, options = {}) {
        if (!map || !trails) return;

        const bounds = [];
        const { 
            exactColor = '#059669',   // --color-map-recommended (distinct green)
            suggestionColor = '#ea580c', // --color-map-suggestion (orange, distinct from green)
            collaborativeColor = '#8b5a2b', // --color-collaborative (dot)
            collaborativeRingColor = '#0ea5e9', // --color-collaborative-ring (dashed border, sky blue)
            onMarkerClick = null 
        } = options;

        // Store trail data for interactivity
        const trailDataMap = new Map();

        trails.forEach(trail => {
            const { latitude, longitude, name, distance, duration, elevation_gain, difficulty, description, view_type, trail_id, elevation_profile, forecast_weather, is_collaborative } = trail;
            
            if (!latitude || !longitude) {
                if (is_collaborative || (view_type && view_type.includes('collaborative'))) {
                    console.warn('Collaborative trail missing coordinates:', { trail_id, name, latitude, longitude });
                }
                return;
            }

            // Check if trail is collaborative (either explicitly marked or in view_type)
            const isCollaborative = is_collaborative || (view_type && view_type.includes('collaborative'));
            
            // Check if trail is ONLY collaborative (not also recommended or suggested)
            const isOnlyCollaborative = isCollaborative && 
                view_type === 'collaborative' && 
                !view_type.includes('recommended') && 
                !view_type.includes('suggested');
            
            // Determine color: prioritize recommended > suggested > collaborative
            let color = suggestionColor;
            if (view_type === 'recommended' || view_type === 'exact' || (view_type && view_type.includes('recommended'))) {
                color = exactColor;
            } else if (view_type === 'suggested' || (view_type && view_type.includes('suggested'))) {
                color = suggestionColor;
            } else if (isOnlyCollaborative) {
                // If trail is ONLY collaborative (not also recommended/suggested), use collaborative color
                color = collaborativeColor;
            }

            // Option A: DOM/CSS dans divIcon - Le point et le cercle font partie du même élément DOM
            // Cela garantit un alignement parfait et une taille constante relative au marqueur
            const icon = L.divIcon({
                className: `custom-marker ${isCollaborative ? 'has-collaborative-ring' : ''}`,
                html: `
                    <div class="marker-wrapper" style="position: relative; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center;">
                        ${isCollaborative ? `
                            <div class="collaborative-ring" style="
                                position: absolute;
                                left: 50%;
                                top: 50%;
                                transform: translate(-50%, -50%);
                                width: 35px;
                                height: 35px;
                                border: 3px dashed ${collaborativeRingColor};
                                border-radius: 50%;
                                background-color: transparent;
                                pointer-events: none;
                                z-index: 1;
                            "></div>
                        ` : ''}
                        <div class="marker-dot" style="
                            position: absolute;
                            left: 50%;
                            top: 50%;
                            transform: translate(-50%, -50%);
                            background-color: ${color};
                            width: 18px;
                            height: 18px;
                            border-radius: 50%;
                            border: 2px solid #fff;
                            box-shadow: 0 2px 6px rgba(0,0,0,.3);
                            z-index: 2;
                        "></div>
                    </div>
                `,
                iconSize: [50, 50],  // Assez grand pour contenir le ring (35px) + marge
                iconAnchor: [25, 25]  // Centre du wrapper (50/2 = 25)
            });

            const marker = L.marker([latitude, longitude], { icon }).addTo(map);
            
            // Toggle de visibilité du cercle collaboratif basé sur le zoom
            // Utilise le DOM directement pour un contrôle précis
            if (isCollaborative) {
                
                // Use setTimeout to ensure the marker icon is fully rendered before accessing it
                setTimeout(() => {
                    const updateCircleVisibility = () => {
                        const currentZoom = map.getZoom();
                        const iconElement = marker._icon;
                        if (iconElement) {
                            const ring = iconElement.querySelector('.collaborative-ring');
                            if (ring) {
                                // Show ring at zoom 6 and above (less restrictive than before)
                                if (currentZoom < 6) {
                                    ring.style.display = 'none';
                                } else {
                                    ring.style.display = 'block';
                                    ring.style.opacity = '1';
                                    ring.style.visibility = 'visible';
                                }
                            } else {
                                // Ring element not found - this can happen if marker hasn't rendered yet
                            }
                        }
                    };
                    
                    // Update visibility on zoom changes
                    map.on('zoomend', updateCircleVisibility);
                    updateCircleVisibility(); // Set initial visibility
                }, 100); // Small delay to ensure DOM is ready
            }
            
            // Format difficulty
            const difficultyValue = difficulty || 0;
            const difficultyText = difficultyValue <= 3 ? 'Easy' : difficultyValue <= 6 ? 'Medium' : 'Hard';
            const difficultyClass = difficultyValue <= 3 ? 'easy' : difficultyValue <= 6 ? 'medium' : 'hard';
            
            // Format duration using Utils if available
            let durationText = '—';
            if (duration && typeof Utils !== 'undefined' && Utils.formatDuration) {
                durationText = Utils.formatDuration(duration);
            } else if (duration) {
                const mins = parseInt(duration) || 0;
                if (mins < 60) {
                    durationText = `${mins} min`;
                } else {
                    const hours = Math.floor(mins / 60);
                    const remainingMins = mins % 60;
                    durationText = remainingMins === 0 
                        ? `${hours} hour${hours !== 1 ? 's' : ''}` 
                        : `${hours} hour${hours !== 1 ? 's' : ''} ${remainingMins} min`;
                }
            }
            
            // Build elevation profile SVG if available
            let elevationProfileSVG = '';
            let profileData = elevation_profile;
            let polyline = null;
            let trailCoordinates = null;
            
            // Parse elevation_profile if it's a JSON string
            if (profileData && typeof profileData === 'string') {
                try {
                    profileData = JSON.parse(profileData);
                } catch (e) {
                    console.warn('Failed to parse elevation_profile:', e);
                    profileData = null;
                }
            }
            
            // Parse coordinates for trail line
            if (trail.coordinates) {
                try {
                    trailCoordinates = typeof trail.coordinates === 'string' 
                        ? JSON.parse(trail.coordinates) 
                        : trail.coordinates;
                } catch (e) {
                    console.warn('Failed to parse trail coordinates:', e);
                }
            }
            
            if (profileData && Array.isArray(profileData) && profileData.length > 0) {
                elevationProfileSVG = this.renderElevationProfile(profileData, distance, trail_id);
            }
            
            // Format weather info
            let weatherIcon = '';
            let weatherText = '';
            if (forecast_weather) {
                const weatherIcons = {
                    'sunny': '☀️',
                    'cloudy': '☁️',
                    'rainy': '🌧️',
                    'snowy': '❄️',
                    'storm_risk': '⛈️'
                };
                weatherIcon = weatherIcons[forecast_weather] || '🌤️';
                weatherText = forecast_weather.charAt(0).toUpperCase() + forecast_weather.slice(1).replace('_', ' ');
            }
            
            // Build popup content with all trail information
            const titleHtml = (options.userId && trail_id)
                ? `<a href="/profile/${options.userId}/trail/${trail_id}" class="trail-popup__title-link">${name || 'Unknown'}</a>`
                : `<span class="trail-popup__title">${name || 'Unknown'}</span>`;
            const saveBtnHtml = (options.userId && trail_id)
                ? `<button type="button" class="btn-save-trail-map btn btn-secondary btn--sm" data-trail-id="${trail_id}" data-user-id="${options.userId}" style="margin-left: auto;">Save Trail</button>`
                : '';
            const popupContent = `
                <div class="trail-popup">
                    <div class="trail-popup__header" style="display: flex; align-items: center; gap: var(--space-xs); flex-wrap: wrap;">
                        <h3 class="trail-popup__title-wrap" style="margin: 0; flex: 1 1 auto; min-width: 0;">
                            ${titleHtml}
                        </h3>
                        ${saveBtnHtml}
                        <div style="display: flex; align-items: center; gap: var(--space-xs);">
                            <span class="trail-popup__difficulty difficulty-${difficultyClass}">${difficultyText}</span>
                            <button type="button" class="trail-explanation-btn" aria-label="Why was this recommended?" data-trail-id="${trail_id || ''}" data-user-id="${options.userId || ''}" style="width: 18px; height: 18px; padding: 0;">
                                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M8 2C4.69 2 2 4.69 2 8C2 11.31 4.69 14 8 14C11.31 14 14 11.31 14 8C14 4.69 11.31 2 8 2Z" stroke="currentColor" stroke-width="1.5" fill="none"/>
                                    <path d="M8 5.5V8.5M8 11H8.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                    ${description ? `<p class="trail-popup__description">${description}</p>` : ''}
                    <div class="trail-popup__stats">
                        <div class="trail-popup__stat">
                            <span class="trail-popup__stat-icon">📏</span>
                            <span class="trail-popup__stat-label">Distance:</span>
                            <span class="trail-popup__stat-value">${distance || '—'} km</span>
                        </div>
                        <div class="trail-popup__stat">
                            <span class="trail-popup__stat-icon">⏱</span>
                            <span class="trail-popup__stat-label">Duration:</span>
                            <span class="trail-popup__stat-value">${durationText}</span>
                        </div>
                        <div class="trail-popup__stat">
                            <span class="trail-popup__stat-icon">⛰</span>
                            <span class="trail-popup__stat-label">Elevation:</span>
                            <span class="trail-popup__stat-value">${elevation_gain || '—'} m</span>
                        </div>
                        ${forecast_weather ? `
                        <div class="trail-popup__stat">
                            <span class="trail-popup__stat-icon">${weatherIcon}</span>
                            <span class="trail-popup__stat-label">Weather:</span>
                            <span class="trail-popup__stat-value">${weatherText}</span>
                        </div>
                        ` : ''}
                    </div>
                    <div class="trail-popup-explanation" id="trail-popup-explanation-${trail_id || ''}" style="display: none; margin-top: var(--space-sm); padding: var(--space-sm); background: var(--color-bg-secondary); border-radius: var(--radius-md);">
                        <div class="trail-popup-explanation-loading" style="text-align: center; color: var(--color-text-secondary); font-size: var(--font-size-sm);">
                            <span style="display: inline-block; animation: spin 1s linear infinite;">⏳</span> Generating...
                        </div>
                        <div class="trail-popup-explanation-loaded" style="display: none;">
                            <p class="trail-popup-explanation-text" style="font-size: var(--font-size-sm); margin-bottom: var(--space-xs);"></p>
                            <ul class="trail-popup-explanation-factors" style="list-style: none; padding: 0; margin: 0; font-size: var(--font-size-xs);"></ul>
                        </div>
                    </div>
                    ${elevationProfileSVG ? `<div class="trail-popup__elevation">${elevationProfileSVG}</div>` : ''}
                </div>
            `;
            
            marker.bindPopup(popupContent, {
                maxWidth: 300,
                className: 'trail-popup-wrapper',
                closeOnClick: false,
                autoClose: false
            });

            let popupCloseTimer;
            marker.on('mouseover', () => {
                clearTimeout(popupCloseTimer);
                marker.openPopup();
            });
            marker.on('mouseout', () => {
                popupCloseTimer = setTimeout(() => marker.closePopup(), 150);
            });
            marker.off('click');
            if (onMarkerClick && trail_id) {
                marker.on('click', () => onMarkerClick(trail_id));
            }
            
            // Store popup reference for later interaction setup
            marker.on('popupopen', () => {
                const popupEl = marker.getPopup().getElement();
                if (popupEl) {
                    popupEl.addEventListener('mouseenter', () => clearTimeout(popupCloseTimer));
                    popupEl.addEventListener('mouseleave', () => {
                        popupCloseTimer = setTimeout(() => marker.closePopup(), 150);
                    });
                }
                // Setup interactivity after popup opens
                // Get polyline from stored trail data
                const storedData = map._trailDataMap?.get(trail_id);
                if (profileData && storedData && storedData.polyline) {
                    this.setupElevationProfileInteractivity(
                        trail_id, 
                        profileData, 
                        storedData.polyline, 
                        storedData.coordinates,
                        storedData.distance
                    );
                }
                
                // Setup Why? button click handler for popup
                const whyBtn = document.querySelector(`.trail-popup-wrapper .trail-explanation-btn[data-trail-id="${trail_id}"]`);
                if (whyBtn) {
                    whyBtn.addEventListener('click', async (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        const trailId = whyBtn.dataset.trailId;
                        const userId = whyBtn.dataset.userId || 'a';
                        const explanationDiv = document.getElementById(`trail-popup-explanation-${trailId}`);
                        
                        if (!explanationDiv) return;
                        
                        const loadingDiv = explanationDiv.querySelector('.trail-popup-explanation-loading');
                        const loadedDiv = explanationDiv.querySelector('.trail-popup-explanation-loaded');
                        const textEl = loadedDiv?.querySelector('.trail-popup-explanation-text');
                        const factorsEl = loadedDiv?.querySelector('.trail-popup-explanation-factors');
                        
                        // Toggle visibility
                        if (explanationDiv.style.display === 'none') {
                            explanationDiv.style.display = 'block';
                            
                            // Check if already loaded
                            if (loadedDiv && loadedDiv.style.display !== 'none' && textEl?.textContent) {
                                return;
                            }
                            
                            // Show loading
                            if (loadingDiv) loadingDiv.style.display = 'block';
                            if (loadedDiv) loadedDiv.style.display = 'none';
                            whyBtn.classList.add('loading');
                            
                            try {
                                // Build context from URL params
                                const params = new URLSearchParams(window.location.search);
                                const context = {};
                                const contextKeys = ['time_available_days', 'time_available_hours', 'device', 'weather', 
                                                   'connection', 'season', 'hike_start_date', 'hike_end_date'];
                                contextKeys.forEach(key => {
                                    const value = params.get(`a_${key}`) || params.get(key);
                                    if (value) context[key] = value;
                                });
                                
                                // Get user_id from URL params or form
                                const form = document.getElementById('demo-form');
                                const userSelect = form?.querySelector(`#user-select-${userId}`);
                                const user_id = userSelect?.value || params.get(`user_id_${userId}`) || params.get('user_id_a') || '';
                                if (user_id) {
                                    context[`user_id_${userId}`] = user_id;
                                }
                                
                                const queryString = new URLSearchParams(context).toString();
                                const response = await fetch(`/api/explanations/trail/${userId}/${trailId}?${queryString}`);
                                const data = await response.json();
                                
                                if (data.explanation_text) {
                                    if (textEl) textEl.textContent = data.explanation_text;
                                    if (factorsEl && data.key_factors) {
                                        factorsEl.innerHTML = '';
                                        data.key_factors.forEach(factor => {
                                            const li = document.createElement('li');
                                            li.textContent = '• ' + factor;
                                            li.style.padding = '2px 0';
                                            factorsEl.appendChild(li);
                                        });
                                    }
                                    
                                    if (loadingDiv) loadingDiv.style.display = 'none';
                                    if (loadedDiv) loadedDiv.style.display = 'block';
                                }
                            } catch (error) {
                                console.error('Error fetching trail explanation:', error);
                                if (loadingDiv) loadingDiv.textContent = 'Unable to load explanation.';
                            } finally {
                                whyBtn.classList.remove('loading');
                            }
                        } else {
                            explanationDiv.style.display = 'none';
                            if (whyBtn && typeof whyBtn.blur === 'function') {
                                whyBtn.blur();
                            }
                        }
                    });
                }
                // Setup Save Trail button in popup (demo map)
                const saveBtn = document.querySelector(`.trail-popup-wrapper .btn-save-trail-map[data-trail-id="${trail_id}"]`);
                if (saveBtn && !saveBtn._saveBound) {
                    saveBtn._saveBound = true;
                    saveBtn.addEventListener('click', function (e) {
                        e.preventDefault();
                        const uid = this.dataset.userId;
                        const tid = this.dataset.trailId;
                        if (!uid || !tid) return;
                        fetch(`/api/profile/${uid}/trails/save`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ trail_id: tid })
                        })
                            .then(r => r.json())
                            .then(d => {
                                if (d.success) {
                                    this.textContent = 'Saved!';
                                    this.disabled = true;
                                } else {
                                    this.textContent = 'Already saved';
                                    this.disabled = true;
                                }
                            })
                            .catch(() => { this.textContent = 'Error'; });
                    });
                }
            });

            bounds.push([latitude, longitude]);

            // Add trail path if coordinates available
            if (trailCoordinates && trailCoordinates.coordinates && Array.isArray(trailCoordinates.coordinates)) {
                const latLngs = trailCoordinates.coordinates.map(coord => [coord[1], coord[0]]);
                polyline = L.polyline(latLngs, {
                    color: color,
                    weight: 3,
                    opacity: 0.8
                }).addTo(map);
                
                // Store trail data for interactivity
                const trailData = {
                    polyline,
                    profileData,
                    coordinates: trailCoordinates,
                    distance,
                    color,
                    marker
                };
                trailDataMap.set(trail_id, trailData);
                
                // Add hover interaction to polyline (only if we have elevation profile)
                if (profileData && Array.isArray(profileData) && profileData.length > 0) {
                    this.setupPolylineInteractivity(trail_id, polyline, profileData, trailCoordinates, distance, marker);
                }
            }
        });

        if (bounds.length > 0) {
            map.fitBounds(bounds, { padding: [20, 20] });
        }

        // Store trail data map for later access
        map._trailDataMap = trailDataMap;

        return map;
    }

    setupPolylineInteractivity(trailId, polyline, profileData, coordinates, totalDistance, marker) {
        if (!profileData || !Array.isArray(profileData) || profileData.length === 0) return;
        
        let hoverMarker = null;
        let currentProfileIndex = -1;
        
        // Calculate cumulative distances along the trail
        const latLngs = coordinates.coordinates.map(coord => [coord[1], coord[0]]);
        const distances = [0];
        for (let i = 1; i < latLngs.length; i++) {
            const prev = latLngs[i - 1];
            const curr = latLngs[i];
            const dist = L.latLng(prev).distanceTo(L.latLng(curr)) / 1000; // km
            distances.push(distances[i - 1] + dist);
        }
        
        polyline.on('mouseover', (e) => {
            if (!e.latlng) return;
            
            // Find closest point on polyline
            let minDist = Infinity;
            let closestIndex = 0;
            let closestPoint = latLngs[0];
            
            latLngs.forEach((point, index) => {
                const dist = L.latLng(point).distanceTo(e.latlng);
                if (dist < minDist) {
                    minDist = dist;
                    closestIndex = index;
                    closestPoint = point;
                }
            });
            
            // Calculate distance along trail
            const distanceAlongTrail = distances[closestIndex];
            
            // Find corresponding point in elevation profile
            const profileIndex = this.findProfileIndexForDistance(profileData, distanceAlongTrail * 1000);
            
            if (profileIndex >= 0 && profileIndex !== currentProfileIndex) {
                currentProfileIndex = profileIndex;
                
                // Create or update hover marker
                if (!hoverMarker) {
                    hoverMarker = L.circleMarker(closestPoint, {
                        radius: 8,
                        color: '#ef4444',
                        fillColor: '#fff',
                        fillOpacity: 1,
                        weight: 2
                    }).addTo(polyline._map);
                } else {
                    hoverMarker.setLatLng(closestPoint);
                }
                
                // Highlight on elevation profile
                this.highlightElevationProfile(trailId, profileIndex);
            }
        });
        
        polyline.on('mouseout', () => {
            if (hoverMarker) {
                hoverMarker.remove();
                hoverMarker = null;
            }
            currentProfileIndex = -1;
            this.clearElevationProfileHighlight(trailId);
        });
    }

    setupElevationProfileInteractivity(trailId, profileData, polyline, coordinates, totalDistance) {
        if (!profileData || !Array.isArray(profileData) || profileData.length === 0) return;
        if (!polyline || !coordinates) return;
        
        const svg = document.querySelector(`#elevation-chart-${trailId}`);
        if (!svg) return;
        
        const latLngs = coordinates.coordinates.map(coord => [coord[1], coord[0]]);
        
        // Calculate cumulative distances along the trail
        const distances = [0];
        for (let i = 1; i < latLngs.length; i++) {
            const prev = latLngs[i - 1];
            const curr = latLngs[i];
            const dist = L.latLng(prev).distanceTo(L.latLng(curr)) / 1000; // km
            distances.push(distances[i - 1] + dist);
        }
        
        let hoverMarker = null;
        let currentProfileIndex = -1;
        
        // Add invisible hover areas over the elevation line
        const points = profileData.map(p => ({
            distance: p.distance_m || 0,
            elevation: p.elevation_m || 0
        }));
        
        const width = 280;
        const height = 100;
        const padding = { top: 8, right: 8, bottom: 20, left: 40 };
        const maxDistance = points[points.length - 1].distance / 1000;
        const minElevation = Math.min(...points.map(p => p.elevation));
        const maxElevation = Math.max(...points.map(p => p.elevation));
        const elevationRange = maxElevation - minElevation || 1;
        const xScale = (width - padding.left - padding.right) / maxDistance;
        const yScale = (height - padding.top - padding.bottom) / elevationRange;
        
        // Create hover areas
        points.forEach((point, index) => {
            if (index === 0) return; // Skip first point
            
            const x1 = padding.left + (points[index - 1].distance / 1000) * xScale;
            const x2 = padding.left + (point.distance / 1000) * xScale;
            const y1 = padding.top;
            const y2 = height - padding.bottom;
            
            const hoverArea = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            hoverArea.setAttribute('x', Math.min(x1, x2));
            hoverArea.setAttribute('y', y1);
            hoverArea.setAttribute('width', Math.abs(x2 - x1));
            hoverArea.setAttribute('height', y2 - y1);
            hoverArea.setAttribute('fill', 'transparent');
            hoverArea.setAttribute('style', 'cursor: crosshair;');
            hoverArea.classList.add('elevation-hover-area');
            
            hoverArea.addEventListener('mouseenter', () => {
                if (index !== currentProfileIndex) {
                    currentProfileIndex = index;
                    
                    // Find corresponding point on trail
                    const distanceKm = point.distance / 1000;
                    const trailIndex = this.findTrailIndexForDistance(distances, distanceKm);
                    
                    if (trailIndex >= 0 && trailIndex < latLngs.length) {
                        const trailPoint = latLngs[trailIndex];
                        
                        // Create or update hover marker on trail
                        if (!hoverMarker) {
                            hoverMarker = L.circleMarker(trailPoint, {
                                radius: 8,
                                color: '#ef4444',
                                fillColor: '#fff',
                                fillOpacity: 1,
                                weight: 2
                            }).addTo(polyline._map);
                        } else {
                            hoverMarker.setLatLng(trailPoint);
                        }
                        
                        // Highlight on elevation profile
                        this.highlightElevationProfile(trailId, index);
                    }
                }
            });
            
            hoverArea.addEventListener('mouseleave', () => {
                if (hoverMarker) {
                    hoverMarker.remove();
                    hoverMarker = null;
                }
                currentProfileIndex = -1;
                this.clearElevationProfileHighlight(trailId);
            });
            
            svg.appendChild(hoverArea);
        });
    }

    findProfileIndexForDistance(profileData, distanceM) {
        for (let i = 0; i < profileData.length; i++) {
            if (profileData[i].distance_m >= distanceM) {
                return i;
            }
        }
        return profileData.length - 1;
    }

    findTrailIndexForDistance(distances, distanceKm) {
        for (let i = 0; i < distances.length; i++) {
            if (distances[i] >= distanceKm) {
                return i;
            }
        }
        return distances.length - 1;
    }

    highlightElevationProfile(trailId, index) {
        const marker = document.querySelector(`#elevation-marker-${trailId}`);
        if (marker) {
            marker.setAttribute('display', 'block');
            const profileData = JSON.parse(marker.getAttribute('data-profile'));
            if (profileData && profileData[index]) {
                const point = profileData[index];
                const width = 280;
                const height = 100;
                const padding = { top: 8, right: 8, bottom: 20, left: 40 };
                const maxDistance = profileData[profileData.length - 1].distance_m / 1000;
                const minElevation = Math.min(...profileData.map(p => p.elevation_m));
                const maxElevation = Math.max(...profileData.map(p => p.elevation_m));
                const elevationRange = maxElevation - minElevation || 1;
                const xScale = (width - padding.left - padding.right) / maxDistance;
                const yScale = (height - padding.top - padding.bottom) / elevationRange;
                
                const x = padding.left + (point.distance_m / 1000) * xScale;
                const y = padding.top + (maxElevation - point.elevation_m) * yScale;
                
                marker.setAttribute('cx', x);
                marker.setAttribute('cy', y);
            }
        }
    }

    clearElevationProfileHighlight(trailId) {
        const marker = document.querySelector(`#elevation-marker-${trailId}`);
        if (marker) {
            marker.setAttribute('display', 'none');
        }
    }

    renderElevationProfile(elevationProfile, totalDistance, trailId) {
        if (!elevationProfile || !Array.isArray(elevationProfile) || elevationProfile.length === 0) {
            return '';
        }

        // Parse elevation profile data
        const points = elevationProfile.map(p => ({
            distance: p.distance_m || 0,
            elevation: p.elevation_m || 0
        }));

        // Chart dimensions
        const width = 280;
        const height = 100;
        const padding = { top: 8, right: 8, bottom: 20, left: 40 };

        // Calculate scales
        const maxDistance = points[points.length - 1].distance / 1000; // Convert to km
        const minElevation = Math.min(...points.map(p => p.elevation));
        const maxElevation = Math.max(...points.map(p => p.elevation));
        const elevationRange = maxElevation - minElevation || 1;

        // Scale factors
        const xScale = (width - padding.left - padding.right) / maxDistance;
        const yScale = (height - padding.top - padding.bottom) / elevationRange;

        // Generate path
        let pathData = '';
        points.forEach((point, index) => {
            const x = padding.left + (point.distance / 1000) * xScale;
            const y = padding.top + (maxElevation - point.elevation) * yScale;
            if (index === 0) {
                pathData += `M ${x} ${y}`;
            } else {
                pathData += ` L ${x} ${y}`;
            }
        });

        // Generate area fill path (closed path for fill)
        const areaPath = pathData + 
            ` L ${padding.left + maxDistance * xScale} ${height - padding.bottom}` +
            ` L ${padding.left} ${height - padding.bottom} Z`;

        // Format elevation labels
        const formatElevation = (elev) => Math.round(elev);

        const uniqueGradientId = `elevationGradient-${trailId || 'default'}`;
        
        return `
            <div class="trail-popup__elevation-header">
                <span class="trail-popup__elevation-title">Elevation Profile</span>
                <span class="trail-popup__elevation-range">${formatElevation(minElevation)}m - ${formatElevation(maxElevation)}m</span>
            </div>
            <svg class="trail-popup__elevation-chart" id="elevation-chart-${trailId || 'default'}" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
                <!-- Grid lines -->
                <defs>
                    <linearGradient id="${uniqueGradientId}" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#6366f1;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#6366f1;stop-opacity:0.05" />
                    </linearGradient>
                </defs>
                
                <!-- Area fill -->
                <path d="${areaPath}" fill="url(#${uniqueGradientId})" />
                
                <!-- Elevation line -->
                <path d="${pathData}" 
                      fill="none" 
                      stroke="#6366f1" 
                      stroke-width="2" 
                      stroke-linecap="round" 
                      stroke-linejoin="round" />
                
                <!-- Hover marker (hidden by default) -->
                <circle id="elevation-marker-${trailId || 'default'}" 
                        r="4" 
                        fill="#ef4444" 
                        stroke="#fff" 
                        stroke-width="2"
                        display="none"
                        data-profile='${JSON.stringify(elevationProfile)}' />
                
                <!-- Y-axis labels -->
                <text x="${padding.left - 5}" y="${padding.top + 2}" 
                      text-anchor="end" 
                      font-size="9" 
                      fill="#64748b" 
                      alignment-baseline="hanging">${formatElevation(maxElevation)}m</text>
                <text x="${padding.left - 5}" y="${height - padding.bottom - 2}" 
                      text-anchor="end" 
                      font-size="9" 
                      fill="#64748b" 
                      alignment-baseline="baseline">${formatElevation(minElevation)}m</text>
                
                <!-- X-axis labels -->
                <text x="${padding.left}" y="${height - padding.bottom + 15}" 
                      text-anchor="start" 
                      font-size="9" 
                      fill="#64748b">0 km</text>
                <text x="${padding.left + maxDistance * xScale}" y="${height - padding.bottom + 15}" 
                      text-anchor="end" 
                      font-size="9" 
                      fill="#64748b">${maxDistance.toFixed(1)} km</text>
            </svg>
        `;
    }

    invalidateSize(mapId) {
        const map = this.maps.get(mapId);
        if (map) {
            setTimeout(() => map.invalidateSize(), 100);
        }
    }

    removeMap(containerId) {
        const map = this.maps.get(containerId);
        if (map) {
            map.remove();
            this.maps.delete(containerId);
        }
    }
}

// ============================================
// Form Manager
// ============================================

class FormManager {
    constructor(formElement) {
        this.form = formElement;
        this.setupEventListeners();
    }

    setupEventListeners() {
        if (!this.form) return;

        // Handle date range logic
        const startDateInput = this.form.querySelector('[name*="hike_start_date"]');
        const endDateInput = this.form.querySelector('[name*="hike_end_date"]');

        if (startDateInput && endDateInput) {
            startDateInput.addEventListener('change', () => {
                endDateInput.min = startDateInput.value;
                if (endDateInput.value && endDateInput.value < startDateInput.value) {
                    endDateInput.value = startDateInput.value;
                }
                this.calculateTimeAvailable();
            });

            endDateInput.addEventListener('change', () => {
                this.calculateTimeAvailable();
            });

            // Set default start date to today
            if (!startDateInput.value) {
                startDateInput.value = new Date().toISOString().split('T')[0];
            }
        }

        // Auto-fill season
        this.autoFillSeason();
    }

    calculateTimeAvailable() {
        const prefix = this.getFormPrefix();
        const startDateInput = this.form.querySelector(`[name="${prefix}_hike_start_date"]`);
        const endDateInput = this.form.querySelector(`[name="${prefix}_hike_end_date"]`);
        
        if (!startDateInput) return;

        let daysInput = this.form.querySelector(`[name="${prefix}_time_available_days"]`);
        let hoursInput = this.form.querySelector(`[name="${prefix}_time_available_hours"]`);

        if (!daysInput) {
            daysInput = document.createElement('input');
            daysInput.type = 'hidden';
            daysInput.name = `${prefix}_time_available_days`;
            this.form.appendChild(daysInput);
        }

        if (!hoursInput) {
            hoursInput = document.createElement('input');
            hoursInput.type = 'hidden';
            hoursInput.name = `${prefix}_time_available_hours`;
            this.form.appendChild(hoursInput);
        }

        const startDate = startDateInput.value;
        const endDate = endDateInput?.value || startDate;

        if (!startDate) return;

        const start = new Date(startDate);
        const end = new Date(endDate);
        start.setHours(0, 0, 0, 0);
        end.setHours(0, 0, 0, 0);

        const diffTime = end - start;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        daysInput.value = Math.max(0, diffDays).toString();
        hoursInput.value = '0';
    }

    autoFillSeason() {
        const currentSeason = this.getCurrentSeason(new Date());
        const seasonSelects = this.form.querySelectorAll('[name*="season"]');
        
        seasonSelects.forEach(select => {
            if (!select.value) {
                select.value = currentSeason;
            }
        });
    }

    getCurrentSeason(date) {
        const month = date.getMonth() + 1;
        if (month >= 3 && month <= 5) return 'spring';
        if (month >= 6 && month <= 8) return 'summer';
        if (month >= 9 && month <= 11) return 'fall';
        return 'winter';
    }

    getFormPrefix() {
        // Determine prefix from form inputs (a_ or b_)
        const firstInput = this.form.querySelector('input[name^="a_"], input[name^="b_"]');
        if (firstInput) {
            return firstInput.name.split('_')[0];
        }
        return 'a';
    }

    getFormData() {
        if (!this.form) return {};

        const formData = new FormData(this.form);
        const data = {};

        for (const [key, value] of formData.entries()) {
            if (!data[key]) {
                data[key] = value;
            }
        }

        return data;
    }

    serializeFormData() {
        const data = this.getFormData();
        return new URLSearchParams(data).toString();
    }
}

// ============================================
// View Manager
// ============================================

class ViewManager {
    constructor(container) {
        this.container = container;
        this.currentView = 'list';
    }

    switchView(viewName) {
        if (!this.container) return;

        this.currentView = viewName;
        
        // Update toggle buttons
        const buttons = this.container.querySelectorAll('[data-view-toggle]');
        buttons.forEach(btn => {
            if (btn.dataset.view === viewName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update view sections
        const sections = this.container.querySelectorAll('[data-view-section]');
        sections.forEach(section => {
            if (section.dataset.view === viewName) {
                section.classList.remove('hidden');
                section.classList.add('active');
            } else {
                section.classList.add('hidden');
                section.classList.remove('active');
            }
        });

        // Dispatch custom event
        this.container.dispatchEvent(new CustomEvent('viewChanged', {
            detail: { view: viewName }
        }));
    }

    getCurrentView() {
        return this.currentView;
    }
}

// ============================================
// Utility Functions
// ============================================

const Utils = {
    formatDuration(minutes) {
        if (!minutes || minutes === 0) return '—';
        const mins = parseInt(minutes) || 0;

        if (mins < 60) {
            return `${mins} min`;
        } else if (mins < 1440) {
            const hours = Math.floor(mins / 60);
            const remainingMins = mins % 60;
            if (remainingMins === 0) {
                return `${hours} hour${hours !== 1 ? 's' : ''}`;
            }
            return `${hours} hour${hours !== 1 ? 's' : ''} ${remainingMins} min`;
        } else {
            const days = Math.floor(mins / 1440);
            const remainingMins = mins % 1440;
            const hours = Math.floor(remainingMins / 60);
            const remainingMinutes = remainingMins % 60;

            const parts = [];
            if (days > 0) parts.push(`${days} day${days !== 1 ? 's' : ''}`);
            if (hours > 0) parts.push(`${hours} hour${hours !== 1 ? 's' : ''}`);
            if (remainingMinutes > 0 && days === 0) {
                parts.push(`${remainingMinutes} min`);
            }

            return parts.join(' ') || '—';
        }
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// ============================================
// Export for use in other modules
// ============================================

window.AppState = AppState;
window.ApiClient = ApiClient;
window.MapManager = MapManager;
window.Utils = Utils;
window.FormManager = FormManager;
window.ViewManager = ViewManager;
window.Utils = Utils;
