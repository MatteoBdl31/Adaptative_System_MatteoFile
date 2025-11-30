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
            exactColor = '#5b8df9', 
            suggestionColor = '#f59e0b',
            onMarkerClick = null 
        } = options;

        trails.forEach(trail => {
            const { latitude, longitude, name, distance, view_type, trail_id } = trail;
            
            if (!latitude || !longitude) return;

            const isExact = view_type === 'recommended' || view_type === 'exact';
            const color = isExact ? exactColor : suggestionColor;

            const icon = L.divIcon({
                className: 'custom-marker',
                html: `<div style="
                    background-color: ${color};
                    width: 18px;
                    height: 18px;
                    border-radius: 50%;
                    border: 2px solid #fff;
                    box-shadow: 0 2px 6px rgba(0,0,0,.3);
                "></div>`,
                iconSize: [18, 18],
                iconAnchor: [9, 9]
            });

            const marker = L.marker([latitude, longitude], { icon }).addTo(map);
            
            const popupContent = `
                <strong>${name || 'Unknown'}</strong><br/>
                ${distance || '—'} km
            `;
            
            marker.bindPopup(popupContent);
            
            if (onMarkerClick && trail_id) {
                marker.on('click', () => onMarkerClick(trail_id));
            }

            bounds.push([latitude, longitude]);

            // Add trail path if coordinates available
            if (trail.coordinates) {
                try {
                    const coords = typeof trail.coordinates === 'string' 
                        ? JSON.parse(trail.coordinates) 
                        : trail.coordinates;
                    
                    if (coords && coords.coordinates && Array.isArray(coords.coordinates)) {
                        const latLngs = coords.coordinates.map(coord => [coord[1], coord[0]]);
                        L.polyline(latLngs, {
                            color: color,
                            weight: 3,
                            opacity: 0.8
                        }).addTo(map);
                    }
                } catch (e) {
                    console.warn('Failed to parse trail coordinates:', e);
                }
            }
        });

        if (bounds.length > 0) {
            map.fitBounds(bounds, { padding: [20, 20] });
        }

        return map;
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
window.FormManager = FormManager;
window.ViewManager = ViewManager;
window.Utils = Utils;
