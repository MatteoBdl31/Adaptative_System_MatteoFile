/**
 * Trail List JavaScript
 * Handles displaying trails, status indicators, filtering, and actions
 */

const TrailListManager = (function() {
    'use strict';
    
    let currentUserId = null;
    let currentUserProfile = null; // Store user profile
    let trails = { saved: [], started: [], completed: [] };
    let currentViewMode = 'grid'; // grid, list, timeline
    let currentFilters = {};
    let currentSort = 'date-desc';
    let searchQuery = '';
    
    // Profile-to-default-tab mapping
    function getProfileDefaultTab(userProfile) {
        const profileTabMap = {
            'elevation_lover': 'elevation',
            'explorer': 'map',
            'photographer': 'gallery',
            'performance_athlete': 'performance',
            'contemplative': 'overview',
            'casual': 'overview',
            'family': 'overview'
        };
        return profileTabMap[userProfile] || 'overview';
    }
    
    // Profile-to-tab-priority mapping (order tabs based on profile)
    function getTabOrderForProfile(userProfile) {
        const tabOrders = {
            'elevation_lover': ['overview', 'elevation', 'performance', 'weather', 'map', 'gallery', 'recommendations'],
            'explorer': ['overview', 'map', 'weather', 'performance', 'elevation', 'gallery', 'recommendations'],
            'photographer': ['overview', 'gallery', 'map', 'weather', 'recommendations', 'elevation', 'performance'],
            'performance_athlete': ['overview', 'performance', 'elevation', 'weather', 'map', 'gallery', 'recommendations'],
            'contemplative': ['overview', 'gallery', 'weather', 'recommendations', 'map', 'elevation', 'performance'],
            'casual': ['overview', 'weather', 'recommendations', 'map', 'gallery', 'elevation', 'performance'],
            'family': ['overview', 'weather', 'recommendations', 'map', 'gallery', 'elevation', 'performance']
        };
        return tabOrders[userProfile] || ['overview', 'performance', 'weather', 'recommendations', 'elevation', 'map', 'gallery'];
    }
    
    // Reorder tabs based on profile
    function reorderTabsForProfile(userProfile) {
        const tabsContainer = document.getElementById('trail-detail-tabs');
        if (!tabsContainer) return;
        
        const tabOrder = getTabOrderForProfile(userProfile);
        const defaultTab = getProfileDefaultTab(userProfile);
        
        // Get all tabs
        const tabs = Array.from(tabsContainer.querySelectorAll('.detail-tab'));
        const tabMap = {};
        tabs.forEach(tab => {
            const tabId = tab.getAttribute('data-tab');
            tabMap[tabId] = tab;
        });
        
        // Clear container
        tabsContainer.innerHTML = '';
        
        // Reorder tabs based on profile priority
        tabOrder.forEach(tabId => {
            if (tabMap[tabId]) {
                tabsContainer.appendChild(tabMap[tabId]);
                // Set active tab based on profile default
                if (tabId === defaultTab) {
                    tabMap[tabId].classList.add('active');
                } else {
                    tabMap[tabId].classList.remove('active');
                }
            }
        });
        
        // Update tab content visibility
        document.querySelectorAll('.detail-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        const defaultContent = document.getElementById(`${defaultTab}-tab`);
        if (defaultContent) {
            defaultContent.classList.add('active');
        }
        
        // Hide tabs that don't have data (will be shown when data loads)
        ['elevation', 'map', 'gallery'].forEach(tabId => {
            const tab = tabMap[tabId];
            if (tab) {
                tab.style.display = 'none'; // Will be shown when data is available
            }
        });
    }
    
    function init(userId, userProfile) {
        currentUserId = userId;
        currentUserProfile = userProfile || currentUserProfile || null;
        
        // Load saved preferences
        const savedViewMode = localStorage.getItem('trail-view-mode') || 'grid';
        switchViewMode(savedViewMode);
        
        setupTabs();
        setupViewModeToggle();
        setupSearch();
        setupFilters();
        setupSort();
        setupKeyboardNavigation();
        setupExpandableSections();
        loadTrails();
    }
    
    // Setup expandable sections
    function setupExpandableSections() {
        // Use event delegation for dynamically created expandable sections
        document.addEventListener('click', function(e) {
            const toggle = e.target.closest('.expand-toggle');
            if (!toggle) return;
            
            e.preventDefault();
            const sectionId = toggle.getAttribute('data-section');
            const content = toggle.nextElementSibling;
            
            if (content && content.classList.contains('expandable-content')) {
                const isExpanded = content.style.display !== 'none';
                content.style.display = isExpanded ? 'none' : 'block';
                const icon = toggle.querySelector('.expand-icon');
                if (icon) {
                    icon.textContent = isExpanded ? '▼' : '▲';
                }
                toggle.classList.toggle('expanded', !isExpanded);
            }
        });
    }
    
    function setupTabs() {
        const tabs = document.querySelectorAll('.trail-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const tabType = this.getAttribute('data-tab');
                
                // Update active tab
                tabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                
                // Show corresponding list
                document.querySelectorAll('.trail-list').forEach(list => {
                    list.classList.remove('active');
                });
                document.getElementById(`${tabType}-trails`).classList.add('active');
            });
        });
    }
    
    function loadTrails() {
        if (!currentUserId) {
            console.warn('No currentUserId set');
            return;
        }
        
        fetch(`/api/profile/${currentUserId}/trails`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Handle different response formats
                if (Array.isArray(data)) {
                    // If API returns array, convert to object format
                    trails = {
                        saved: data.filter(t => t.status === 'saved') || [],
                        started: data.filter(t => t.status === 'started') || [],
                        completed: data.filter(t => t.status === 'completed') || []
                    };
                } else {
                    trails = data || { saved: [], started: [], completed: [] };
                }
                
                // Ensure all properties exist
                if (!trails.saved) trails.saved = [];
                if (!trails.started) trails.started = [];
                if (!trails.completed) trails.completed = [];
                
                // Update counts first, then render
                updateCounts();
                renderTrails();
            })
            .catch(error => {
                console.error('Error loading trails:', error);
                // Show error in UI
                const containers = ['saved-trails', 'started-trails', 'completed-trails'];
                containers.forEach(id => {
                    const container = document.getElementById(id);
                    if (container) {
                        container.innerHTML = `<p class="empty-state error">Error loading trails: ${error.message}</p>`;
                    }
                });
            });
    }
    
    function renderTrails() {
        renderSavedTrails();
        renderStartedTrails();
        renderCompletedTrails();
    }
    
    function renderSavedTrails() {
        const container = document.getElementById('saved-trails');
        if (!container) return;
        
        let trailList = trails.saved || [];
        
        // Apply filters and search
        trailList = applyFilters(trailList, 'saved');
        trailList = applySearch(trailList);
        trailList = applySort(trailList, 'saved');
        
        if (trailList.length === 0) {
            container.innerHTML = getEmptyState('saved');
            return;
        }
        
        container.innerHTML = renderTrailsByViewMode(trailList, 'saved');
        setTimeout(() => {
            attachTrailActions(container, 'saved');
        }, 0);
    }
    
    function renderStartedTrails() {
        const container = document.getElementById('started-trails');
        if (!container) return;
        
        let trailList = trails.started || [];
        
        // Apply filters and search
        trailList = applyFilters(trailList, 'started');
        trailList = applySearch(trailList);
        trailList = applySort(trailList, 'started');
        
        if (trailList.length === 0) {
            container.innerHTML = getEmptyState('started');
            return;
        }
        
        container.innerHTML = renderTrailsByViewMode(trailList, 'started');
        // Small delay to ensure DOM is ready
        setTimeout(() => {
            attachTrailActions(container, 'started');
        }, 0);
    }
    
    function renderCompletedTrails() {
        const container = document.getElementById('completed-trails');
        if (!container) return;
        
        let trailList = trails.completed || [];
        
        // Apply filters and search
        trailList = applyFilters(trailList, 'completed');
        trailList = applySearch(trailList);
        trailList = applySort(trailList, 'completed');
        
        if (trailList.length === 0) {
            container.innerHTML = getEmptyState('completed');
            return;
        }
        
        container.innerHTML = renderTrailsByViewMode(trailList, 'completed');
        attachTrailActions(container, 'completed');
    }
    
    function renderTrailsByViewMode(trailList, status) {
        switch (currentViewMode) {
            case 'grid':
                return renderGridView(trailList, status);
            case 'list':
                return renderListView(trailList, status);
            case 'timeline':
                return renderTimelineView(trailList, status);
            default:
                return renderGridView(trailList, status);
        }
    }
    
    function renderGridView(trailList, status) {
        return `<div class="trail-grid-view">${trailList.map(trail => createEnhancedTrailCard(trail, status, 'grid')).join('')}</div>`;
    }
    
    function renderListView(trailList, status) {
        return `<div class="trail-list-view">${trailList.map(trail => createEnhancedTrailCard(trail, status, 'list')).join('')}</div>`;
    }
    
    function renderTimelineView(trailList, status) {
        // Group by date
        const grouped = groupTrailsByDate(trailList, status);
        let html = '<div class="trail-timeline-view">';
        
        Object.keys(grouped).sort((a, b) => new Date(b) - new Date(a)).forEach(date => {
            html += `<div class="timeline-group">
                <div class="timeline-date-marker">${formatDateHeader(date)}</div>
                <div class="timeline-trails">${grouped[date].map(trail => createEnhancedTrailCard(trail, status, 'timeline')).join('')}</div>
            </div>`;
        });
        
        html += '</div>';
        return html;
    }
    
    function groupTrailsByDate(trailList, status) {
        const grouped = {};
        trailList.forEach(trail => {
            let dateKey;
            if (status === 'completed' && trail.completion_date) {
                dateKey = trail.completion_date.split('T')[0];
            } else if (status === 'started' && trail.start_date) {
                dateKey = trail.start_date.split('T')[0];
            } else if (status === 'saved' && trail.saved_date) {
                dateKey = trail.saved_date.split('T')[0];
            } else {
                dateKey = 'unknown';
            }
            
            if (!grouped[dateKey]) {
                grouped[dateKey] = [];
            }
            grouped[dateKey].push(trail);
        });
        return grouped;
    }
    
    function formatDateHeader(dateStr) {
        if (dateStr === 'unknown') return 'Unknown Date';
        const date = new Date(dateStr);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        
        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Yesterday';
        } else {
            return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
        }
    }
    
    function createEnhancedTrailCard(trail, status, viewMode) {
        const statusBadge = createStatusBadge(status, trail);
        const difficultyBadge = createDifficultyBadge(trail.difficulty);
        const dateBadge = createDateBadge(trail, status);
        const progressRing = status === 'started' && trail.progress_percentage 
            ? createProgressRing(trail.progress_percentage) 
            : '';
        const performanceIndicators = status === 'completed' 
            ? createPerformanceIndicators(trail) 
            : '';
        const ratingStars = status === 'completed' && trail.rating 
            ? createRatingStars(trail.rating) 
            : '';
        
        const cardClass = `trail-card trail-card-${viewMode} trail-card-${status}`;
        
        if (viewMode === 'list') {
            return `
                <div class="${cardClass}" data-trail-id="${trail.trail_id}">
                    <div class="trail-card-list-content">
                        <div class="trail-card-list-main">
                            ${statusBadge}
                            ${difficultyBadge}
                            <h3 class="trail-name">${escapeHtml(trail.name || trail.trail_id)}</h3>
                            <div class="trail-info-compact">
                                <span>📏 ${trail.distance || 'N/A'} km</span>
                                <span>⛰️ ${trail.elevation_gain || 'N/A'}m</span>
                                <span>⏱️ ${formatDuration(trail.estimated_duration || trail.actual_duration)}</span>
                            </div>
                            ${dateBadge}
                            ${ratingStars}
                            ${performanceIndicators}
                        </div>
                        <div class="trail-card-list-actions">
                            ${progressRing}
                            <div class="trail-actions">
                                <button class="btn-view-details" data-trail-id="${trail.trail_id}">View</button>
                                ${status === 'saved' ? '<button class="btn-unsave" data-trail-id="' + trail.trail_id + '">Remove</button>' : ''}
                                ${status === 'started' ? '<button class="btn-complete-trail" data-trail-id="' + trail.trail_id + '">Complete</button>' : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Grid and Timeline views
        return `
            <div class="${cardClass}" data-trail-id="${trail.trail_id}">
                <div class="trail-card-header">
                    <div class="trail-badges-top">
                        ${statusBadge}
                        ${difficultyBadge}
                    </div>
                    <div class="trail-card-quick-actions">
                        ${status === 'saved' ? '<button class="btn-quick-action btn-start-quick" data-trail-id="' + trail.trail_id + '" title="Start Trail">▶️</button>' : ''}
                        ${status === 'saved' ? '<button class="btn-quick-action btn-unsave-card" data-trail-id="' + trail.trail_id + '" title="Remove">×</button>' : ''}
                        ${status === 'started' ? '<button class="btn-quick-action btn-continue-quick" data-trail-id="' + trail.trail_id + '" title="Continue">▶️</button>' : ''}
                        ${status === 'started' ? '<button class="btn-quick-action btn-complete-quick" data-trail-id="' + trail.trail_id + '" title="Complete Trail">✓</button>' : ''}
                    </div>
                </div>
                <div class="trail-card-body">
                    <h3 class="trail-name">${escapeHtml(trail.name || trail.trail_id)}</h3>
                    <div class="trail-info">
                        <span>📏 ${trail.distance || 'N/A'} km</span>
                        <span>⛰️ ${trail.elevation_gain || 'N/A'}m</span>
                        <span>⏱️ ${formatDuration(trail.estimated_duration || trail.actual_duration)}</span>
                    </div>
                    ${progressRing}
                    ${ratingStars}
                    ${performanceIndicators}
                    ${dateBadge}
                    <div class="trail-actions">
                        <button class="btn-view-details" data-trail-id="${trail.trail_id}">View Details</button>
                        ${status === 'started' ? '<button class="btn-complete-trail" data-trail-id="' + trail.trail_id + '">Complete Trail</button>' : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    function createStatusBadge(status, trail) {
        const config = {
            'saved': { color: '#3b82f6', icon: '🔖', label: 'Saved' },
            'started': { color: '#f59e0b', icon: '▶️', label: 'Started' },
            'completed': { color: '#10b981', icon: '✅', label: 'Completed' }
        };
        const cfg = config[status] || config.saved;
        return `<span class="status-badge status-badge-${status}" style="background-color: ${cfg.color}20; color: ${cfg.color}; border-color: ${cfg.color}">
            ${cfg.icon} ${cfg.label}
        </span>`;
    }
    
    function createDifficultyBadge(difficulty) {
        if (!difficulty) return '';
        const level = difficulty <= 3 ? 'easy' : difficulty <= 7 ? 'medium' : 'hard';
        const colors = {
            easy: { bg: '#10b98120', color: '#10b981', label: 'Easy' },
            medium: { bg: '#f59e0b20', color: '#f59e0b', label: 'Medium' },
            hard: { bg: '#ef444420', color: '#ef4444', label: 'Hard' }
        };
        const cfg = colors[level];
        return `<span class="difficulty-badge difficulty-${level}" style="background-color: ${cfg.bg}; color: ${cfg.color}; border-color: ${cfg.color}">
            ${cfg.label} (${difficulty}/10)
        </span>`;
    }
    
    function createDateBadge(trail, status) {
        let date, label;
        if (status === 'completed' && trail.completion_date) {
            date = new Date(trail.completion_date);
            label = 'Completed';
        } else if (status === 'started' && trail.start_date) {
            date = new Date(trail.start_date);
            label = 'Started';
            const daysAgo = Math.floor((new Date() - date) / (1000 * 60 * 60 * 24));
            return `<span class="date-badge">${label} ${daysAgo === 0 ? 'today' : daysAgo === 1 ? 'yesterday' : daysAgo + ' days ago'}</span>`;
        } else if (status === 'saved' && trail.saved_date) {
            date = new Date(trail.saved_date);
            label = 'Saved';
        } else {
            return '';
        }
        return `<span class="date-badge">${label} ${date.toLocaleDateString()}</span>`;
    }
    
    function createProgressRing(percentage) {
        const radius = 30;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (percentage / 100) * circumference;
        return `
            <div class="progress-ring-container">
                <svg class="progress-ring" width="70" height="70">
                    <circle class="progress-ring-background" cx="35" cy="35" r="${radius}" fill="none" stroke="#e5e7eb" stroke-width="6"/>
                    <circle class="progress-ring-fill" cx="35" cy="35" r="${radius}" fill="none" stroke="#f59e0b" stroke-width="6" 
                        stroke-dasharray="${circumference}" stroke-dashoffset="${offset}" transform="rotate(-90 35 35)"/>
                </svg>
                <div class="progress-ring-text">${Math.round(percentage)}%</div>
            </div>
        `;
    }
    
    function createPerformanceIndicators(trail) {
        if (!trail.avg_heart_rate && !trail.avg_speed && !trail.total_calories) return '';
        
        let html = '<div class="performance-indicators">';
        if (trail.avg_heart_rate) {
            html += `<span class="perf-indicator" title="Average Heart Rate">❤️ ${trail.avg_heart_rate} bpm</span>`;
        }
        if (trail.avg_speed) {
            html += `<span class="perf-indicator" title="Average Speed">⚡ ${trail.avg_speed.toFixed(1)} km/h</span>`;
        }
        if (trail.total_calories) {
            html += `<span class="perf-indicator" title="Calories Burned">🔥 ${trail.total_calories} kcal</span>`;
        }
        html += '</div>';
        return html;
    }
    
    function createRatingStars(rating) {
        if (!rating) return '';
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        let html = '<div class="rating-stars">';
        for (let i = 0; i < 5; i++) {
            if (i < fullStars) {
                html += '<span class="star star-full">⭐</span>';
            } else if (i === fullStars && hasHalfStar) {
                html += '<span class="star star-half">⭐</span>';
            } else {
                html += '<span class="star star-empty">☆</span>';
            }
        }
        html += ` <span class="rating-value">${rating.toFixed(1)}</span></div>`;
        return html;
    }
    
    function formatDuration(minutes) {
        if (!minutes) return 'N/A';
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        if (hours > 0) {
            return `${hours}h ${mins}m`;
        }
        return `${mins}m`;
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function getEmptyState(status) {
        const messages = {
            saved: {
                title: 'No saved trails yet',
                description: 'Browse trails and save your favorites to plan your next adventure!',
                cta: 'Browse Trails',
                ctaLink: '/recommendations'
            },
            started: {
                title: 'No started trails yet',
                description: 'Start a trail to track your progress and see your journey unfold!',
                cta: 'Start a Trail',
                ctaLink: '#'
            },
            completed: {
                title: 'No completed trails yet',
                description: 'Complete trails to see your achievements and track your progress!',
                cta: 'View Recommendations',
                ctaLink: '/recommendations'
            }
        };
        
        const msg = messages[status];
        return `<div class="empty-state">
            <div class="empty-state-icon">${status === 'saved' ? '🔖' : status === 'started' ? '▶️' : '✅'}</div>
            <h3 class="empty-state-title">${msg.title}</h3>
            <p class="empty-state-description">${msg.description}</p>
            ${msg.ctaLink !== '#' ? `<a href="${msg.ctaLink}" class="btn-primary empty-state-cta">${msg.cta}</a>` : ''}
        </div>`;
    }
    
    function attachTrailActions(container, status) {
        // View details buttons
        container.querySelectorAll('.btn-view-details').forEach(btn => {
            btn.addEventListener('click', function() {
                const trailId = this.getAttribute('data-trail-id');
                showTrailDetails(trailId);
            });
        });
        
        // Unsave buttons (both regular and card versions)
        container.querySelectorAll('.btn-unsave, .btn-unsave-card').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const trailId = this.getAttribute('data-trail-id');
                unsaveTrail(trailId);
            });
        });
        
        // Quick start buttons
        container.querySelectorAll('.btn-start-quick').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const trailId = this.getAttribute('data-trail-id');
                startTrail(trailId);
            });
        });
        
        // Quick continue buttons
        container.querySelectorAll('.btn-continue-quick').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const trailId = this.getAttribute('data-trail-id');
                showTrailDetails(trailId);
            });
        });
        
        // Complete trail buttons (both regular and quick action)
        const completeButtons = container.querySelectorAll('.btn-complete-trail, .btn-complete-quick');
        
        completeButtons.forEach((btn) => {
            const trailId = btn.getAttribute('data-trail-id');
            
            // Remove any existing listeners by cloning
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            newBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();
                const trailId = this.getAttribute('data-trail-id');
                
                if (!trailId) {
                    console.error('No trail ID found on button');
                    alert('Error: No trail ID found');
                    return;
                }
                
                if (!currentUserId) {
                    console.error('No current user ID');
                    alert('Error: User not logged in');
                    return;
                }
                
                // Call completeTrail function
                completeTrail(trailId);
            });
        });
    }
    
    function unsaveTrail(trailId) {
        if (!confirm('Remove this trail from saved?')) return;
        
        fetch(`/api/profile/${currentUserId}/trails/${trailId}/unsave`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadTrails();
            }
        })
        .catch(error => {
            console.error('Error unsaving trail:', error);
        });
    }
    
    // Expose updateCounts for external calls if needed
    function refreshCounts() {
        updateCounts();
    }
    
    // Cache for DOM elements to avoid repeated queries
    let cachedElements = null;
    let tabsInitialized = false;
    
    function ensureModalStructure() {
        const content = document.getElementById('trail-detail-content');
        if (!content) {
            return false;
        }
        
        // Check if template is already inserted
        const modalContentWrapper = content.querySelector('.trail-detail-modal-content');
        if (!modalContentWrapper) {
            const template = document.getElementById('trail-detail-modal-template');
            if (template) {
                content.innerHTML = template.innerHTML;
                // Clear cache since DOM structure changed
                cachedElements = null;
                tabsInitialized = false;
                // Initialize tabs immediately after template insertion
                setupDetailTabs();
                return true;
            } else {
                console.error('trail-detail-modal-template not found');
                return false;
            }
        } else if (!tabsInitialized) {
            // Template exists but tabs not initialized yet
            setupDetailTabs();
        }
        return true;
    }
    
    function getCachedElements() {
        if (cachedElements) {
            return cachedElements;
        }
        
        const content = document.getElementById('trail-detail-content');
        if (!content) {
            return null;
        }
        
        const modalContentWrapper = content.querySelector('.trail-detail-modal-content') || content;
        
        const overviewTab = modalContentWrapper.querySelector('#overview-tab');
        const descSummary = overviewTab ? overviewTab.querySelector('#trail-description-summary') : null;
        const keyStatsGrid = overviewTab ? overviewTab.querySelector('#trail-key-stats-grid') : null;
        
        cachedElements = {
            wrapper: modalContentWrapper,
            header: modalContentWrapper.querySelector('.trail-detail-header'),
            name: modalContentWrapper.querySelector('#trail-detail-name'),
            distance: modalContentWrapper.querySelector('#trail-detail-distance'),
            difficulty: modalContentWrapper.querySelector('#trail-detail-difficulty'),
            elevation: modalContentWrapper.querySelector('#trail-detail-elevation'),
            overviewTab: overviewTab,
            performanceTab: modalContentWrapper.querySelector('#performance-tab'),
            weatherTab: modalContentWrapper.querySelector('#weather-tab'),
            recommendationsTab: modalContentWrapper.querySelector('#recommendations-tab'),
            elevationTab: modalContentWrapper.querySelector('#elevation-tab'),
            mapTab: modalContentWrapper.querySelector('#map-tab'),
            galleryTab: modalContentWrapper.querySelector('#gallery-tab'),
            description: modalContentWrapper.querySelector('#trail-description'),
            landscapes: modalContentWrapper.querySelector('#trail-landscapes'),
            performanceMetrics: modalContentWrapper.querySelector('#performance-metrics'),
            weatherForecast: modalContentWrapper.querySelector('#weather-forecast'),
            aiRecommendations: modalContentWrapper.querySelector('#ai-recommendations')
        };
        return cachedElements;
    }
    
    function showLoadingState(tabId, message = 'Loading...') {
        const elements = getCachedElements();
        if (!elements) return;
        
        // Map tab IDs to element keys
        const tabMap = {
            'performance': 'performanceTab',
            'weather': 'weatherTab',
            'recommendations': 'recommendationsTab',
            'overview': 'overviewTab'
        };
        
        const elementKey = tabMap[tabId];
        if (elementKey && elements[elementKey]) {
            // Preserve tab structure, only update content area
            if (tabId === 'performance' && elements.performanceMetrics) {
                elements.performanceMetrics.innerHTML = `<div class="loading">${message}</div>`;
            } else if (tabId === 'weather' && elements.weatherForecast) {
                elements.weatherForecast.innerHTML = `<div class="loading">${message}</div>`;
            } else if (tabId === 'recommendations' && elements.aiRecommendations) {
                elements.aiRecommendations.innerHTML = `<div class="loading">${message}</div>`;
            } else if (elements[elementKey]) {
                elements[elementKey].innerHTML = `<div class="loading">${message}</div>`;
            }
        }
    }
    
    function showTrailDetails(trailId) {
        const modal = document.getElementById('trail-detail-modal');
        const content = document.getElementById('trail-detail-content');
        
        if (!modal || !content) {
            console.error('Trail detail modal not found');
            return;
        }
        
        // Clear cache and reset tab initialization
        cachedElements = null;
        tabsInitialized = false;
        
        // Ensure template structure exists
        if (!ensureModalStructure()) {
            return;
        }
        
        // Detect user profile (from global variable or fetch)
        let userProfile = currentUserProfile;
        if (!userProfile && typeof currentUserProfile !== 'undefined') {
            userProfile = currentUserProfile;
        }
        if (!userProfile && typeof window.currentUserProfile !== 'undefined') {
            userProfile = window.currentUserProfile;
        }
        
        // Note: reorderTabsForProfile will be called AFTER template is restored in renderHeaderAndOverview
        
        // Show loading states for tabs that will load later
        showLoadingState('performance', 'Loading performance data...');
        showLoadingState('weather', 'Loading weather forecast...');
        showLoadingState('recommendations', 'Loading recommendations...');
        
        modal.style.display = 'block';
        
        // Progressive loading: Load trail first (fast), then other data
        fetch(`/api/trail/${trailId}`)
            .then(r => {
                if (!r.ok) throw new Error(`Trail API returned ${r.status}`);
                return r.json();
            })
            .then(trail => {
                // Store trail data for lazy loading
                if (typeof window._setCurrentTrailData === 'function') {
                    window._setCurrentTrailData(trail);
                }
                
                // Render header and overview immediately
                renderHeaderAndOverview(trail, userProfile);
                
                // Check if profile-specific tab has data, otherwise fall back to overview
                let profileTabHasData = false;
                if (userProfile === 'elevation_lover' && trail.elevation_profile && trail.elevation_profile.length > 0) {
                    profileTabHasData = true;
                    renderElevationTab(trail);
                    document.querySelector('.detail-tab[data-tab="elevation"]')?.style.setProperty('display', '');
                } else if (userProfile === 'explorer' && trail.coordinates) {
                    profileTabHasData = true;
                    document.querySelector('.detail-tab[data-tab="map"]')?.style.setProperty('display', '');
                } else if (userProfile === 'photographer' && (trail.landscapes || trail.elevation_profile)) {
                    profileTabHasData = true;
                    renderGalleryTab(trail);
                    document.querySelector('.detail-tab[data-tab="gallery"]')?.style.setProperty('display', '');
                }
                
                // If profile-specific tab has no data, switch to overview
                if (!profileTabHasData && userProfile) {
                    // Remove active from all tab contents
                    document.querySelectorAll('.detail-tab-content').forEach(content => {
                        content.classList.remove('active');
                    });
                    const overviewTab = document.getElementById('overview-tab');
                    if (overviewTab) {
                        overviewTab.classList.add('active');
                    }
                    // Also ensure the tab button is active
                    document.querySelectorAll('.detail-tab').forEach(tab => {
                        tab.classList.remove('active');
                    });
                    const overviewTabButton = document.querySelector('.detail-tab[data-tab="overview"]');
                    if (overviewTabButton) {
                        overviewTabButton.classList.add('active');
                    }
                }
                
                // Render other profile-specific tabs if data is available (but don't switch to them)
                if (trail.coordinates && userProfile !== 'explorer') {
                    document.querySelector('.detail-tab[data-tab="map"]')?.style.setProperty('display', '');
                }
                if ((trail.landscapes || trail.elevation_profile) && userProfile !== 'photographer') {
                    renderGalleryTab(trail);
                    document.querySelector('.detail-tab[data-tab="gallery"]')?.style.setProperty('display', '');
                }
                
                // Load weather and performance in parallel (fast)
                return Promise.all([
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
                    fetch(`/api/profile/${currentUserId}/trail/${trailId}/performance`)
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
                        })
                ]).then(([weather, performance]) => {
                    // Render Performance and Weather tabs as soon as data arrives
                    renderPerformanceTab(performance);
                    renderWeatherTab(weather);
                    
                    // Load recommendations with weather data (can be slow - AI service)
                    // Pass weather forecast to avoid redundant API call
                    let recommendationsUrl = `/api/profile/${currentUserId}/trail/${trailId}/recommendations`;
                    if (weather && weather.forecast && weather.forecast.length > 0) {
                        try {
                            const weatherParam = encodeURIComponent(JSON.stringify(weather.forecast));
                            recommendationsUrl += `?weather_forecast=${weatherParam}`;
                        } catch (e) {
                            console.warn('Error encoding weather parameter:', e);
                            // Continue without weather parameter - API will fetch it
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
                            // Render Recommendations tab when ready
                            renderRecommendationsTab(recommendations);
                        });
                });
            })
            .catch(error => {
                console.error('Error loading trail details:', error);
                const elements = getCachedElements();
                if (elements && elements.overviewTab) {
                    elements.overviewTab.innerHTML = `<div class="error">Error loading trail details: ${error.message}. Please try again.</div>`;
                } else if (content) {
                    content.innerHTML = `<div class="error">Error loading trail details: ${error.message}. Please try again.</div>`;
                }
            });
    }
    
    function renderHeaderAndOverview(trail, userProfile) {
        const ensureResult = ensureModalStructure();
        if (!ensureResult) return;
        
        // Reorder tabs and set active tab AFTER template is restored
        if (userProfile) {
            reorderTabsForProfile(userProfile);
        } else {
            // Default to overview if no profile
            // Remove active from all tab contents
            document.querySelectorAll('.detail-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            const overviewTab = document.getElementById('overview-tab');
            if (overviewTab) {
                overviewTab.classList.add('active');
            }
            // Also ensure the tab button is active
            document.querySelectorAll('.detail-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            const overviewTabButton = document.querySelector('.detail-tab[data-tab="overview"]');
            if (overviewTabButton) {
                overviewTabButton.classList.add('active');
            }
        }
        // Clear cache to force fresh lookup after setting active class
        cachedElements = null;
        
        const elements = getCachedElements();
        if (!elements) return;
        
        // Render header
        if (elements.name) {
            elements.name.textContent = trail.name || trail.trail_id || 'Unknown Trail';
        }
        if (elements.distance) {
            elements.distance.textContent = trail.distance !== undefined && trail.distance !== null ? trail.distance : 'N/A';
        }
        if (elements.difficulty) {
            elements.difficulty.textContent = trail.difficulty !== undefined && trail.difficulty !== null ? trail.difficulty : 'N/A';
        }
        if (elements.elevation) {
            elements.elevation.textContent = trail.elevation_gain !== undefined && trail.elevation_gain !== null ? trail.elevation_gain : 'N/A';
        }
        
        // Render quick stats
        const quickStatsContainer = document.getElementById('trail-detail-quick-stats');
        if (quickStatsContainer) {
            let quickStatsHTML = '<div class="quick-stats-grid">';
            
            if (trail.region) {
                quickStatsHTML += `<div class="quick-stat-card"><span class="stat-label">Region</span><span class="stat-value">${escapeHtml(trail.region)}</span></div>`;
            }
            if (trail.trail_type) {
                const typeIcon = trail.trail_type.toLowerCase().includes('loop') ? '🔁' : '➡️';
                quickStatsHTML += `<div class="quick-stat-card"><span class="stat-label">Type</span><span class="stat-value">${typeIcon} ${escapeHtml(trail.trail_type)}</span></div>`;
            }
            if (trail.popularity !== undefined && trail.popularity !== null) {
                const popularityStars = '⭐'.repeat(Math.min(5, Math.floor(trail.popularity / 20)));
                quickStatsHTML += `<div class="quick-stat-card"><span class="stat-label">Popularity</span><span class="stat-value">${popularityStars}</span></div>`;
            }
            if (trail.duration) {
                const hours = Math.floor(trail.duration / 60);
                const mins = trail.duration % 60;
                quickStatsHTML += `<div class="quick-stat-card"><span class="stat-label">Duration</span><span class="stat-value">${hours}h ${mins}m</span></div>`;
            }
            
            quickStatsHTML += '</div>';
            quickStatsContainer.innerHTML = quickStatsHTML;
        }
        
        // Render status badges and safety info
        const statusActionsContainer = document.getElementById('trail-detail-status-actions');
        if (statusActionsContainer) {
            let statusHTML = '<div class="trail-status-badges">';
            
            // Safety badge
            if (trail.safety_risks) {
                const riskLevel = trail.safety_risks.toLowerCase();
                const riskColor = riskLevel.includes('high') ? '#ef4444' : riskLevel.includes('medium') ? '#f59e0b' : '#10b981';
                statusHTML += `<span class="safety-badge" style="background-color: ${riskColor}20; color: ${riskColor}; border-color: ${riskColor}">⚠️ ${escapeHtml(trail.safety_risks)}</span>`;
            }
            
            // Accessibility badge
            if (trail.accessibility) {
                statusHTML += `<span class="accessibility-badge">♿ ${escapeHtml(trail.accessibility)}</span>`;
            }
            
            // Closed seasons warning
            if (trail.closed_seasons) {
                const currentMonth = new Date().getMonth() + 1;
                const closedSeasons = trail.closed_seasons.split(',').map(s => s.trim().toLowerCase());
                const isClosed = closedSeasons.some(season => {
                    if (season.includes('winter')) return currentMonth >= 12 || currentMonth <= 2;
                    if (season.includes('spring')) return currentMonth >= 3 && currentMonth <= 5;
                    if (season.includes('summer')) return currentMonth >= 6 && currentMonth <= 8;
                    if (season.includes('fall') || season.includes('autumn')) return currentMonth >= 9 && currentMonth <= 11;
                    return false;
                });
                if (isClosed) {
                    statusHTML += `<span class="closed-season-badge">🚫 Closed in ${escapeHtml(trail.closed_seasons)}</span>`;
                }
            }
            
            statusHTML += '</div>';
            
            // Add action buttons
            statusHTML += '<div class="trail-actions-header">';
            statusHTML += `<button class="btn-save-trail" data-trail-id="${trail.trail_id}">🔖 Save Trail</button>`;
            statusHTML += `<button class="btn-start-trail" data-trail-id="${trail.trail_id}">▶️ Start Trail</button>`;
            statusHTML += '</div>';
            
            statusActionsContainer.innerHTML = statusHTML;
            
            // Attach event listeners
            statusActionsContainer.querySelector('.btn-save-trail')?.addEventListener('click', () => saveTrail(trail.trail_id));
            statusActionsContainer.querySelector('.btn-start-trail')?.addEventListener('click', () => startTrail(trail.trail_id));
        }
        
        // Render overview tab with hybrid information density
        const overviewTab = document.getElementById('overview-tab');
        if (!overviewTab) {
            console.warn('Overview tab not found');
            return;
        }
        
        // Template should have the structure, just populate it
        const descSummary = overviewTab.querySelector('#trail-description-summary');
        const keyStatsGrid = overviewTab.querySelector('#trail-key-stats-grid');
        const landscapesSummary = overviewTab.querySelector('#trail-landscapes-summary');
        if (descSummary) {
            const firstParagraph = trail.description ? trail.description.split('\n')[0] : 'No description available';
            descSummary.innerHTML = `<p class="trail-description-summary">${escapeHtml(firstParagraph)}</p>`;
        }
        
        if (keyStatsGrid) {
            keyStatsGrid.innerHTML = `
                <div class="key-stats-grid">
                    <div class="key-stat"><span class="key-stat-label">Distance</span><span class="key-stat-value">${trail.distance || 'N/A'} km</span></div>
                    <div class="key-stat"><span class="key-stat-label">Elevation</span><span class="key-stat-value">${trail.elevation_gain || 'N/A'}m</span></div>
                    <div class="key-stat"><span class="key-stat-label">Difficulty</span><span class="key-stat-value">${trail.difficulty || 'N/A'}/10</span></div>
                    <div class="key-stat"><span class="key-stat-label">Type</span><span class="key-stat-value">${trail.trail_type || 'N/A'}</span></div>
                    ${trail.duration ? `<div class="key-stat"><span class="key-stat-label">Duration</span><span class="key-stat-value">${Math.floor(trail.duration / 60)}h ${trail.duration % 60}m</span></div>` : ''}
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
        
        // Populate expandable sections (template should have them)
        const fullDescContent = overviewTab.querySelector('#trail-description-full');
        if (fullDescContent && trail.description) {
            fullDescContent.innerHTML = `<p>${escapeHtml(trail.description).replace(/\n/g, '</p><p>')}</p>`;
        }
        
        const detailsExpanded = overviewTab.querySelector('#trail-details-expanded');
        if (detailsExpanded) {
            let detailsHTML = '<div class="trail-details-expanded-grid">';
            if (trail.region) detailsHTML += `<div><strong>Region:</strong> ${escapeHtml(trail.region)}</div>`;
            if (trail.popularity !== undefined) detailsHTML += `<div><strong>Popularity:</strong> ${trail.popularity}/100</div>`;
            if (trail.safety_risks) detailsHTML += `<div><strong>Safety:</strong> ${escapeHtml(trail.safety_risks)}</div>`;
            if (trail.accessibility) detailsHTML += `<div><strong>Accessibility:</strong> ${escapeHtml(trail.accessibility)}</div>`;
            if (trail.closed_seasons) detailsHTML += `<div><strong>Closed Seasons:</strong> ${escapeHtml(trail.closed_seasons)}</div>`;
            detailsHTML += '</div>';
            detailsExpanded.innerHTML = detailsHTML;
        }
    }
    
    // Profile-specific visualization functions
    
    function renderElevationTab(trail) {
        const elevationTab = document.getElementById('elevation-tab');
        if (!elevationTab || !trail.elevation_profile || trail.elevation_profile.length === 0) {
            return;
        }
        
        // Template should have the structure, just populate it
        const elevationSummary = elevationTab.querySelector('#elevation-summary');
        if (elevationSummary) {
                const maxElevation = Math.max(...trail.elevation_profile.map(p => p.elevation || 0));
                const minElevation = Math.min(...trail.elevation_profile.map(p => p.elevation || 0));
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
        }
        
        // Ensure chart container exists
        let chartContainer = elevationTab.querySelector('.chart-container');
        if (!chartContainer) {
            chartContainer = document.createElement('div');
            chartContainer.className = 'chart-container';
            elevationTab.appendChild(chartContainer);
        }
        
        let canvas = chartContainer.querySelector('#elevation-chart');
        if (!canvas) {
            canvas = document.createElement('canvas');
            canvas.id = 'elevation-chart';
            chartContainer.appendChild(canvas);
        }
        
        // Render elevation chart
        setTimeout(() => {
            if (!canvas || typeof Chart === 'undefined') {
                console.warn('Chart.js not available or canvas not found for elevation chart');
                return;
            }
            
            // Destroy existing chart if it exists
            if (canvas.chart) {
                canvas.chart.destroy();
            }
            
            const ctx = canvas.getContext('2d');
            const elevationData = trail.elevation_profile.map(p => p.elevation || 0);
            const distanceData = trail.elevation_profile.map((p, i) => {
                if (i === 0) return 0;
                // Calculate cumulative distance (simplified - would need actual distance calculation)
                return i * (trail.distance / trail.elevation_profile.length);
            });
            
            canvas.chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: distanceData.map((d, i) => i === 0 || i === distanceData.length - 1 || i % Math.floor(distanceData.length / 5) === 0 ? d.toFixed(1) + ' km' : ''),
                    datasets: [{
                        label: 'Elevation (m)',
                        data: elevationData,
                        borderColor: 'rgb(99, 102, 241)',
                        backgroundColor: 'rgba(99, 102, 241, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 2.5,
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
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Elevation (m)'
                            }
                        }
                    }
                }
            });
        }, 100);
    }
    
    function renderMapTab(trail) {
        const mapTab = document.getElementById('map-tab');
        if (!mapTab || !trail.coordinates) {
            return;
        }
        
        const mapContainer = mapTab.querySelector('#trail-map-container');
        if (!mapContainer) {
            return;
        }
        
        // Check if already initialized
        if (mapContainer._mapInitialized) {
            return;
        }
        
        // Clear existing map
        mapContainer.innerHTML = '';
        
        // Initialize map only when tab is visible (lazy load)
        const mapId = 'trail-detail-map';
        mapContainer.id = mapId;
        // Use MapManager if available
        if (typeof MapManager !== 'undefined') {
            const mapManager = new MapManager();
            setTimeout(() => {
                try {
                    // Parse coordinates (assuming GeoJSON LineString format)
                    let coordinates = [];
                    if (typeof trail.coordinates === 'string') {
                        try {
                            const geoJson = JSON.parse(trail.coordinates);
                            if (geoJson.type === 'LineString' && geoJson.coordinates) {
                                coordinates = geoJson.coordinates.map(coord => [coord[1], coord[0]]); // [lat, lon]
                            }
                        } catch (e) {
                            console.warn('Could not parse coordinates as GeoJSON:', e);
                        }
                    } else if (Array.isArray(trail.coordinates)) {
                        coordinates = trail.coordinates;
                    }
                    if (coordinates.length === 0) {
                        mapContainer.innerHTML = '<p>No route data available</p>';
                        return;
                    }
                    const map = mapManager.initMap(mapId, {
                        zoom: 10,
                        center: coordinates[Math.floor(coordinates.length / 2)]
                    });
                    // Add trail route
                    if (typeof L !== 'undefined' && map) {
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
                        
                        // Fit bounds to show entire route
                        map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
                        mapContainer._mapInitialized = true;
                    }
                } catch (e) {
                    console.error('Error rendering map:', e);
                    mapContainer.innerHTML = '<p>Error loading map. Please ensure Leaflet.js is loaded.</p>';
                }
            }, 200);
        } else {
            mapContainer.innerHTML = '<p>Map functionality requires MapManager. Please ensure app.js is loaded.</p>';
        }
    }
    
    function renderGalleryTab(trail) {
        const galleryTab = document.getElementById('gallery-tab');
        if (!galleryTab) {
            return;
        }
        
        // Template should have the structure, just populate it
        const gallerySummary = galleryTab.querySelector('#gallery-summary');
        if (gallerySummary) {
            gallerySummary.innerHTML = '<h4>Scenic Points & Photo Spots</h4>';
        }
        
        const galleryContent = galleryTab.querySelector('#trail-gallery-content');
        if (!galleryContent) {
            console.warn('Gallery content container not found');
            return;
        }
        
        let galleryHTML = '';
        
        // Derive scenic points from elevation profile peaks
        if (trail.elevation_profile && trail.elevation_profile.length > 0) {
            const elevations = trail.elevation_profile.map(p => p.elevation || 0);
            const maxElevation = Math.max(...elevations);
            const peaks = [];
            
            // Find peaks (local maxima)
            for (let i = 1; i < elevations.length - 1; i++) {
                if (elevations[i] > elevations[i - 1] && elevations[i] > elevations[i + 1]) {
                    peaks.push({
                        index: i,
                        elevation: elevations[i],
                        distance: (i / elevations.length) * (trail.distance || 0)
                    });
                }
            }
            
            // Sort by elevation and take top 5
            peaks.sort((a, b) => b.elevation - a.elevation);
            const topPeaks = peaks.slice(0, 5);
            
            if (topPeaks.length > 0) {
                galleryHTML += '<div class="scenic-points-section"><h5>Best Viewpoints</h5><div class="scenic-points-grid">';
                topPeaks.forEach((peak, idx) => {
                    galleryHTML += `
                        <div class="scenic-point-card">
                            <div class="scenic-point-icon">🏔️</div>
                            <div class="scenic-point-info">
                                <div class="scenic-point-name">Viewpoint ${idx + 1}</div>
                                <div class="scenic-point-details">Elevation: ${peak.elevation}m | Distance: ${peak.distance.toFixed(1)}km</div>
                            </div>
                        </div>
                    `;
                });
                galleryHTML += '</div></div>';
            }
        }
        
        // Landscape highlights
        if (trail.landscapes) {
            const landscapes = trail.landscapes.split(',').map(l => l.trim()).filter(l => l);
            if (landscapes.length > 0) {
                galleryHTML += '<div class="landscape-highlights-section"><h5>Landscape Highlights</h5><div class="landscape-highlights-grid">';
                landscapes.forEach(landscape => {
                    const icon = landscape.toLowerCase().includes('mountain') ? '⛰️' :
                               landscape.toLowerCase().includes('lake') ? '🏞️' :
                               landscape.toLowerCase().includes('forest') ? '🌲' :
                               landscape.toLowerCase().includes('valley') ? '🏔️' : '📸';
                    galleryHTML += `
                        <div class="landscape-highlight-card">
                            <div class="landscape-icon">${icon}</div>
                            <div class="landscape-name">${escapeHtml(landscape)}</div>
                        </div>
                    `;
                });
                galleryHTML += '</div></div>';
            }
        }
        
        if (!galleryHTML) {
            galleryHTML = '<p>No scenic points or photo spots available for this trail.</p>';
        }
        
        galleryContent.innerHTML = galleryHTML;
    }
    
    function renderPerformanceTab(performance) {
        const performanceTab = document.getElementById('performance-tab');
        if (!performanceTab) {
            showLoadingState('performance', 'No performance data available');
            return;
        }
        
        if (performance && performance.completed && performance.performance) {
            const perf = performance.performance;
            
            // Summary cards (always visible) - template should have this
            const summaryCards = performanceTab.querySelector('#performance-summary-cards');
            if (summaryCards) {
                let summaryHTML = '<div class="performance-summary-grid">';
                
                if (perf.actual_duration !== undefined && perf.actual_duration !== null) {
                    const hours = Math.floor(perf.actual_duration / 60);
                    const minutes = perf.actual_duration % 60;
                    summaryHTML += `<div class="performance-summary-card"><span class="summary-label">Duration</span><span class="summary-value">${hours}h ${minutes}m</span></div>`;
                }
                
                if (perf.rating !== undefined && perf.rating !== null) {
                    summaryHTML += `<div class="performance-summary-card"><span class="summary-label">Rating</span><span class="summary-value">${perf.rating.toFixed(1)}/5 ⭐</span></div>`;
                }
                
                if (perf.avg_heart_rate !== undefined && perf.avg_heart_rate !== null) {
                    summaryHTML += `<div class="performance-summary-card"><span class="summary-label">Avg Heart Rate</span><span class="summary-value">${perf.avg_heart_rate} bpm</span></div>`;
                }
                
                if (perf.total_calories !== undefined && perf.total_calories !== null) {
                    summaryHTML += `<div class="performance-summary-card"><span class="summary-label">Calories</span><span class="summary-value">${perf.total_calories} kcal</span></div>`;
                }
                
                summaryHTML += '</div>';
                summaryCards.innerHTML = summaryHTML;
            }
            
            // Detailed metrics (expandable) - template should have this
            const detailedMetrics = performanceTab.querySelector('#performance-metrics-detailed');
            if (detailedMetrics) {
                let html = '<div class="performance-metrics-grid">';
                
                if (perf.max_heart_rate !== undefined && perf.max_heart_rate !== null) {
                    html += `<div class="metric-item"><strong>Max Heart Rate:</strong> ${perf.max_heart_rate} bpm</div>`;
                }
                
                if (perf.avg_speed !== undefined && perf.avg_speed !== null) {
                    html += `<div class="metric-item"><strong>Avg Speed:</strong> ${perf.avg_speed.toFixed(2)} km/h</div>`;
                }
                
                if (perf.max_speed !== undefined && perf.max_speed !== null) {
                    html += `<div class="metric-item"><strong>Max Speed:</strong> ${perf.max_speed.toFixed(2)} km/h</div>`;
                }
                
                if (perf.completion_date) {
                    html += `<div class="metric-item"><strong>Completed:</strong> ${new Date(perf.completion_date).toLocaleDateString()}</div>`;
                }
                
                html += '</div>';
                detailedMetrics.innerHTML = html;
            }
            
            // Performance chart (expandable) - render when expanded
            if (perf.time_series && perf.time_series.length > 0) {
                const chartToggle = performanceTab.querySelector('.expand-toggle[data-section="performance-chart"]');
                if (chartToggle) {
                    chartToggle._timeSeriesData = perf.time_series;
                    // Render chart when section is expanded
                    chartToggle.addEventListener('click', function() {
                        setTimeout(() => {
                            const content = chartToggle.nextElementSibling;
                            if (content && content.classList.contains('expandable-content') && content.style.display !== 'none') {
                                renderPerformanceChart(perf.time_series);
                            }
                        }, 100);
                    }, { once: true });
                }
            }
        } else {
            const summaryCards = performanceTab.querySelector('#performance-summary-cards');
            if (summaryCards) {
                summaryCards.innerHTML = '<p>No performance data available. Complete this trail to see your metrics.</p>';
            }
        }
    }
    
    function renderWeatherTab(weather) {
        const weatherTab = document.getElementById('weather-tab');
        if (!weatherTab) {
            showLoadingState('weather', 'No weather data available');
            return;
        }
        
        if (weather && weather.forecast && weather.forecast.length > 0) {
            // Summary cards (today + next 3 days) - template should have this
            const summaryCards = weatherTab.querySelector('#weather-summary-cards');
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
            
            // Full forecast (expandable) - template should have this
            const fullForecast = weatherTab.querySelector('#weather-forecast-full');
            if (fullForecast) {
                fullForecast.innerHTML = weather.forecast.map(day => {
                    const date = new Date(day.date);
                    const weatherIcon = getWeatherIcon(day.weather || '');
                    return `
                        <div class="weather-day-full">
                            <div class="weather-day-header">
                                <span class="weather-day-date">${date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</span>
                                <span class="weather-day-icon">${weatherIcon}</span>
                            </div>
                            <div class="weather-day-details">
                                <span class="weather-day-condition">${escapeHtml(day.weather || 'N/A')}</span>
                                ${day.temperature ? `<span class="weather-day-temp">${day.temperature}°C</span>` : ''}
                            </div>
                        </div>
                    `;
                }).join('');
            }
        } else {
            const summaryCards = weatherTab.querySelector('#weather-summary-cards');
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
    
    function renderRecommendationsTab(recommendations) {
        const recommendationsTab = document.getElementById('recommendations-tab');
        if (!recommendationsTab) {
            showLoadingState('recommendations', 'No recommendations available');
            return;
        }
        
        if (recommendations) {
            // Key tips (always visible - top 3-5) - template should have this
            const keyTips = recommendationsTab.querySelector('#recommendations-key-tips');
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
            
            // Full recommendations (expandable) - template should have this
            const fullRecommendations = recommendationsTab.querySelector('#ai-recommendations-full');
            if (fullRecommendations) {
                let html = '';
                
                if (recommendations.ai_explanation && recommendations.ai_explanation.explanation_text) {
                    html += `<div class="ai-explanation-full"><h5>Full Explanation</h5><p>${escapeHtml(recommendations.ai_explanation.explanation_text)}</p></div>`;
                }
                
                if (recommendations.ai_explanation && recommendations.ai_explanation.key_factors && recommendations.ai_explanation.key_factors.length > 0) {
                    html += '<div class="key-factors-section"><h5>Key Factors</h5><ul>';
                    recommendations.ai_explanation.key_factors.forEach(factor => {
                        html += `<li>${escapeHtml(factor)}</li>`;
                    });
                    html += '</ul></div>';
                }
                
                if (recommendations.profile_recommendations && recommendations.profile_recommendations.tips && recommendations.profile_recommendations.tips.length > 0) {
                    html += '<div class="all-tips-section"><h5>All Tips</h5><ul>';
                    recommendations.profile_recommendations.tips.forEach(tip => {
                        html += `<li>${escapeHtml(tip)}</li>`;
                    });
                    html += '</ul></div>';
                }
                
                if (!html) {
                    html = '<p>No detailed recommendations available</p>';
                }
                
                fullRecommendations.innerHTML = html;
            }
        } else {
            const keyTips = recommendationsTab.querySelector('#recommendations-key-tips');
            if (keyTips) {
                keyTips.innerHTML = '<p>No recommendations available</p>';
            }
        }
    }
    
    // Legacy function - kept for compatibility but refactored internally
    function renderTrailDetails(trail, recommendations, weather, performance) {
        // Legacy compatibility - delegate to new functions
        renderHeaderAndOverview(trail);
        renderPerformanceTab(performance);
        renderWeatherTab(weather);
        renderRecommendationsTab(recommendations);
    }
    
    function renderPerformanceChart(timeSeries) {
        const canvas = document.getElementById('performance-chart');
        if (!canvas || typeof Chart === 'undefined') {
            console.warn('Chart.js not available or canvas not found');
            return;
        }
        
        // Destroy existing chart if it exists
        if (canvas.chart) {
            canvas.chart.destroy();
        }
        
        const ctx = canvas.getContext('2d');
        const labels = timeSeries.map((point, index) => {
            // Convert timestamp to time string or use index
            if (point.timestamp) {
                const date = new Date(point.timestamp);
                return date.toLocaleTimeString();
            }
            return index.toString();
        });
        
        canvas.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Heart Rate (bpm)',
                        data: timeSeries.map(p => p.heart_rate || null),
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        yAxisID: 'y',
                        tension: 0.1
                    },
                    {
                        label: 'Speed (km/h)',
                        data: timeSeries.map(p => p.speed || null),
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        yAxisID: 'y1',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Heart Rate (bpm)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Speed (km/h)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });
    }
    
    function saveTrail(trailId) {
        fetch(`/api/profile/${currentUserId}/trails/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trail_id: trailId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Trail saved successfully!');
                loadTrails();
            } else {
                alert('Trail is already saved');
            }
        })
        .catch(error => {
            console.error('Error saving trail:', error);
            alert('Error saving trail');
        });
    }
    
    function startTrail(trailId) {
        fetch(`/api/profile/${currentUserId}/trails/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trail_id: trailId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Trail started!');
                loadTrails();
            } else {
                alert('Trail is already started');
            }
        })
        .catch(error => {
            console.error('Error starting trail:', error);
            alert('Error starting trail');
        });
    }
    
    // Helper function to show a custom modal dialog
    function showCompleteTrailModal(trailId) {
        return new Promise((resolve) => {
            // Create modal overlay
            const overlay = document.createElement('div');
            overlay.className = 'complete-trail-modal-overlay';
            overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:10000;display:flex;align-items:center;justify-content:center;';
            
            // Create modal content
            const modal = document.createElement('div');
            modal.className = 'complete-trail-modal';
            modal.style.cssText = 'background:white;padding:30px;border-radius:8px;max-width:400px;width:90%;box-shadow:0 4px 6px rgba(0,0,0,0.1);';
            
            modal.innerHTML = `
                <h3 style="margin-top:0;">Complete Trail</h3>
                <p>Rate this trail (1-5, or leave empty for default):</p>
                <input type="number" id="trail-rating-input" min="1" max="5" step="0.1" placeholder="Rating (optional)" style="width:100%;padding:8px;margin-bottom:15px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;">
                <div style="display:flex;gap:10px;justify-content:flex-end;">
                    <button id="complete-trail-cancel" style="padding:8px 16px;border:1px solid #ddd;background:white;border-radius:4px;cursor:pointer;">Cancel</button>
                    <button id="complete-trail-confirm" style="padding:8px 16px;border:none;background:#10b981;color:white;border-radius:4px;cursor:pointer;">Complete</button>
                </div>
            `;
            
            overlay.appendChild(modal);
            document.body.appendChild(overlay);
            
            const ratingInput = modal.querySelector('#trail-rating-input');
            const confirmBtn = modal.querySelector('#complete-trail-confirm');
            const cancelBtn = modal.querySelector('#complete-trail-cancel');
            
            // Focus input
            setTimeout(() => ratingInput.focus(), 100);
            
            // Handle confirm
            confirmBtn.addEventListener('click', () => {
                let rating = null;
                const value = ratingInput.value.trim();
                if (value !== '') {
                    rating = parseFloat(value);
                    if (isNaN(rating) || rating < 1 || rating > 5) {
                        alert('Invalid rating. Please enter a number between 1 and 5.');
                        return;
                    }
                }
                document.body.removeChild(overlay);
                resolve({ confirmed: true, rating: rating });
            });
            
            // Handle cancel
            cancelBtn.addEventListener('click', () => {
                document.body.removeChild(overlay);
                resolve({ confirmed: false, rating: null });
            });
            
            // Handle overlay click
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    document.body.removeChild(overlay);
                    resolve({ confirmed: false, rating: null });
                }
            });
            
            // Handle Enter key
            ratingInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    confirmBtn.click();
                }
            });
        });
    }
    
    function completeTrail(trailId) {
        if (!trailId) {
            console.error('No trailId provided to completeTrail');
            alert('Error: No trail ID provided');
            return;
        }
        
        if (!currentUserId) {
            console.error('No currentUserId in completeTrail');
            alert('Error: User not logged in');
            return;
        }
        
        // Show custom modal
        showCompleteTrailModal(trailId).then(result => {
            if (!result.confirmed) {
                return;
            }
            
            const payload = {};
            if (result.rating !== null) {
                payload.rating = result.rating;
            }
            
            fetch(`/api/profile/${currentUserId}/trails/${trailId}/complete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.error || 'Failed to complete trail');
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    alert('Trail marked as completed!');
                    loadTrails();
                } else {
                    alert('Failed to complete trail');
                }
            })
            .catch(error => {
                console.error('Error completing trail:', error);
                alert('Error completing trail: ' + error.message);
            });
        });
    }
    
    function setupDetailTabs() {
        if (tabsInitialized) return; // Already initialized
        
        const content = document.getElementById('trail-detail-content');
        if (!content) return;
        
        const modalContentWrapper = content.querySelector('.trail-detail-modal-content');
        if (!modalContentWrapper) return;
        
        // Store current trail data for lazy loading
        let currentTrailData = null;
        
        // Use event delegation on the modal content wrapper
        // This handles tabs even if they're dynamically created
        modalContentWrapper.addEventListener('click', function(e) {
            const tab = e.target.closest('.detail-tab');
            if (!tab) return;
            
            e.preventDefault();
            e.stopPropagation();
            
            const targetTab = tab.getAttribute('data-tab');
            if (!targetTab) return;
            
            // Update tab buttons
            modalContentWrapper.querySelectorAll('.detail-tab').forEach(t => {
                t.classList.remove('active');
            });
            tab.classList.add('active');
            
            // Update tab content
            modalContentWrapper.querySelectorAll('.detail-tab-content').forEach(tabContent => {
                tabContent.classList.remove('active');
            });
            
            const targetContent = modalContentWrapper.querySelector(`#${targetTab}-tab`);
            if (targetContent) {
                targetContent.classList.add('active');
                
                // Lazy load map when map tab is activated
                if (targetTab === 'map') {
                    if (currentTrailData && currentTrailData.coordinates) {
                        const mapContainer = targetContent.querySelector('#trail-map-container');
                        if (mapContainer && !mapContainer._mapInitialized) {
                            renderMapTab(currentTrailData);
                            mapContainer._mapInitialized = true;
                        }
                    } else {
                    }
                }
            }
        });
        
        // Store trail data setter
        window._setCurrentTrailData = function(trail) {
            currentTrailData = trail;
        };
        
        tabsInitialized = true;
    }
    
    // Close modal
    const modal = document.getElementById('trail-detail-modal');
    if (modal) {
        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
    
    function updateCounts() {
        const savedCount = document.getElementById('saved-count');
        const startedCount = document.getElementById('started-count');
        const completedCount = document.getElementById('completed-count');
        
        if (!trails) {
            console.warn('trails object is null when updating counts');
            return;
        }
        
        // Ensure trails object has the right structure
        if (!trails) {
            console.warn('trails object is null when updating counts');
            trails = { saved: [], started: [], completed: [] };
        }
        
        if (!trails.saved) trails.saved = [];
        if (!trails.started) trails.started = [];
        if (!trails.completed) trails.completed = [];
        
        const savedLength = trails.saved.length;
        const startedLength = trails.started.length;
        const completedLength = trails.completed.length;
        
        if (savedCount) {
            savedCount.textContent = savedLength;
        } else {
            console.warn('saved-count element not found in DOM');
        }
        
        if (startedCount) {
            startedCount.textContent = startedLength;
        } else {
            console.warn('started-count element not found in DOM');
        }
        
        if (completedCount) {
            completedCount.textContent = completedLength;
        } else {
            console.warn('completed-count element not found in DOM');
        }
    }
    
    // View Mode Management
    function setupViewModeToggle() {
        const buttons = document.querySelectorAll('.view-mode-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', function() {
                const mode = this.getAttribute('data-view');
                switchViewMode(mode);
            });
        });
    }
    
    function switchViewMode(mode) {
        currentViewMode = mode;
        localStorage.setItem('trail-view-mode', mode);
        
        // Update button states
        document.querySelectorAll('.view-mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-view') === mode);
        });
        
        // Update container classes for smooth transitions
        document.querySelectorAll('.trail-list').forEach(container => {
            container.classList.remove('view-grid', 'view-list', 'view-timeline');
            container.classList.add(`view-${mode}`);
        });
        
        // Trigger re-render with animation
        setTimeout(() => {
            renderTrails();
        }, 50);
    }
    
    // Search Functionality
    function setupSearch() {
        const searchInput = document.getElementById('trail-search');
        if (!searchInput) return;
        
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchQuery = this.value.toLowerCase().trim();
                renderTrails();
            }, 300);
        });
    }
    
    function applySearch(trailList) {
        if (!searchQuery) return trailList;
        return trailList.filter(trail => {
            const name = (trail.name || '').toLowerCase();
            return name.includes(searchQuery);
        });
    }
    
    // Filter Functionality
    function setupFilters() {
        const filterToggle = document.getElementById('filter-toggle');
        const filterPanel = document.getElementById('filter-panel');
        const clearFiltersBtn = document.querySelector('.btn-clear-filters');
        
        if (filterToggle && filterPanel) {
            filterToggle.addEventListener('click', () => {
                filterPanel.style.display = filterPanel.style.display === 'none' ? 'block' : 'none';
            });
        }
        
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                clearAllFilters();
            });
        }
        
        // Difficulty filters
        document.querySelectorAll('.filter-checkbox[data-filter="difficulty"]').forEach(cb => {
            cb.addEventListener('change', updateFilters);
        });
        
        // Rating filters
        document.querySelectorAll('.filter-checkbox[data-filter="rating"]').forEach(cb => {
            cb.addEventListener('change', updateFilters);
        });
        
        // Distance range
        const distanceMin = document.getElementById('distance-min');
        const distanceMax = document.getElementById('distance-max');
        const distanceMinLabel = document.getElementById('distance-min-label');
        const distanceMaxLabel = document.getElementById('distance-max-label');
        
        if (distanceMin && distanceMax) {
            [distanceMin, distanceMax].forEach(input => {
                input.addEventListener('input', function() {
                    if (distanceMinLabel) distanceMinLabel.textContent = distanceMin.value;
                    if (distanceMaxLabel) distanceMaxLabel.textContent = distanceMax.value;
                    updateFilters();
                });
            });
        }
    }
    
    function updateFilters() {
        currentFilters = {};
        
        // Difficulty
        const difficultyFilters = Array.from(document.querySelectorAll('.filter-checkbox[data-filter="difficulty"]:checked'))
            .map(cb => cb.value);
        if (difficultyFilters.length > 0) {
            currentFilters.difficulty = difficultyFilters;
        }
        
        // Rating
        const ratingFilters = Array.from(document.querySelectorAll('.filter-checkbox[data-filter="rating"]:checked'))
            .map(cb => parseInt(cb.value));
        if (ratingFilters.length > 0) {
            currentFilters.rating = ratingFilters;
        }
        
        // Distance
        const distanceMin = parseFloat(document.getElementById('distance-min')?.value || 0);
        const distanceMax = parseFloat(document.getElementById('distance-max')?.value || 50);
        if (distanceMin > 0 || distanceMax < 50) {
            currentFilters.distance = { min: distanceMin, max: distanceMax };
        }
        
        updateFilterUI();
        renderTrails();
    }
    
    function clearAllFilters() {
        document.querySelectorAll('.filter-checkbox').forEach(cb => cb.checked = false);
        const distanceMin = document.getElementById('distance-min');
        const distanceMax = document.getElementById('distance-max');
        if (distanceMin) distanceMin.value = 0;
        if (distanceMax) distanceMax.value = 50;
        if (document.getElementById('distance-min-label')) document.getElementById('distance-min-label').textContent = '0';
        if (document.getElementById('distance-max-label')) document.getElementById('distance-max-label').textContent = '50';
        
        currentFilters = {};
        updateFilterUI();
        renderTrails();
    }
    
    function applyFilters(trailList, status) {
        let filtered = [...trailList];
        
        // Difficulty filter
        if (currentFilters.difficulty && currentFilters.difficulty.length > 0) {
            filtered = filtered.filter(trail => {
                if (!trail.difficulty) return false;
                const level = trail.difficulty <= 3 ? 'easy' : trail.difficulty <= 7 ? 'medium' : 'hard';
                return currentFilters.difficulty.includes(level);
            });
        }
        
        // Distance filter
        if (currentFilters.distance) {
            filtered = filtered.filter(trail => {
                const dist = parseFloat(trail.distance) || 0;
                return dist >= currentFilters.distance.min && dist <= currentFilters.distance.max;
            });
        }
        
        // Rating filter (only for completed trails)
        if (currentFilters.rating && currentFilters.rating.length > 0 && status === 'completed') {
            filtered = filtered.filter(trail => {
                const rating = trail.rating || 0;
                return currentFilters.rating.includes(Math.floor(rating));
            });
        }
        
        return filtered;
    }
    
    function updateFilterUI() {
        const filterCount = Object.keys(currentFilters).length;
        const filterCountEl = document.getElementById('filter-count');
        const activeFiltersEl = document.getElementById('active-filters');
        
        if (filterCountEl) {
            filterCountEl.textContent = filterCount;
            filterCountEl.style.display = filterCount > 0 ? 'inline-block' : 'none';
        }
        
        if (activeFiltersEl) {
            if (filterCount === 0) {
                activeFiltersEl.style.display = 'none';
                activeFiltersEl.innerHTML = '';
            } else {
                activeFiltersEl.style.display = 'flex';
                let chips = '';
                if (currentFilters.difficulty) {
                    currentFilters.difficulty.forEach(d => {
                        chips += `<span class="filter-chip">Difficulty: ${d}<button class="chip-remove" data-filter="difficulty" data-value="${d}">×</button></span>`;
                    });
                }
                if (currentFilters.rating) {
                    currentFilters.rating.forEach(r => {
                        chips += `<span class="filter-chip">Rating: ${r}⭐<button class="chip-remove" data-filter="rating" data-value="${r}">×</button></span>`;
                    });
                }
                if (currentFilters.distance) {
                    chips += `<span class="filter-chip">Distance: ${currentFilters.distance.min}-${currentFilters.distance.max}km<button class="chip-remove" data-filter="distance">×</button></span>`;
                }
                activeFiltersEl.innerHTML = chips;
                
                // Attach remove handlers
                activeFiltersEl.querySelectorAll('.chip-remove').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const filter = this.getAttribute('data-filter');
                        const value = this.getAttribute('data-value');
                        if (filter === 'difficulty') {
                            document.querySelector(`.filter-checkbox[data-filter="difficulty"][value="${value}"]`).checked = false;
                        } else if (filter === 'rating') {
                            document.querySelector(`.filter-checkbox[data-filter="rating"][value="${value}"]`).checked = false;
                        } else if (filter === 'distance') {
                            document.getElementById('distance-min').value = 0;
                            document.getElementById('distance-max').value = 50;
                            document.getElementById('distance-min-label').textContent = '0';
                            document.getElementById('distance-max-label').textContent = '50';
                        }
                        updateFilters();
                    });
                });
            }
        }
    }
    
    // Sort Functionality
    function setupSort() {
        const sortSelect = document.getElementById('trail-sort');
        if (!sortSelect) return;
        
        const savedSort = localStorage.getItem('trail-sort');
        if (savedSort) {
            sortSelect.value = savedSort;
            currentSort = savedSort;
        }
        
        sortSelect.addEventListener('change', function() {
            currentSort = this.value;
            localStorage.setItem('trail-sort', currentSort);
            renderTrails();
        });
    }
    
    function applySort(trailList, status) {
        const [sortBy, order] = currentSort.split('-');
        const sorted = [...trailList].sort((a, b) => {
            let aVal, bVal;
            
            switch (sortBy) {
                case 'date':
                    if (status === 'completed') {
                        aVal = a.completion_date ? new Date(a.completion_date) : new Date(0);
                        bVal = b.completion_date ? new Date(b.completion_date) : new Date(0);
                    } else if (status === 'started') {
                        aVal = a.start_date ? new Date(a.start_date) : new Date(0);
                        bVal = b.start_date ? new Date(b.start_date) : new Date(0);
                    } else {
                        aVal = a.saved_date ? new Date(a.saved_date) : new Date(0);
                        bVal = b.saved_date ? new Date(b.saved_date) : new Date(0);
                    }
                    break;
                case 'name':
                    aVal = (a.name || '').toLowerCase();
                    bVal = (b.name || '').toLowerCase();
                    break;
                case 'distance':
                    aVal = parseFloat(a.distance) || 0;
                    bVal = parseFloat(b.distance) || 0;
                    break;
                case 'difficulty':
                    aVal = parseFloat(a.difficulty) || 0;
                    bVal = parseFloat(b.difficulty) || 0;
                    break;
                case 'rating':
                    aVal = parseFloat(a.rating) || 0;
                    bVal = parseFloat(b.rating) || 0;
                    break;
                case 'progress':
                    aVal = parseFloat(a.progress_percentage) || 0;
                    bVal = parseFloat(b.progress_percentage) || 0;
                    break;
                default:
                    return 0;
            }
            
            if (aVal < bVal) return order === 'asc' ? -1 : 1;
            if (aVal > bVal) return order === 'asc' ? 1 : -1;
            return 0;
        });
        
        return sorted;
    }
    
    // Keyboard Navigation
    function setupKeyboardNavigation() {
        document.addEventListener('keydown', function(e) {
            // Don't interfere with input fields
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            // Tab switching: S for Saved, T for Started, C for Completed
            if (e.key.toLowerCase() === 's' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                switchTab('saved');
            } else if (e.key.toLowerCase() === 't' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                switchTab('started');
            } else if (e.key.toLowerCase() === 'c' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                switchTab('completed');
            }
            
            // View mode switching: G for Grid, L for List, M for Timeline
            if (e.key.toLowerCase() === 'g' && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
                e.preventDefault();
                switchViewMode('grid');
            } else if (e.key.toLowerCase() === 'l' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                switchViewMode('list');
            } else if (e.key.toLowerCase() === 'm' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                switchViewMode('timeline');
            }
            
            // Escape to close filter panel
            if (e.key === 'Escape') {
                const filterPanel = document.getElementById('filter-panel');
                if (filterPanel && filterPanel.style.display !== 'none') {
                    filterPanel.style.display = 'none';
                }
            }
        });
    }
    
    function switchTab(tabType) {
        const tab = document.querySelector(`.trail-tab[data-tab="${tabType}"]`);
        if (tab) {
            tab.click();
        }
    }
    
    
    return {
        init: init,
        loadTrails: loadTrails,
        updateCounts: updateCounts,
        refreshCounts: refreshCounts
    };
})();

// Initialize on page load (fallback - prefer explicit init from template)
document.addEventListener('DOMContentLoaded', function() {
    // Only auto-initialize if not already initialized
    // The profile.html template should call TrailListManager.init() explicitly
    // This is just a fallback for other pages that might use this script
    // Try to get userId from URL
    const userId = parseInt(window.location.pathname.split('/').pop());
    if (userId && !isNaN(userId)) {
        TrailListManager.init(userId);
    }
});
