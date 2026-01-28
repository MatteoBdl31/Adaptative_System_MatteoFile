/**
 * Profile Page JavaScript
 * Handles dashboard switching, data fetching, and chart rendering
 */

const ProfileManager = (function() {
    'use strict';
    
    let currentUserId = null;
    let currentDashboard = null;
    let charts = {};
    
    function init(userId, defaultDashboard) {
        currentUserId = userId;
        currentDashboard = defaultDashboard;
        
        setupUserSelector();
        setupDashboardTabs();
        loadDashboard(defaultDashboard);
        loadTrails();
    }
    
    function setupUserSelector() {
        const selector = document.getElementById('user-select');
        if (selector) {
            selector.addEventListener('change', function() {
                const newUserId = parseInt(this.value);
                window.location.href = `/profile/${newUserId}`;
            });
        }
    }
    
    function setupDashboardTabs() {
        const tabs = document.querySelectorAll('.dashboard-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const dashboard = this.getAttribute('data-dashboard');
                
                // Update active tab
                tabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                
                // Load dashboard
                loadDashboard(dashboard);
            });
        });
    }
    
    function loadDashboard(dashboardType) {
        currentDashboard = dashboardType;
        const contentDiv = document.getElementById('dashboard-content');
        contentDiv.innerHTML = '<div class="loading">Loading dashboard...</div>';
        
        fetch(`/api/profile/${currentUserId}/dashboard/${dashboardType}`)
            .then(response => response.json())
            .then(data => {
                renderDashboard(dashboardType, data);
            })
            .catch(error => {
                console.error('Error loading dashboard:', error);
                contentDiv.innerHTML = '<div class="error">Error loading dashboard</div>';
            });
    }
    
    function renderDashboard(type, data) {
        const contentDiv = document.getElementById('dashboard-content');
        
        // Create inline template
        contentDiv.innerHTML = createInlineTemplate(type);
        
        // Render dashboard-specific content
        setTimeout(() => {
            switch(type) {
                case 'elevation':
                    renderElevationDashboard(data);
                    break;
                case 'fitness':
                    renderFitnessDashboard(data);
                    break;
                case 'persistence':
                    renderPersistenceDashboard(data);
                    break;
                case 'exploration':
                    renderExplorationDashboard(data);
                    break;
                case 'photography':
                    renderPhotographyDashboard(data);
                    break;
                case 'contemplative':
                    renderContemplativeDashboard(data);
                    break;
                case 'performance':
                    renderPerformanceDashboard(data);
                    break;
            }
        }, 100);
    }
    
    function renderElevationDashboard(data) {
        // Update metrics
        if (document.getElementById('highest-point')) {
            document.getElementById('highest-point').textContent = data.highest_point || '0';
        }
        if (document.getElementById('avg-elevation-speed')) {
            document.getElementById('avg-elevation-speed').textContent = data.avg_elevation_speed || '0';
        }
        
        // Render charts
        if (data.elevation_gain_over_time && data.elevation_gain_over_time.length > 0) {
            renderElevationOverTimeChart(data.elevation_gain_over_time);
        }
        if (data.elevation_distribution) {
            renderElevationDistributionChart(data.elevation_distribution);
        }
        
        // Render top trails
        if (data.top_elevation_trails && document.getElementById('top-elevation-trails-list')) {
            const list = document.getElementById('top-elevation-trails-list');
            list.innerHTML = data.top_elevation_trails.slice(0, 5).map(trail => `
                <div class="trail-item">
                    <strong>${trail.name || trail.trail_id}</strong>
                    <span>${trail.elevation_gain}m elevation</span>
                </div>
            `).join('');
        }
    }
    
    function renderFitnessDashboard(data) {
        // Update metric cards
        if (document.getElementById('total-calories')) {
            document.getElementById('total-calories').textContent = data.calories_burned || '0';
        }
        if (document.getElementById('avg-heart-rate')) {
            const avgHR = data.heart_rate_zones?.avg ||
                          (data.heart_rate_trends && data.heart_rate_trends.length > 0
                           ? Math.round(data.heart_rate_trends.reduce((sum, t) => sum + (t.avg || 0), 0) / data.heart_rate_trends.length)
                           : 0);
            document.getElementById('avg-heart-rate').textContent = avgHR || '0';
        }
        if (document.getElementById('max-heart-rate')) {
            const maxHR = data.heart_rate_zones?.max ||
                          (data.heart_rate_trends && data.heart_rate_trends.length > 0
                           ? Math.max(...data.heart_rate_trends.map(t => t.max || 0))
                           : 0);
            document.getElementById('max-heart-rate').textContent = maxHR || '0';
        }
        // Training consistency
        const tc = data.training_consistency;
        const tpmEl = document.getElementById('trails-per-month');
        const csEl = document.getElementById('consistency-score');
        if (tpmEl) tpmEl.textContent = (tc && tc.trails_per_month != null) ? tc.trails_per_month : '-';
        if (csEl) csEl.textContent = (tc && tc.consistency_score != null) ? tc.consistency_score : '-';

        // Render charts
        if (data.heart_rate_zones) {
            renderHeartRateZonesChart(data.heart_rate_zones);
        }
        if (data.distance_over_time && data.distance_over_time.length > 0) {
            renderDistanceOverTimeChart(data.distance_over_time);
        }
        // Speed trends chart
        if (data.speed_trends && data.speed_trends.length > 0) {
            renderSpeedTrendsChart(data.speed_trends);
        } else {
            if (charts.speedTrends) {
                charts.speedTrends.destroy();
                charts.speedTrends = null;
            }
            const speedContainer = document.getElementById('speed-trends-chart-container');
            if (speedContainer) speedContainer.style.display = 'none';
        }
    }

    function renderSpeedTrendsChart(data) {
        const ctx = document.getElementById('speed-trends-chart');
        if (!ctx) return;
        if (charts.speedTrends) {
            charts.speedTrends.destroy();
        }
        const container = document.getElementById('speed-trends-chart-container');
        if (container) container.style.display = '';
        charts.speedTrends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => formatDate(d.date)),
                datasets: [
                    { label: 'Avg speed (km/h)', data: data.map(d => d.avg), borderColor: 'rgb(75, 192, 192)', tension: 0.1 },
                    { label: 'Max speed (km/h)', data: data.map(d => d.max), borderColor: 'rgb(255, 99, 132)', tension: 0.1 }
                ]
            },
            options: {
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
    
    function renderPersistenceDashboard(data) {
        if (document.getElementById('completion-rate')) {
            document.getElementById('completion-rate').textContent = data.completion_rate || '0';
        }
        if (document.getElementById('longest-streak')) {
            document.getElementById('longest-streak').textContent = data.longest_streak || '0';
        }
        if (data.started_vs_completed) {
            renderStartedVsCompletedChart(data.started_vs_completed);
        }
        if (document.getElementById('persistence-score')) {
            const v = data.persistence_score;
            document.getElementById('persistence-score').textContent = (v != null && v !== '') ? (Math.round(Number(v) * 100) / 100) : '-';
        }
        // Abandoned trails list
        const abandonedList = document.getElementById('abandoned-trails-list');
        if (abandonedList) {
            if (data.abandoned_trails && data.abandoned_trails.length > 0) {
                abandonedList.innerHTML = `
                    <table class="dashboard-table">
                        <thead><tr><th>Trail</th><th>Started</th><th>Progress</th></tr></thead>
                        <tbody>
                            ${data.abandoned_trails.map(t => `
                                <tr>
                                    <td><a href="/profile/${currentUserId}/trail/${t.trail_id}" class="trail-link">${escapeHtml(t.name || t.trail_id)}</a></td>
                                    <td>${formatDate(t.start_date)}</td>
                                    <td>${(t.progress != null ? (Number(t.progress) * 100).toFixed(0) : '0')}%</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>`;
            } else {
                abandonedList.innerHTML = '<p class="dashboard-empty">No abandoned trails.</p>';
            }
        }
        // Difficulty progression chart
        const diffChartContainer = document.getElementById('difficulty-progression-chart-container');
        const diffEmptyEl = document.getElementById('difficulty-progression-empty');
        if (data.difficulty_progression && data.difficulty_progression.length > 0) {
            if (diffChartContainer) diffChartContainer.style.display = '';
            if (diffEmptyEl) diffEmptyEl.style.display = 'none';
            renderDifficultyProgressionChart(data.difficulty_progression);
        } else {
            if (charts.difficultyProgression) {
                charts.difficultyProgression.destroy();
                charts.difficultyProgression = null;
            }
            if (diffChartContainer) diffChartContainer.style.display = 'none';
            if (diffEmptyEl) diffEmptyEl.style.display = 'block';
        }
        // Completion time comparison (estimated vs actual)
        const timeCompareList = document.getElementById('completion-time-comparison-list');
        if (timeCompareList) {
            if (data.completion_time_comparison && data.completion_time_comparison.length > 0) {
                timeCompareList.innerHTML = `
                    <table class="dashboard-table">
                        <thead><tr><th>Trail</th><th>Est. (min)</th><th>Actual (min)</th><th>Diff %</th></tr></thead>
                        <tbody>
                            ${data.completion_time_comparison.slice(0, 10).map(t => `
                                <tr>
                                    <td><a href="/profile/${currentUserId}/trail/${t.trail_id}" class="trail-link">${escapeHtml((t.name || t.trail_id).substring(0, 30))}${(t.name || '').length > 30 ? '…' : ''}</a></td>
                                    <td>${t.estimated || '-'}</td>
                                    <td>${t.actual || '-'}</td>
                                    <td>${t.percentage != null ? (t.difference >= 0 ? '+' : '') + (t.percentage - 100).toFixed(0) + '%' : '-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>`;
            } else {
                timeCompareList.innerHTML = '<p class="dashboard-empty">No completion time data yet.</p>';
            }
        }
    }

    function formatDate(s) {
        if (!s) return '-';
        try {
            const d = s.split('T')[0];
            if (!d) return s;
            const [y, m, day] = d.split('-');
            return [day, m, y].filter(Boolean).join('/') || s;
        } catch (_) { return s; }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function renderDifficultyProgressionChart(data) {
        const ctx = document.getElementById('difficulty-progression-chart');
        if (!ctx) return;
        if (charts.difficultyProgression) {
            charts.difficultyProgression.destroy();
        }
        charts.difficultyProgression = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => formatDate(d.date)),
                datasets: [{
                    label: 'Difficulty',
                    data: data.map(d => d.difficulty),
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
    
    function renderExplorationDashboard(data) {
        if (document.getElementById('unique-regions-count')) {
            document.getElementById('unique-regions-count').textContent = data.unique_regions ? data.unique_regions.length : '0';
        }
        if (document.getElementById('diversity-score')) {
            document.getElementById('diversity-score').textContent = data.trail_diversity_score || '0';
        }
        if (document.getElementById('exploration-level')) {
            const v = data.exploration_level;
            document.getElementById('exploration-level').textContent = (v != null && v !== '') ? (Math.round(Number(v) * 100) / 100) : '-';
        }
        // Regions list
        const regionsList = document.getElementById('regions-list');
        if (regionsList) {
            if (data.unique_regions && data.unique_regions.length > 0) {
                regionsList.innerHTML = '<ul class="dashboard-tag-list">' +
                    data.unique_regions.map(r => `<li class="dashboard-tag">${escapeHtml(r)}</li>`).join('') +
                    '</ul>';
            } else {
                regionsList.innerHTML = '<p class="dashboard-empty">No regions visited yet.</p>';
            }
        }
        // Landscapes discovered (tags with counts)
        const landscapesEl = document.getElementById('landscapes-discovered-tags');
        if (landscapesEl) {
            const ld = data.landscapes_discovered;
            if (ld && typeof ld === 'object' && Object.keys(ld).length > 0) {
                landscapesEl.innerHTML = '<div class="dashboard-tag-cloud">' +
                    Object.entries(ld).map(([name, count]) =>
                        `<span class="dashboard-tag dashboard-tag--count" title="${escapeHtml(String(count))} trails">${escapeHtml(name)} <em>${count}</em></span>`
                    ).join('') +
                    '</div>';
            } else {
                landscapesEl.innerHTML = '<p class="dashboard-empty">Complete trails to discover landscapes.</p>';
            }
        }
        // Uncharted suggestions (trails in new regions)
        const unchartedList = document.getElementById('uncharted-suggestions-list');
        if (unchartedList) {
            const u = data.uncharted_suggestions;
            if (u && Array.isArray(u) && u.length > 0) {
                unchartedList.innerHTML = '<ul class="dashboard-trail-list">' +
                    u.map(t => `
                        <li><a href="/profile/${currentUserId}/trail/${t.trail_id}" class="trail-link">${escapeHtml(t.name || t.trail_id)}</a>
                        <span class="dashboard-meta">${escapeHtml(t.region || '')} · ${t.distance != null ? t.distance + ' km' : '-'} · diff ${t.difficulty != null ? t.difficulty : '-'}</span>
                        </li>
                    `).join('') +
                    '</ul>';
            } else {
                unchartedList.innerHTML = '<p class="dashboard-empty">You\'ve explored all regions we suggest, or complete a trail to get suggestions.</p>';
            }
        }
    }
    
    function renderPhotographyDashboard(data) {
        if (document.getElementById('scenic-trails-count')) {
            document.getElementById('scenic-trails-count').textContent = data.scenic_trails ? data.scenic_trails.length : '0';
        }
        if (document.getElementById('trail-photos-count')) {
            document.getElementById('trail-photos-count').textContent = (data.trail_photos_count != null) ? data.trail_photos_count : '0';
        }
        // Photo opportunities: prefer instagram_locations, fallback to best_photo_opportunities
        const listEl = document.getElementById('photo-opportunities-list');
        if (listEl) {
            const items = (data.instagram_locations && data.instagram_locations.length > 0)
                ? data.instagram_locations
                : (data.best_photo_opportunities || []);
            if (items.length > 0) {
                listEl.innerHTML = '<h3>Photo opportunities</h3><ul class="dashboard-trail-list">' +
                    items.slice(0, 10).map(t => `
                        <li><a href="/profile/${currentUserId}/trail/${t.trail_id}" class="trail-link">${escapeHtml(t.name || t.trail_id)}</a>
                        ${t.popularity != null ? `<span class="dashboard-meta">★ ${t.popularity}</span>` : ''}
                        ${t.landscapes ? `<span class="dashboard-meta">${escapeHtml(String(t.landscapes).substring(0, 40))}${String(t.landscapes).length > 40 ? '…' : ''}</span>` : ''}
                        </li>
                    `).join('') +
                    '</ul>';
            } else {
                listEl.innerHTML = '<p class="dashboard-empty">Complete scenic trails to see photo opportunities.</p>';
            }
        }
        // Recent photos strip
        const recentList = document.getElementById('recent-photos-list');
        if (recentList) {
            const rp = data.recent_photos;
            if (rp && Array.isArray(rp) && rp.length > 0) {
                recentList.innerHTML = '<ul class="dashboard-trail-list recent-photos-list">' +
                    rp.map(p => {
                        const trailLink = `<a href="/profile/${currentUserId}/trail/${p.trail_id}" class="trail-link">${escapeHtml(p.trail_name || p.trail_id)}</a>`;
                        const img = (p.photo_path && (p.photo_path.startsWith('/') || p.photo_path.startsWith('http')))
                            ? `<img src="${escapeHtml(p.photo_path)}" alt="" class="recent-photo-thumb" loading="lazy">`
                            : '';
                        return `<li>${img}<span>${trailLink}${p.caption ? ' · ' + escapeHtml(p.caption) : ''}</span></li>`;
                    }).join('') +
                    '</ul>';
            } else {
                recentList.innerHTML = '<p class="dashboard-empty">Upload photos when completing trails to see them here.</p>';
            }
        }
    }
    
    function renderContemplativeDashboard(data) {
        if (document.getElementById('beauty-score')) {
            document.getElementById('beauty-score').textContent = data.scenic_beauty_score || '0';
        }
        if (document.getElementById('avg-time-spent')) {
            document.getElementById('avg-time-spent').textContent = Math.round(data.avg_time_spent || 0);
        }
        // Nature immersion
        const ni = data.nature_immersion;
        const pctEl = document.getElementById('nature-immersion-pct');
        const detailEl = document.getElementById('nature-immersion-detail');
        if (pctEl) {
            if (ni && typeof ni === 'object') {
                pctEl.textContent = (ni.percentage != null ? ni.percentage : 0) + '%';
                if (detailEl && ni.total_nature_trails != null) {
                    detailEl.textContent = (ni.total_nature_trails || 0) + ' nature trails';
                }
            } else {
                pctEl.textContent = '0';
                if (detailEl) detailEl.textContent = '';
            }
        }
        // Meditation-friendly list
        const mfList = document.getElementById('meditation-friendly-list');
        if (mfList) {
            const mf = data.meditation_friendly;
            if (mf && Array.isArray(mf) && mf.length > 0) {
                mfList.innerHTML = '<ul class="dashboard-trail-list">' +
                    mf.slice(0, 8).map(t => `
                        <li><a href="/profile/${currentUserId}/trail/${t.trail_id}" class="trail-link">${escapeHtml(t.name || t.trail_id)}</a>
                        <span class="dashboard-meta">${t.duration || '-'} min · popularity ${t.popularity != null ? t.popularity : '-'}</span>
                        </li>
                    `).join('') +
                    '</ul>';
            } else {
                mfList.innerHTML = '<p class="dashboard-empty">No meditation-friendly trails in your history yet.</p>';
            }
        }
    }
    
    function renderPerformanceDashboard(data) {
        if (data.personal_records) {
            const prDiv = document.getElementById('personal-records');
            if (prDiv) {
                prDiv.innerHTML = `
                    <div>Longest: ${data.personal_records.longest_distance || 0}km</div>
                    <div>Highest: ${data.personal_records.highest_elevation || 0}m</div>
                `;
            }
        }
        if (document.getElementById('activity-frequency')) {
            const v = data.activity_frequency;
            document.getElementById('activity-frequency').textContent = (v != null && v !== '') ? v : '-';
        }
        if (document.getElementById('avg-difficulty-completed')) {
            const v = data.avg_difficulty_completed;
            document.getElementById('avg-difficulty-completed').textContent = (v != null && v !== '') ? (Number(v).toFixed(1)) : '-';
        }
        // Improvement metrics (recent vs older half)
        const imDiv = document.getElementById('improvement-metrics');
        if (imDiv) {
            const im = data.improvement_metrics;
            if (im && (im.distance_improvement != null || im.difficulty_improvement != null)) {
                const dist = im.distance_improvement != null ? im.distance_improvement : 0;
                const diff = im.difficulty_improvement != null ? im.difficulty_improvement : 0;
                imDiv.innerHTML = `
                    <div class="improvement-row">Distance: <strong>${dist >= 0 ? '+' : ''}${dist} km</strong> (recent vs earlier)</div>
                    <div class="improvement-row">Difficulty: <strong>${diff >= 0 ? '+' : ''}${diff}</strong> (recent vs earlier)</div>
                `;
            } else {
                imDiv.innerHTML = '<p class="dashboard-empty">Complete more trails to see improvement.</p>';
            }
        }
        if (data.performance_trends && data.performance_trends.length > 0) {
            renderPerformanceTrendsChart(data.performance_trends);
        }
        // Vs predictions (from performance-improvements)
        const pi = data.performance_improvements;
        const pvpc = document.getElementById('performance-vs-predictions-content');
        if (pvpc) {
            if (pi && (pi.avg_duration_diff_pct != null || pi.avg_hr_diff_pct != null || pi.avg_speed_diff_pct != null)) {
                const fmt = (v) => (v == null || v === '') ? '-' : (Number(v) >= 0 ? '+' : '') + Number(v).toFixed(1) + '%';
                let html = '<p class="vs-predictions-summary">';
                if (pi.avg_duration_diff_pct != null) html += `Duration: <strong>${fmt(pi.avg_duration_diff_pct)}</strong> vs predicted. `;
                if (pi.avg_hr_diff_pct != null) html += `Heart rate: <strong>${fmt(pi.avg_hr_diff_pct)}</strong>. `;
                if (pi.avg_speed_diff_pct != null) html += `Speed: <strong>${fmt(pi.avg_speed_diff_pct)}</strong>.`;
                html += '</p>';
                if (pi.improvements && pi.improvements.length > 0) {
                    html += '<table class="dashboard-table"><thead><tr><th>Date</th><th>Duration diff %</th><th>HR diff %</th><th>Speed diff %</th></tr></thead><tbody>';
                    pi.improvements.slice(0, 6).forEach(i => {
                        const d = (i.completion_date || '').split('T')[0];
                        html += `<tr><td>${escapeHtml(d)}</td><td>${fmt(i.duration_diff_pct)}</td><td>${fmt(i.hr_diff_pct)}</td><td>${fmt(i.speed_diff_pct)}</td></tr>`;
                    });
                    html += '</tbody></table>';
                }
                pvpc.innerHTML = html;
            } else {
                pvpc.innerHTML = '<p class="dashboard-empty">Complete trails with predicted metrics to see vs predictions.</p>';
            }
        }
    }
    
    function renderElevationOverTimeChart(data) {
        const ctx = document.getElementById('elevation-over-time-chart');
        if (!ctx) return;
        
        if (charts.elevationOverTime) {
            charts.elevationOverTime.destroy();
        }
        
        charts.elevationOverTime = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => formatDate(d.date)),
                datasets: [{
                    label: 'Elevation Gain',
                    data: data.map(d => d.elevation_gain),
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            }
        });
    }
    
    const ELEVATION_BUCKET_ORDER = ['0-300m', '300-600m', '600-900m', '900-1200m', '1200m+'];

    function renderElevationDistributionChart(data) {
        const ctx = document.getElementById('elevation-distribution-chart');
        if (!ctx) return;
        
        if (charts.elevationDist) {
            charts.elevationDist.destroy();
        }
        
        const labels = ELEVATION_BUCKET_ORDER;
        const values = ELEVATION_BUCKET_ORDER.map(k => (data[k] != null ? data[k] : 0));
        
        charts.elevationDist = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Trails',
                    data: values,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)'
                }]
            }
        });
    }
    
    function renderHeartRateZonesChart(zones) {
        const ctx = document.getElementById('heart-rate-zones-chart');
        if (!ctx) return;
        
        if (charts.hrZones) {
            charts.hrZones.destroy();
        }
        
        charts.hrZones = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Resting', 'Active', 'Peak'],
                datasets: [{
                    data: [zones.resting || 0, zones.active || 0, zones.peak || 0],
                    backgroundColor: ['#36A2EB', '#FFCE56', '#FF6384']
                }]
            }
        });
    }
    
    function renderDistanceOverTimeChart(data) {
        const ctx = document.getElementById('distance-over-time-chart');
        if (!ctx) return;
        
        if (charts.distanceOverTime) {
            charts.distanceOverTime.destroy();
        }
        
        charts.distanceOverTime = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => formatDate(d.date)),
                datasets: [{
                    label: 'Distance',
                    data: data.map(d => d.distance),
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1
                }]
            }
        });
    }
    
    function renderStartedVsCompletedChart(data) {
        const ctx = document.getElementById('started-vs-completed-chart');
        if (!ctx) return;
        
        if (charts.startedVsCompleted) {
            charts.startedVsCompleted.destroy();
        }
        
        charts.startedVsCompleted = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Started', 'Completed', 'Saved'],
                datasets: [{
                    data: [data.started || 0, data.completed || 0, data.saved || 0],
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                layout: {
                    padding: {
                        top: 10,
                        bottom: 10,
                        left: 10,
                        right: 10
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 10,
                            boxWidth: 12
                        }
                    }
                }
            }
        });
    }
    
    function renderPerformanceTrendsChart(data) {
        const ctx = document.getElementById('performance-trends-chart');
        if (!ctx) return;
        
        if (charts.performanceTrends) {
            charts.performanceTrends.destroy();
        }
        
        charts.performanceTrends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => formatDate(d.date)),
                datasets: [{
                    label: 'Distance',
                    data: data.map(d => d.distance),
                    borderColor: 'rgb(75, 192, 192)',
                    yAxisID: 'y'
                }, {
                    label: 'Difficulty',
                    data: data.map(d => d.difficulty),
                    borderColor: 'rgb(255, 99, 132)',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                layout: {
                    padding: {
                        top: 10,
                        bottom: 10,
                        left: 10,
                        right: 10
                    }
                },
                scales: {
                    y: { 
                        type: 'linear', 
                        position: 'left',
                        ticks: {
                            padding: 5
                        }
                    },
                    y1: { 
                        type: 'linear', 
                        position: 'right', 
                        grid: { drawOnChartArea: false },
                        ticks: {
                            padding: 5
                        }
                    },
                    x: {
                        ticks: {
                            padding: 5
                        }
                    }
                }
            }
        });
    }
    
    function loadTrails() {
        if (typeof TrailListManager !== 'undefined') {
            TrailListManager.loadTrails(currentUserId);
        }
    }
    
    function createInlineTemplate(type) {
        const templates = {
            elevation: `<div class="dashboard-view elevation-dashboard">
                <h2>Elevation Dashboard</h2>
                <div class="dashboard-metrics">
                    <div class="metric-card">
                        <h3>Highest Point</h3>
                        <div class="metric-value" id="highest-point">-</div>
                        <div class="metric-unit">meters</div>
                    </div>
                    <div class="metric-card">
                        <h3>Avg Elevation Speed</h3>
                        <div class="metric-value" id="avg-elevation-speed">-</div>
                        <div class="metric-unit">m/hour</div>
                    </div>
                </div>
                <div class="dashboard-charts">
                    <div class="chart-container">
                        <canvas id="elevation-over-time-chart"></canvas>
                    </div>
                    <div class="chart-container">
                        <canvas id="elevation-distribution-chart"></canvas>
                    </div>
                </div>
                <div class="top-trails">
                    <h3>Top Elevation Trails</h3>
                    <div id="top-elevation-trails-list"></div>
                </div>
            </div>`,
            fitness: `<div class="dashboard-view fitness-dashboard">
                <h2>Fitness Dashboard</h2>
                <div class="dashboard-metrics">
                    <div class="metric-card">
                        <h3>Total Calories</h3>
                        <div class="metric-value" id="total-calories">-</div>
                    </div>
                    <div class="metric-card">
                        <h3>Avg Heart Rate</h3>
                        <div class="metric-value" id="avg-heart-rate">-</div>
                        <div class="metric-unit">bpm</div>
                    </div>
                    <div class="metric-card">
                        <h3>Max Heart Rate</h3>
                        <div class="metric-value" id="max-heart-rate">-</div>
                        <div class="metric-unit">bpm</div>
                    </div>
                    <div class="metric-card" id="fitness-consistency-card">
                        <h3>Trails / month</h3>
                        <div class="metric-value" id="trails-per-month">-</div>
                    </div>
                    <div class="metric-card">
                        <h3>Consistency score</h3>
                        <div class="metric-value" id="consistency-score">-</div>
                        <div class="metric-unit">0–100</div>
                    </div>
                </div>
                <div class="dashboard-charts">
                    <div class="chart-container">
                        <canvas id="heart-rate-zones-chart"></canvas>
                    </div>
                    <div class="chart-container">
                        <canvas id="distance-over-time-chart"></canvas>
                    </div>
                    <div class="chart-container" id="speed-trends-chart-container">
                        <canvas id="speed-trends-chart"></canvas>
                    </div>
                </div>
            </div>`,
            persistence: `<div class="dashboard-view persistence-dashboard">
                <h2>Persistence Dashboard</h2>
                <div class="dashboard-metrics">
                    <div class="metric-card">
                        <h3>Completion Rate</h3>
                        <div class="metric-value" id="completion-rate">-</div>
                        <div class="metric-unit">%</div>
                    </div>
                    <div class="metric-card">
                        <h3>Longest Streak</h3>
                        <div class="metric-value" id="longest-streak">-</div>
                        <div class="metric-unit">trails</div>
                    </div>
                    <div class="metric-card" id="persistence-score-card">
                        <h3>Persistence score</h3>
                        <div class="metric-value" id="persistence-score">-</div>
                        <div class="metric-unit">0–1</div>
                    </div>
                </div>
                <div class="started-vs-completed">
                    <h3>Trail Status</h3>
                    <div class="chart-container">
                        <canvas id="started-vs-completed-chart"></canvas>
                    </div>
                </div>
                <div class="persistence-abandoned" id="persistence-abandoned-section">
                    <h3>Abandoned Trails</h3>
                    <div id="abandoned-trails-list"></div>
                </div>
                <div class="persistence-difficulty-progression" id="persistence-difficulty-section">
                    <h3>Difficulty Progression</h3>
                    <div class="chart-container" id="difficulty-progression-chart-container">
                        <canvas id="difficulty-progression-chart"></canvas>
                    </div>
                    <p id="difficulty-progression-empty" class="dashboard-empty" style="display:none">Complete more trails to see difficulty progression.</p>
                </div>
                <div class="persistence-time-comparison" id="persistence-time-comparison-section">
                    <h3>Estimated vs Actual Time</h3>
                    <div id="completion-time-comparison-list"></div>
                </div>
            </div>`,
            exploration: `<div class="dashboard-view exploration-dashboard">
                <h2>Exploration Dashboard</h2>
                <div class="dashboard-metrics">
                    <div class="metric-card">
                        <h3>Unique Regions</h3>
                        <div class="metric-value" id="unique-regions-count">-</div>
                    </div>
                    <div class="metric-card">
                        <h3>Diversity Score</h3>
                        <div class="metric-value" id="diversity-score">-</div>
                    </div>
                    <div class="metric-card" id="exploration-level-card">
                        <h3>Exploration level</h3>
                        <div class="metric-value" id="exploration-level">-</div>
                        <div class="metric-unit">0–1</div>
                    </div>
                </div>
                <div class="exploration-regions" id="exploration-regions-section">
                    <h3>Regions Visited</h3>
                    <div id="regions-list"></div>
                </div>
                <div class="exploration-landscapes" id="exploration-landscapes-section">
                    <h3>Landscapes Discovered</h3>
                    <div id="landscapes-discovered-tags"></div>
                </div>
                <div class="exploration-uncharted" id="exploration-uncharted-section">
                    <h3>Suggested new regions</h3>
                    <div id="uncharted-suggestions-list"></div>
                </div>
            </div>`,
            photography: `<div class="dashboard-view photography-dashboard">
                <h2>Photography Dashboard</h2>
                <div class="dashboard-metrics">
                    <div class="metric-card">
                        <h3>Scenic Trails</h3>
                        <div class="metric-value" id="scenic-trails-count">-</div>
                    </div>
                    <div class="metric-card">
                        <h3>Your trail photos</h3>
                        <div class="metric-value" id="trail-photos-count">-</div>
                    </div>
                </div>
                <div id="photo-opportunities-list"></div>
                <div class="photography-recent-photos" id="photography-recent-photos-section">
                    <h3>Recent photos</h3>
                    <div id="recent-photos-list"></div>
                </div>
            </div>`,
            contemplative: `<div class="dashboard-view contemplative-dashboard">
                <h2>Contemplative Dashboard</h2>
                <div class="dashboard-metrics">
                    <div class="metric-card">
                        <h3>Scenic Beauty Score</h3>
                        <div class="metric-value" id="beauty-score">-</div>
                    </div>
                    <div class="metric-card">
                        <h3>Avg Time Spent</h3>
                        <div class="metric-value" id="avg-time-spent">-</div>
                        <div class="metric-unit">minutes</div>
                    </div>
                    <div class="metric-card" id="contemplative-nature-card">
                        <h3>Nature Immersion</h3>
                        <div class="metric-value" id="nature-immersion-pct">-</div>
                        <div class="metric-unit" id="nature-immersion-detail"></div>
                    </div>
                </div>
                <div class="contemplative-meditation" id="contemplative-meditation-section">
                    <h3>Meditation-friendly trails</h3>
                    <div id="meditation-friendly-list"></div>
                </div>
            </div>`,
            performance: `<div class="dashboard-view performance-dashboard">
                <h2>Performance Analytics Dashboard</h2>
                <div class="dashboard-metrics">
                    <div class="metric-card">
                        <h3>Personal Records</h3>
                        <div id="personal-records"></div>
                    </div>
                    <div class="metric-card">
                        <h3>Improvement</h3>
                        <div id="improvement-metrics"></div>
                    </div>
                    <div class="metric-card">
                        <h3>Hikes / month</h3>
                        <div class="metric-value" id="activity-frequency">-</div>
                    </div>
                    <div class="metric-card">
                        <h3>Avg difficulty (completed)</h3>
                        <div class="metric-value" id="avg-difficulty-completed">-</div>
                    </div>
                </div>
                <div class="performance-trends">
                    <h3>Performance Trends</h3>
                    <div class="chart-container">
                        <canvas id="performance-trends-chart"></canvas>
                    </div>
                </div>
                <div class="performance-vs-predictions" id="performance-vs-predictions-section">
                    <h3>Vs predictions</h3>
                    <div id="performance-vs-predictions-content"></div>
                </div>
            </div>`
        };
        
        return templates[type] || `<div class="dashboard-view ${type}-dashboard">
            <h2>${type.charAt(0).toUpperCase() + type.slice(1)} Dashboard</h2>
            <div class="dashboard-content-placeholder">Dashboard content will be loaded here</div>
        </div>`;
    }
    
    return {
        init: init,
        loadDashboard: loadDashboard,
        loadTrails: loadTrails
    };
})();
