/**
 * Recommendations Page JavaScript
 * Handles view toggling and map initialization
 */

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        const recommendationsApp = new RecommendationsApp();
        recommendationsApp.init();
    });

    class RecommendationsApp {
        constructor() {
            this.mapManager = new MapManager();
            this.viewManager = null;
        }

        init() {
            this.setupViewToggles();
            this.initRecommendationMap();
        }

        setupViewToggles() {
            const viewPanels = document.querySelector('[data-view-panels]');
            if (!viewPanels) return;

            const toggleButtons = document.querySelectorAll('.view-toggle__button[data-view-target]');
            
            toggleButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    const targetView = btn.getAttribute('data-view-target');
                    if (!targetView) return;

                    // Update active state
                    toggleButtons.forEach(b => {
                        if (b === btn) {
                            b.classList.add('active');
                        } else {
                            b.classList.remove('active');
                        }
                    });

                    // Update panels
                    viewPanels.dataset.activeView = targetView;
                    viewPanels.querySelectorAll('[data-view-panel]').forEach(panel => {
                        const panelView = panel.getAttribute('data-view-panel');
                        if (panelView === targetView) {
                            panel.classList.remove('hidden');
                            panel.classList.add('active');
                        } else {
                            panel.classList.add('hidden');
                            panel.classList.remove('active');
                        }
                    });

                    // Invalidate map size if switching to map view
                    if (targetView === 'map' && window.recommendationsMap) {
                        setTimeout(() => {
                            window.recommendationsMap.invalidateSize();
                        }, 200);
                    }
                });
            });
        }

        initRecommendationMap() {
            if (typeof L === 'undefined') return;
            
            const container = document.getElementById('recommendations-map');
            if (!container || !Array.isArray(window.recommendationMapData)) return;
            if (!window.recommendationMapData.length) return;

            // Ensure any existing map is removed before initializing
            if (window.recommendationsMap) {
                try {
                    window.recommendationsMap.remove();
                } catch (e) {
                    console.warn('Error removing existing map:', e);
                }
                window.recommendationsMap = null;
            }

            // Small delay to ensure DOM is ready and container is visible
            setTimeout(() => {
                const map = this.mapManager.initMap('recommendations-map', {
                    zoom: 8,
                    center: [45.8, 6.5]
                });
                
                if (!map) {
                    console.error('Failed to initialize map');
                    return;
                }
                
                window.recommendationsMap = map;

                const bounds = [];
                window.recommendationMapData.forEach(trail => {
                    const lat = trail.latitude ?? trail.lat;
                    const lon = trail.longitude ?? trail.lon;
                    if (lat == null || lon == null) return;

                    let geometry = trail.coordinates;
                    if (typeof geometry === 'string') {
                        try {
                            geometry = JSON.parse(geometry);
                        } catch {
                            geometry = null;
                        }
                    }

                    // Determine icon color based on view_type (prioritize recommended > suggested)
                    let iconColor = '#f59e0b'; // default (suggested)
                    if (trail.view_type && trail.view_type.includes('recommended')) {
                        iconColor = '#5b8df9'; // recommended
                    }
                    
                    // Check if trail is collaborative
                    const isCollaborative = trail.is_collaborative || (trail.view_type && trail.view_type.includes('collaborative'));
                    const collaborativeColor = '#f71e50';
                    
                    // Option A: DOM/CSS dans divIcon - Le point et le cercle font partie du même élément DOM
                    const icon = L.divIcon({
                        className: `custom-marker ${isCollaborative ? 'has-collaborative-ring' : ''}`,
                        html: `
                            <div class="marker-wrapper" style="position: relative; width: 50px; height: 50px;">
                                ${isCollaborative ? `
                                    <div class="collaborative-ring" style="
                                        position: absolute;
                                        left: 50%;
                                        top: 50%;
                                        transform: translate(-50%, -50%);
                                        width: 35px;
                                        height: 35px;
                                        border: 3px dashed ${collaborativeColor};
                                        border-radius: 50%;
                                        background-color: transparent;
                                        pointer-events: none;
                                    "></div>
                                ` : ''}
                                <div class="marker-dot" style="
                                    position: absolute;
                                    left: 50%;
                                    top: 50%;
                                    transform: translate(-50%, -50%);
                                    background-color: ${iconColor};
                                    width: 18px;
                                    height: 18px;
                                    border-radius: 50%;
                                    border: 2px solid #fff;
                                    box-shadow: 0 2px 6px rgba(0,0,0,.3);
                                    z-index: 10;
                                "></div>
                            </div>
                        `,
                        iconSize: [50, 50],
                        iconAnchor: [25, 25]
                    });

                    const marker = L.marker([lat, lon], { icon }).addTo(map);
                    
                    // Toggle de visibilité du cercle collaboratif basé sur le zoom
                    if (isCollaborative) {
                        const updateCircleVisibility = () => {
                            const currentZoom = map.getZoom();
                            const iconElement = marker._icon;
                            if (iconElement) {
                                const ring = iconElement.querySelector('.collaborative-ring');
                                if (ring) {
                                    if (currentZoom < 7) {
                                        ring.style.display = 'none';
                                    } else {
                                        ring.style.display = 'block';
                                    }
                                }
                            }
                        };
                        
                        map.on('zoomend', updateCircleVisibility);
                        updateCircleVisibility();
                    }
                    const detailUrl = typeof window.recommendationDetailUrl === 'function' 
                        ? window.recommendationDetailUrl(trail.trail_id) 
                        : '#';
                    
                    // Build weather info for popup
                    let weatherInfo = '';
                    if (trail.forecast_weather) {
                        let weatherIcon = '';
                        if (trail.forecast_weather === 'sunny') weatherIcon = '☀️';
                        else if (trail.forecast_weather === 'cloudy') weatherIcon = '☁️';
                        else if (trail.forecast_weather === 'rainy') weatherIcon = '🌧️';
                        else if (trail.forecast_weather === 'snowy') weatherIcon = '❄️';
                        else if (trail.forecast_weather === 'storm_risk') weatherIcon = '⛈️';
                        else weatherIcon = '🌤️';
                        
                        const weatherText = trail.forecast_weather.charAt(0).toUpperCase() + trail.forecast_weather.slice(1);
                        weatherInfo = `<br/>${weatherIcon} ${weatherText}`;
                    }
                    
                    marker.bindPopup(`
                        <strong><a href="${detailUrl}">${trail.name}</a></strong><br/>
                        ${trail.distance || '—'} km · ${trail.trail_type || ''}${weatherInfo}
                    `);
                    bounds.push([lat, lon]);

                    if (geometry && geometry.coordinates && Array.isArray(geometry.coordinates)) {
                        const latLngs = geometry.coordinates.map(coord => [coord[1], coord[0]]);
                        const polyline = L.polyline(latLngs, {
                            color: iconColor,
                            opacity: 0.8,
                            weight: 3
                        }).addTo(map);
                        const polyBounds = polyline.getBounds();
                        bounds.push(polyBounds.getSouthWest(), polyBounds.getNorthEast());
                    }
                });

                if (bounds.length) {
                    map.fitBounds(bounds, { padding: [18, 18] });
                } else {
                    map.setView([45.8, 6.5], 8);
                }
                
                // Invalidate size after a short delay to ensure proper rendering
                setTimeout(() => {
                    if (map) {
                        map.invalidateSize();
                    }
                }, 100);
            }, 100);
        }
    }
})();
