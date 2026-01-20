(() => {
    function setupViewToggles() {
        document.querySelectorAll("[data-view-toggle]").forEach((toggle) => {
            const panels = document.querySelector("[data-view-panels]");
            if (!panels) return;
            const targetButtons = toggle.querySelectorAll(".toggle-btn");
            targetButtons.forEach((btn) => {
                btn.addEventListener("click", () => {
                    const target = btn.getAttribute("data-view-target");
                    if (!target) return;
                    panels.dataset.activeView = target;
                    panels.querySelectorAll("[data-view-panel]").forEach((panel) => {
                        panel.classList.toggle("hide", panel.getAttribute("data-view-panel") !== target);
                    });
                    targetButtons.forEach((button) => button.classList.toggle("is-active", button === btn));
                    if (window.recommendationsMap && target === "map") {
                        setTimeout(() => window.recommendationsMap.invalidateSize(), 200);
                    }
                });
            });
        });
    }

    function initRecommendationMap() {
        if (typeof L === "undefined") return;
        const container = document.getElementById("recommendations-map");
        if (!container || !Array.isArray(window.recommendationMapData)) return;
        if (!window.recommendationMapData.length) return;

        // Check if map already exists and remove it
        if (window.recommendationsMap) {
            try {
                window.recommendationsMap.remove();
            } catch (e) {
                // Ignore errors
            }
        }
        if (container._leaflet_id) {
            container.innerHTML = '';
            delete container._leaflet_id;
        }
        const map = L.map(container);
        window.recommendationsMap = map;
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap contributors",
            maxZoom: 19,
        }).addTo(map);

        const bounds = [];
        window.recommendationMapData.forEach((trail) => {
            const lat = trail.latitude ?? trail.lat;
            const lon = trail.longitude ?? trail.lon;
            if (lat == null || lon == null) return;

            let geometry = trail.coordinates;
            if (typeof geometry === "string") {
                try {
                    geometry = JSON.parse(geometry);
                } catch {
                    geometry = null;
                }
            }

            const iconColor = trail.view_type === "recommended" ? "#5b8df9" : "#f59e0b";
            const icon = L.divIcon({
                className: "custom-marker",
                html: `<div style="background-color:${iconColor};width:18px;height:18px;border-radius:50%;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);"></div>`,
                iconSize: [18, 18],
                iconAnchor: [9, 9],
            });

            const marker = L.marker([lat, lon], { icon }).addTo(map);
            const detailUrl = typeof window.recommendationDetailUrl === "function" ? window.recommendationDetailUrl(trail.trail_id) : "#";
            marker.bindPopup(`<strong><a href="${detailUrl}">${trail.name}</a></strong><br/>${trail.distance || "—"} km · ${trail.trail_type || ""}`);
            bounds.push([lat, lon]);

            if (geometry && geometry.coordinates && Array.isArray(geometry.coordinates)) {
                const latLngs = geometry.coordinates.map((coord) => [coord[1], coord[0]]);
                const polyline = L.polyline(latLngs, {
                    color: iconColor,
                    opacity: 0.8,
                    weight: 3,
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

    document.addEventListener("DOMContentLoaded", () => {
        setupViewToggles();
        initRecommendationMap();
    });
})();
