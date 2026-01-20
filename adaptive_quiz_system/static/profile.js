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
        
        // Render charts
        if (data.heart_rate_zones) {
            renderHeartRateZonesChart(data.heart_rate_zones);
        }
        if (data.distance_over_time && data.distance_over_time.length > 0) {
            renderDistanceOverTimeChart(data.distance_over_time);
        }
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
    }
    
    function renderExplorationDashboard(data) {
        if (document.getElementById('unique-regions-count')) {
            document.getElementById('unique-regions-count').textContent = data.unique_regions ? data.unique_regions.length : '0';
        }
        if (document.getElementById('diversity-score')) {
            document.getElementById('diversity-score').textContent = data.trail_diversity_score || '0';
        }
    }
    
    function renderPhotographyDashboard(data) {
        if (document.getElementById('scenic-trails-count')) {
            document.getElementById('scenic-trails-count').textContent = data.scenic_trails ? data.scenic_trails.length : '0';
        }
    }
    
    function renderContemplativeDashboard(data) {
        if (document.getElementById('beauty-score')) {
            document.getElementById('beauty-score').textContent = data.scenic_beauty_score || '0';
        }
        if (document.getElementById('avg-time-spent')) {
            document.getElementById('avg-time-spent').textContent = Math.round(data.avg_time_spent || 0);
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
        if (data.performance_trends && data.performance_trends.length > 0) {
            renderPerformanceTrendsChart(data.performance_trends);
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
                labels: data.map(d => d.date),
                datasets: [{
                    label: 'Elevation Gain',
                    data: data.map(d => d.elevation_gain),
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            }
        });
    }
    
    function renderElevationDistributionChart(data) {
        const ctx = document.getElementById('elevation-distribution-chart');
        if (!ctx) return;
        
        if (charts.elevationDist) {
            charts.elevationDist.destroy();
        }
        
        charts.elevationDist = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    label: 'Trails',
                    data: Object.values(data),
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
                labels: data.map(d => d.date),
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
                labels: data.map(d => d.date),
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
                </div>
                <div class="dashboard-charts">
                    <div class="chart-container">
                        <canvas id="heart-rate-zones-chart"></canvas>
                    </div>
                    <div class="chart-container">
                        <canvas id="distance-over-time-chart"></canvas>
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
                </div>
                <div class="started-vs-completed">
                    <h3>Trail Status</h3>
                    <div class="chart-container">
                        <canvas id="started-vs-completed-chart"></canvas>
                    </div>
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
                </div>
                <div id="regions-list"></div>
            </div>`,
            photography: `<div class="dashboard-view photography-dashboard">
                <h2>Photography Dashboard</h2>
                <div class="dashboard-metrics">
                    <div class="metric-card">
                        <h3>Scenic Trails</h3>
                        <div class="metric-value" id="scenic-trails-count">-</div>
                    </div>
                </div>
                <div id="photo-opportunities-list"></div>
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
                </div>
                <div class="performance-trends">
                    <h3>Performance Trends</h3>
                    <div class="chart-container">
                        <canvas id="performance-trends-chart"></canvas>
                    </div>
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
