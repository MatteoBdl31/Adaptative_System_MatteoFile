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

            const map = this.mapManager.initMap('recommendations-map', {
                zoom: 8,
                center: [45.8, 6.5]
            });
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

                const iconColor = trail.view_type === 'recommended' ? '#5b8df9' : '#f59e0b';
                const icon = L.divIcon({
                    className: 'custom-marker',
                    html: `<div style="
                        background-color: ${iconColor};
                        width: 18px;
                        height: 18px;
                        border-radius: 50%;
                        border: 2px solid #fff;
                        box-shadow: 0 2px 6px rgba(0,0,0,.3);
                    "></div>`,
                    iconSize: [18, 18],
                    iconAnchor: [9, 9]
                });

                const marker = L.marker([lat, lon], { icon }).addTo(map);
                const detailUrl = typeof window.recommendationDetailUrl === 'function' 
                    ? window.recommendationDetailUrl(trail.trail_id) 
                    : '#';
                
                marker.bindPopup(`
                    <strong><a href="${detailUrl}">${trail.name}</a></strong><br/>
                    ${trail.distance || '—'} km · ${trail.trail_type || ''}
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
        }
    }
})();
