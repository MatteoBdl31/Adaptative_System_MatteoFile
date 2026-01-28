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
    
    // Tab-related functions removed - no longer using tabs
    
    function init(userId, userProfile) {
        currentUserId = userId;
        currentUserProfile = userProfile || currentUserProfile || null;
        
        // Load saved preferences (timeline view removed; fallback to grid if stored)
        const savedViewMode = localStorage.getItem('trail-view-mode') || 'grid';
        switchViewMode(savedViewMode === 'timeline' ? 'grid' : savedViewMode);
        
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
    
    /**
     * Show celebratory popup with confetti when user's profile category changes after completing a trail.
     * @param {Object} data - API response with profile_changed, new_profile_display_name, previous_profile_display_name
     * @param {Function} onClose - Callback when user dismisses (e.g. loadTrails)
     */
    function showProfileChangeCelebration(data, onClose) {
        if (typeof onClose !== 'function') onClose = function() {};
        var newName = (data && data.new_profile_display_name) ? data.new_profile_display_name : 'your new profile';
        var title = 'You\u2019ve evolved!';
        var message = 'Your new trail shifted your profile. You are now: ';
        var overlay = document.createElement('div');
        overlay.className = 'profile-change-celebration-overlay';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-labelledby', 'profile-change-title');
        overlay.innerHTML =
            '<div class="profile-change-celebration">' +
            '  <div class="profile-change-celebration__confetti-canvas" id="profile-change-confetti-canvas" aria-hidden="true"></div>' +
            '  <div class="profile-change-celebration__card">' +
            '    <h2 id="profile-change-title" class="profile-change-celebration__title">' + title + '</h2>' +
            '    <p class="profile-change-celebration__message">' + message + '<strong class="profile-change-celebration__profile-name">' + newName + '</strong></p>' +
            '    <p class="profile-change-celebration__sub">Your recommendations will adapt to your new style.</p>' +
            '    <button type="button" class="profile-change-celebration__cta">Awesome!</button>' +
            '  </div>' +
            '</div>';
        document.body.appendChild(overlay);
        if (typeof confetti === 'function') {
            try {
                confetti({ particleCount: 140, spread: 80, origin: { y: 0.6 } });
                setTimeout(function() {
                    confetti({ particleCount: 80, spread: 100, origin: { y: 0.5, x: 0.3 } });
                    confetti({ particleCount: 80, spread: 100, origin: { y: 0.5, x: 0.7 } });
                }, 200);
            } catch (e) { /* no confetti if lib missing */ }
        }
        function dismiss() {
            if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
            onClose();
        }
        overlay.querySelector('.profile-change-celebration__cta').addEventListener('click', dismiss);
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) dismiss();
        });
    }
    
    function setupTabs() {
        const tabs = document.querySelectorAll('.trail-tab');
        const lists = document.querySelector('#trail-lists');
        if (!lists) return;
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const tabType = this.getAttribute('data-tab');
                if (!tabType) return;
                var panel = document.getElementById(tabType + '-trails');
                if (!panel) return;
                tabs.forEach(function(t) { t.classList.remove('active'); });
                this.classList.add('active');
                lists.querySelectorAll('.trail-list').forEach(function(list) {
                    list.classList.remove('active');
                });
                panel.classList.add('active');
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
        // Display rating for completed trails - ensure it's a valid number
        const ratingStars = status === 'completed' && (trail.rating !== null && trail.rating !== undefined)
            ? createRatingStars(trail.rating) 
            : '';
        const statisticsBadge = status === 'saved' && (trail.start_count > 0 || trail.completion_count > 0)
            ? createStatisticsBadge(trail.start_count || 0, trail.completion_count || 0)
            : '';
        
        const cardClass = `trail-card trail-card-${viewMode} trail-card-${status}`;
        
        if (viewMode === 'list') {
            // List view: one compact row. No performance indicators (HR, speed, calories) — use "View" for details.
            return `
                <div class="${cardClass}" data-trail-id="${trail.trail_id}">
                    <div class="trail-card-list-content">
                        <div class="trail-card-list-main">
                            ${statusBadge}
                            ${difficultyBadge}
                            <h3 class="trail-name trail-name-list">${escapeHtml(trail.name || trail.trail_id)}</h3>
                            <div class="trail-info-compact">
                                <span>${trail.distance != null ? trail.distance : 'N/A'} km</span>
                                <span>${trail.elevation_gain != null ? trail.elevation_gain : 'N/A'} m</span>
                                <span>${formatDuration(trail.estimated_duration || trail.actual_duration || trail.duration)}</span>
                            </div>
                            ${dateBadge}
                            ${statisticsBadge}
                            ${ratingStars}
                        </div>
                        <div class="trail-card-list-actions">
                            ${progressRing}
                            <div class="trail-actions">
                                <button class="btn-view-details" data-trail-id="${trail.trail_id}">View</button>
                                ${status === 'saved' ? '<button class="btn-start-trail" data-trail-id="' + trail.trail_id + '">Start Trail</button>' : ''}
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
                    ${statisticsBadge}
                    ${ratingStars}
                    ${performanceIndicators}
                    ${dateBadge}
                    <div class="trail-actions">
                        <button class="btn-view-details" data-trail-id="${trail.trail_id}">View Details</button>
                        ${status === 'saved' ? '<button class="btn-start-trail" data-trail-id="' + trail.trail_id + '">Start Trail</button>' : ''}
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
        if (!trail.avg_heart_rate && !trail.avg_speed && !trail.total_calories && !trail.difficulty_rating) return '';
        
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
        if (trail.difficulty_rating !== null && trail.difficulty_rating !== undefined) {
            html += `<span class="perf-indicator" title="Difficulty Rating">📊 ${trail.difficulty_rating}/10</span>`;
        }
        html += '</div>';
        return html;
    }
    
    function createRatingStars(rating) {
        if (!rating && rating !== 0) return '';
        // Ensure rating is a number
        const numRating = typeof rating === 'string' ? parseFloat(rating) : Number(rating);
        if (isNaN(numRating) || numRating < 1 || numRating > 5) {
            console.warn('Invalid rating value:', rating);
            return '';
        }
        const fullStars = Math.floor(numRating);
        const hasHalfStar = numRating % 1 >= 0.5;
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
        html += ` <span class="rating-value">${numRating.toFixed(1)}</span></div>`;
        return html;
    }
    
    function createStatisticsBadge(startCount, completionCount) {
        if (startCount === 0 && completionCount === 0) return '';
        let html = '<div class="trail-statistics-badge">';
        if (startCount > 0) {
            html += `<span class="stat-item" title="Times Started">▶️ ${startCount}</span>`;
        }
        if (completionCount > 0) {
            html += `<span class="stat-item" title="Times Completed">✅ ${completionCount}</span>`;
        }
        html += '</div>';
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
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function formatSafetyRisks(safetyRisks) {
        if (!safetyRisks) return 'No information';
        const risks = safetyRisks.toLowerCase().trim();
        if (risks === 'low' || risks === 'none' || risks === '') {
            return 'Low risk - Generally safe';
        }
        // Format other risks (e.g., "slippery,exposed" -> "Slippery, Exposed")
        return risks.split(',').map(r => {
            return r.trim().split(' ').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
        }).join(', ');
    }
    
    function getEmptyState(status) {
        const messages = {
            saved: {
                title: 'No saved trails yet',
                description: 'Browse trails and save your favorites to plan your next adventure!',
                cta: 'Browse Trails',
                ctaLink: '/demo'
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
                ctaLink: '/demo'
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
                // Navigate to trail detail page
                window.location.href = `/profile/${currentUserId}/trail/${trailId}`;
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
        
        // Start trail buttons
        container.querySelectorAll('.btn-start-trail').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const trailId = this.getAttribute('data-trail-id');
                startTrail(trailId);
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
                
                // Show completion form
                showCompletionForm(trailId);
            });
        });
    }
    
    function startTrail(trailId) {
        if (!currentUserId) {
            alert('Error: User not logged in');
            return;
        }
        
        fetch(`/api/profile/${currentUserId}/trails/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ trail_id: trailId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadTrails();
            } else {
                alert('Failed to start trail');
            }
        })
        .catch(error => {
            console.error('Error starting trail:', error);
            alert('Error starting trail');
        });
    }
    
    function showCompletionForm(trailId) {
        const modal = document.createElement('div');
        modal.className = 'completion-form-overlay';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-labelledby', 'completion-form-title');
        modal.innerHTML = `
            <div class="completion-form-card">
                <header class="completion-form-header">
                    <h2 id="completion-form-title" class="completion-form-title">Complete Trail</h2>
                    <button type="button" class="completion-form-close" aria-label="Close">&times;</button>
                </header>
                <form id="completion-form" class="completion-form">
                    <div class="completion-form-body">
                        <div class="form-group">
                            <label class="form-label">Trail rating (1–5 stars)</label>
                            <div class="rating-input-interactive" role="group" aria-label="Trail rating">
                                <input type="radio" name="rating" value="1" id="rating-1">
                                <label for="rating-1" data-rating="1" title="1 star – Poor">&#9733;</label>
                                <input type="radio" name="rating" value="2" id="rating-2">
                                <label for="rating-2" data-rating="2" title="2 stars – Fair">&#9733;</label>
                                <input type="radio" name="rating" value="3" id="rating-3">
                                <label for="rating-3" data-rating="3" title="3 stars – Good">&#9733;</label>
                                <input type="radio" name="rating" value="4" id="rating-4">
                                <label for="rating-4" data-rating="4" title="4 stars – Very good">&#9733;</label>
                                <input type="radio" name="rating" value="5" id="rating-5" checked>
                                <label for="rating-5" data-rating="5" title="5 stars – Excellent">&#9733;</label>
                            </div>
                            <span class="rating-display" id="rating-display" aria-live="polite">5 stars</span>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="difficulty-rating">Difficulty (1–10)</label>
                            <div class="difficulty-input">
                                <input type="range" id="difficulty-rating" name="difficulty_rating" min="1" max="10" value="5" aria-valuetext="5">
                                <span id="difficulty-value" class="difficulty-value">5</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="photos">Photos (optional)</label>
                            <div class="file-upload-trigger">
                                <input type="file" id="photos" name="photos" multiple accept="image/*" class="file-upload-input">
                                <button type="button" class="file-upload-btn" id="photos-trigger">
                                    <span class="file-upload-btn-icon" aria-hidden="true">+</span>
                                    <span class="file-upload-btn-text">Add photos</span>
                                    <span class="file-upload-btn-hint">image files</span>
                                </button>
                                <div id="photo-preview" class="photo-preview"></div>
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Smartwatch data (optional)</label>
                            <div class="file-upload-trigger">
                                <input type="file" id="trail-file" name="trail_file" accept=".json,.gpx,.fit" class="file-upload-input">
                                <button type="button" class="file-upload-btn" id="trail-file-trigger">
                                    <span class="file-upload-btn-icon" aria-hidden="true">+</span>
                                    <span class="file-upload-btn-text">Add smartwatch file</span>
                                    <span class="file-upload-btn-hint">.json, .gpx, .fit</span>
                                </button>
                                <div id="file-info" class="file-info u-hidden"></div>
                            </div>
                        </div>
                    </div>
                    <footer class="completion-form-actions">
                        <button type="button" class="completion-form-btn completion-form-btn--secondary btn-cancel">Cancel</button>
                        <button type="submit" class="completion-form-btn completion-form-btn--primary btn-submit">Complete Trail</button>
                    </footer>
                </form>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Make rating stars interactive
        const ratingInputs = modal.querySelectorAll('.rating-input-interactive input[type="radio"]');
        const ratingDisplay = modal.querySelector('#rating-display');
        ratingInputs.forEach(input => {
            input.addEventListener('change', function() {
                const value = parseInt(this.value);
                ratingDisplay.textContent = value === 1 ? '1 star' : `${value} stars`;
                // Update visual feedback
                ratingInputs.forEach(inp => {
                    const label = modal.querySelector(`label[for="${inp.id}"]`);
                    if (label) {
                        if (parseInt(inp.value) <= value) {
                            label.classList.add('star-selected');
                        } else {
                            label.classList.remove('star-selected');
                        }
                    }
                });
            });
        });
        // Initialize display
        ratingDisplay.textContent = '5 stars';
        ratingInputs.forEach(inp => {
            if (inp.checked) {
                const value = parseInt(inp.value);
                ratingInputs.forEach(inp2 => {
                    const label = modal.querySelector(`label[for="${inp2.id}"]`);
                    if (label && parseInt(inp2.value) <= value) {
                        label.classList.add('star-selected');
                    }
                });
            }
        });
        
        // Update difficulty value display
        const difficultySlider = modal.querySelector('#difficulty-rating');
        const difficultyValue = modal.querySelector('#difficulty-value');
        difficultySlider.addEventListener('input', function() {
            difficultyValue.textContent = this.value;
        });
        
        const fileInput = modal.querySelector('#trail-file');
        const fileInfo = modal.querySelector('#file-info');
        const fileTriggerBtn = modal.querySelector('#trail-file-trigger');
        const photoInput = modal.querySelector('#photos');
        const photosTriggerBtn = modal.querySelector('#photos-trigger');
        
        if (fileTriggerBtn && fileInput) {
            fileTriggerBtn.addEventListener('click', function() {
                fileInput.click();
            });
        }
        if (photosTriggerBtn && photoInput) {
            photosTriggerBtn.addEventListener('click', function() {
                photoInput.click();
            });
        }
        
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                fileInfo.textContent = this.files[0].name;
                fileInfo.classList.remove('u-hidden');
            } else {
                fileInfo.classList.add('u-hidden');
            }
        });
        
        // Handle photo preview
        const photoPreview = modal.querySelector('#photo-preview');
        photoInput.addEventListener('change', function() {
            photoPreview.innerHTML = '';
            Array.from(this.files).forEach(file => {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.className = 'photo-preview-item';
                    photoPreview.appendChild(img);
                };
                reader.readAsDataURL(file);
            });
        });
        
        // Close handlers
        modal.querySelector('.completion-form-close').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        modal.querySelector('.btn-cancel').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
        
        // Form submission
        modal.querySelector('#completion-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const ratingInput = this.querySelector('input[name="rating"]:checked');
            if (!ratingInput) {
                alert('Please select a rating');
                return;
            }
            
            const formData = new FormData();
            // Convert rating to number to ensure proper storage
            const ratingValue = parseInt(ratingInput.value, 10);
            formData.append('rating', ratingValue);
            formData.append('difficulty_rating', parseInt(difficultySlider.value, 10));
            
            // Add photos
            const photos = photoInput.files;
            for (let i = 0; i < photos.length; i++) {
                formData.append('photos', photos[i]);
            }
            
            if (fileInput.files.length > 0) {
                formData.append('trail_file', fileInput.files[0]);
            }
            
            // Submit
            fetch(`/api/profile/${currentUserId}/trails/${trailId}/complete`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.body.removeChild(modal);
                    if (data.profile_changed) {
                        showProfileChangeCelebration(data, loadTrails);
                    } else {
                        loadTrails();
                    }
                } else {
                    alert('Failed to complete trail: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error completing trail:', error);
                alert('Error completing trail');
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
    function ensureModalStructure() {
        const content = document.getElementById('trail-detail-content');
        if (!content) {
            console.error('trail-detail-content element not found');
            return false;
        }
        
        // Check if template is already inserted
        let modalContentWrapper = content.querySelector('.trail-detail-modal-content');
        if (!modalContentWrapper) {
            const template = document.getElementById('trail-detail-modal-template');
            if (template) {
                console.log('Inserting template into modal content');
                content.innerHTML = template.innerHTML;
                // Clear cache since DOM structure changed
                cachedElements = null;
                // Verify template was inserted
                modalContentWrapper = content.querySelector('.trail-detail-modal-content');
                if (!modalContentWrapper) {
                    console.error('Template inserted but .trail-detail-modal-content not found');
                    return false;
                }
                console.log('Template successfully inserted');
                return true;
            } else {
                console.error('trail-detail-modal-template not found');
                return false;
            }
        }
        return true;
    }
    
    function getCachedElements() {
        if (cachedElements) {
            return cachedElements;
        }
        
        const content = document.getElementById('trail-detail-content');
        if (!content) {
            console.error('trail-detail-content not found');
            return null;
        }
        
        // Try to find the wrapper - it might be the content itself or a child
        let modalContentWrapper = content.querySelector('.trail-detail-modal-content');
        if (!modalContentWrapper) {
            // If no wrapper found, check if content itself has the structure
            if (content.querySelector('#trail-detail-name')) {
                modalContentWrapper = content;
            } else {
                console.warn('trail-detail-modal-content wrapper not found, using content as fallback');
                modalContentWrapper = content;
            }
        }
        
        // Find overview tab - it's inside .trail-detail-content div
        const detailContentDiv = modalContentWrapper.querySelector('.trail-detail-content');
        const overviewTab = detailContentDiv ? detailContentDiv.querySelector('#overview-tab') : modalContentWrapper.querySelector('#overview-tab');
        
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
            performanceTab: (detailContentDiv || modalContentWrapper).querySelector('#performance-tab'),
            weatherTab: (detailContentDiv || modalContentWrapper).querySelector('#weather-tab'),
            recommendationsTab: (detailContentDiv || modalContentWrapper).querySelector('#recommendations-tab'),
            elevationTab: (detailContentDiv || modalContentWrapper).querySelector('#elevation-tab'),
            mapTab: (detailContentDiv || modalContentWrapper).querySelector('#map-tab'),
            galleryTab: (detailContentDiv || modalContentWrapper).querySelector('#gallery-tab'),
            description: modalContentWrapper.querySelector('#trail-description'),
            landscapes: modalContentWrapper.querySelector('#trail-landscapes'),
            performanceMetrics: modalContentWrapper.querySelector('#performance-metrics'),
            weatherForecast: modalContentWrapper.querySelector('#weather-forecast'),
            aiRecommendations: modalContentWrapper.querySelector('#ai-recommendations')
        };
        
        // Debug logging
        if (!cachedElements.name) {
            console.warn('Could not find trail name element. Available elements:', {
                wrapper: modalContentWrapper,
                content: content,
                hasHeader: !!cachedElements.header
            });
        }
        
        return cachedElements;
    }
    
    function showLoadingState(sectionId, message = 'Loading...') {
        // Map section IDs to element IDs
        const sectionMap = {
            'performance': 'trail-performance-section',
            'weather': 'trail-weather-section',
            'recommendations': 'trail-recommendations-section',
            'overview': 'trail-overview-section'
        };
        
        const sectionElementId = sectionMap[sectionId] || `trail-${sectionId}-section`;
        const sectionElement = document.getElementById(sectionElementId);
        
        if (sectionElement) {
            // Find the summary cards or main content area
            const summaryCards = sectionElement.querySelector(`#${sectionId}-summary-cards`) || 
                                sectionElement.querySelector(`#${sectionId}-summary`) ||
                                sectionElement.querySelector('.summary-cards');
            if (summaryCards) {
                summaryCards.innerHTML = `<div class="loading">${message}</div>`;
            } else {
                // Fallback: show in section itself
                const firstChild = sectionElement.querySelector('h3')?.nextElementSibling || sectionElement;
                if (firstChild && !firstChild.querySelector('.loading')) {
                    firstChild.innerHTML = `<div class="loading">${message}</div>`;
                }
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
        
        // Clear cache
        cachedElements = null;
        
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
        
        modal.style.display = 'block';
        
        // Progressive loading: Load trail first (fast), then other data
        fetch(`/api/trail/${trailId}`)
            .then(r => {
                if (!r.ok) {
                    console.error(`Trail API returned ${r.status} for trail ${trailId}`);
                    throw new Error(`Trail API returned ${r.status}`);
                }
                return r.json();
            })
            .then(trail => {
                if (!trail || !trail.trail_id) {
                    console.error('Invalid trail data received:', trail);
                    const content = document.getElementById('trail-detail-content');
                    if (content) {
                        content.innerHTML = `<div class="error">Invalid trail data received. Trail ID: ${trailId}</div>`;
                    }
                    return;
                }
                
                console.log('Trail data loaded successfully:', trail.trail_id, trail.name);
                
                // Store trail data for lazy loading
                if (typeof window._setCurrentTrailData === 'function') {
                    window._setCurrentTrailData(trail);
                }
                
                // Ensure modal structure exists
                if (!ensureModalStructure()) {
                    console.error('Failed to ensure modal structure before rendering');
                    return;
                }
                
                // Render all sections immediately
                setTimeout(() => {
                    // 1. Enhanced header
                    renderEnhancedHeader(trail);
                    
                    // 2. Image gallery (initial render, will be updated if performance photos available)
                    renderImageGallery(trail, trail.photos || []);
                    
                    // 3. Map and elevation (render immediately)
                    renderMapAndElevation(trail);
                    
                    // 4. Overview section
                    renderOverviewSection(trail);
                }, 200);
                
                // Check if this trail is completed - if so, get completion data
                let completedTrailData = null;
                const completedTrails = trails.completed || [];
                const matchingCompleted = completedTrails.filter(ct => ct.trail_id === trailId);
                if (matchingCompleted.length > 0) {
                    // Use the most recent completion
                    completedTrailData = matchingCompleted[matchingCompleted.length - 1];
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
                    // If we have completed trail data, use it; otherwise fetch from API
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
                    }).then(data => {
                        console.log('Using completed trail data for performance:', data);
                        return data;
                    }) : fetch(`/api/profile/${currentUserId}/trail/${trailId}/performance`)
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
                    console.log('Performance and weather data loaded:', { performance, weather });
                    // Render Performance and Weather sections as soon as data arrives
                    setTimeout(() => {
                        renderPerformanceSection(performance);
                        renderWeatherSection(weather);
                        
                        // Render image gallery with photos from performance data
                        if (performance && performance.completed && performance.performance && performance.performance.photos) {
                            renderImageGallery(trail, performance.performance.photos);
                        } else {
                            renderImageGallery(trail, []);
                        }
                    }, 150);
                    
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
                            // Render Recommendations section when ready
                            renderRecommendationsSection(recommendations);
                        });
                });
            })
            .catch(error => {
                console.error('Error loading trail details:', error);
                const overviewSection = document.getElementById('trail-overview-section');
                if (overviewSection) {
                    overviewSection.innerHTML = `<div class="error">Error loading trail details: ${error.message}. Please try again.</div>`;
                } else if (content) {
                    content.innerHTML = `<div class="error">Error loading trail details: ${error.message}. Please try again.</div>`;
                }
            });
        
        // Setup modal close handler
        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.onclick = function() {
                modal.style.display = 'none';
            };
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        };
    }
    
    // New render functions for single-page layout
    
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
            
            // Speed (if available from performance data)
            // Will be added when performance data loads
            
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
                // Handle image load errors
                mainImageEl.onerror = function() {
                    this.style.display = 'none';
                    console.warn(`Failed to load trail image: ${photoList[index]}`);
                };
            }
        }
        
        // Render thumbnails (2x2 grid, max 4 visible)
        let thumbnailsHTML = '';
        const visibleThumbnails = Math.min(4, photoList.length);
        for (let i = 0; i < visibleThumbnails; i++) {
            const isLast = i === visibleThumbnails - 1 && photoList.length > 4;
            thumbnailsHTML += `
                <div class="trail-gallery-thumbnail ${i === 0 ? 'active' : ''}" data-index="${i}">
                    <img src="/static/${photoList[i]}" alt="Thumbnail ${i + 1}" onerror="this.style.display='none'; console.warn('Failed to load thumbnail: ${photoList[i]}');" />
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
        // Render map
        const mapContainer = document.getElementById('trail-map-container');
        if (mapContainer && trail.coordinates) {
            // Clear existing map
            mapContainer.innerHTML = '';
            mapContainer._mapInitialized = false;
            
            const mapId = 'trail-detail-map';
            mapContainer.id = mapId;
            
            if (typeof MapManager !== 'undefined') {
                const mapManager = new MapManager();
                setTimeout(() => {
                    try {
                        let coordinates = [];
                        if (typeof trail.coordinates === 'string') {
                            try {
                                const geoJson = JSON.parse(trail.coordinates);
                                if (geoJson.type === 'LineString' && geoJson.coordinates) {
                                    coordinates = geoJson.coordinates.map(coord => [coord[1], coord[0]]);
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
                        if (typeof L !== 'undefined' && map) {
                            const polyline = L.polyline(coordinates, {
                                color: '#6366f1',
                                weight: 4,
                                opacity: 0.8
                            }).addTo(map);
                            
                            L.marker(coordinates[0], {
                                icon: L.divIcon({
                                    className: 'trail-start-marker',
                                    html: '<div style="background: #10b981; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-weight: bold;">S</div>',
                                    iconSize: [24, 24]
                                })
                            }).addTo(map).bindPopup('Start');
                            
                            L.marker(coordinates[coordinates.length - 1], {
                                icon: L.divIcon({
                                    className: 'trail-end-marker',
                                    html: '<div style="background: #ef4444; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-weight: bold;">E</div>',
                                    iconSize: [24, 24]
                                })
                            }).addTo(map).bindPopup('End');
                            
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
        
        // Render elevation chart
        const elevationSection = document.querySelector('.trail-elevation-section');
        if (elevationSection && trail.elevation_profile && trail.elevation_profile.length > 0) {
            const elevationSummary = elevationSection.querySelector('#elevation-summary');
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
            
            const chartContainer = elevationSection.querySelector('.chart-container');
            if (chartContainer) {
                let canvas = chartContainer.querySelector('#elevation-chart');
                if (!canvas) {
                    canvas = document.createElement('canvas');
                    canvas.id = 'elevation-chart';
                    chartContainer.appendChild(canvas);
                }
                
                setTimeout(() => {
                    if (!canvas || typeof Chart === 'undefined') {
                        console.warn('Chart.js not available or canvas not found for elevation chart');
                        return;
                    }
                    
                    if (canvas.chart) {
                        canvas.chart.destroy();
                    }
                    
                    const ctx = canvas.getContext('2d');
                    const elevationData = trail.elevation_profile.map(p => p.elevation || 0);
                    const distanceData = trail.elevation_profile.map((p, i) => {
                        if (i === 0) return 0;
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
        }
    }
    
    function renderHeaderAndOverview(trail, userProfile) {
        // Ensure modal structure is ready
        if (!ensureModalStructure()) {
            console.error('Failed to ensure modal structure in renderHeaderAndOverview');
            return;
        }
        
        // Wait a bit more for DOM to be fully ready
        setTimeout(() => {
            renderHeaderAndOverviewContent(trail, userProfile);
        }, 50);
    }
    
    function renderOverviewSection(trail) {
        const overviewSection = document.getElementById('trail-overview-section');
        if (!overviewSection) {
            console.warn('Overview section not found');
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
        
        if (fullDescContent && trail.description) {
            fullDescContent.innerHTML = `<p>${escapeHtml(trail.description).replace(/\n/g, '</p><p>')}</p>`;
        }
        
        if (detailsExpanded) {
            let detailsHTML = '<div class="trail-details-expanded-grid">';
            if (trail.region) detailsHTML += `<div><strong>Region:</strong> ${escapeHtml(trail.region)}</div>`;
            if (trail.popularity !== undefined) detailsHTML += `<div><strong>Popularity:</strong> ${trail.popularity}/10</div>`;
            if (trail.safety_risks) detailsHTML += `<div><strong>Safety:</strong> ${escapeHtml(formatSafetyRisks(trail.safety_risks))}</div>`;
            if (trail.accessibility) detailsHTML += `<div><strong>Accessibility:</strong> ${escapeHtml(trail.accessibility)}</div>`;
            if (trail.closed_seasons) detailsHTML += `<div><strong>Closed Seasons:</strong> ${escapeHtml(trail.closed_seasons)}</div>`;
            detailsHTML += '</div>';
            detailsExpanded.innerHTML = detailsHTML;
        }
    }
    
    function renderHeaderAndOverviewContent(trail, userProfile) {
        // Render enhanced header
        renderEnhancedHeader(trail);
        
        // Render overview section
        renderOverviewSection(trail);
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
    
    function renderPerformanceSection(performance) {
        console.log('renderPerformanceSection called with:', performance);
        const performanceSection = document.getElementById('trail-performance-section');
        if (!performanceSection) {
            console.error('Performance section element not found');
            return;
        }
        
        // Handle both data structures: {completed: true, performance: {...}} or direct performance object
        let perf = null;
        if (performance && performance.completed && performance.performance) {
            // Standard structure: {completed: true, performance: {...}}
            perf = performance.performance;
            console.log('Using performance.performance data:', perf);
        } else if (performance && performance.completed) {
            // If performance itself is the data (shouldn't happen but handle it)
            perf = performance;
            console.log('Using performance as data directly:', perf);
        } else if (performance && !performance.completed) {
            // Not completed, show message
            console.log('Trail not completed, showing empty state');
            const summaryCards = performanceSection.querySelector('#performance-summary-cards');
            if (summaryCards) {
                summaryCards.innerHTML = '<p>No performance data available. Complete this trail to see your metrics.</p>';
            }
            return;
        } else {
            console.log('No performance data provided:', performance);
            const summaryCards = performanceSection.querySelector('#performance-summary-cards');
            if (summaryCards) {
                summaryCards.innerHTML = '<p>No performance data available. Complete this trail to see your metrics.</p>';
            }
            return;
        }
        
        if (perf) {
            console.log('Rendering performance data:', perf);
            
            // Summary cards (always visible)
            const summaryCards = performanceSection.querySelector('#performance-summary-cards');
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
                
                if (perf.max_heart_rate !== undefined && perf.max_heart_rate !== null) {
                    html += `<div class="metric-item"><strong>Max Heart Rate:</strong> ${perf.max_heart_rate} bpm</div>`;
                }
                
                if (perf.avg_speed !== undefined && perf.avg_speed !== null) {
                    html += `<div class="metric-item"><strong>Avg Speed:</strong> ${perf.avg_speed.toFixed(2)} km/h</div>`;
                }
                
                if (perf.max_speed !== undefined && perf.max_speed !== null) {
                    html += `<div class="metric-item"><strong>Max Speed:</strong> ${perf.max_speed.toFixed(2)} km/h</div>`;
                }
                
                if (perf.difficulty_rating !== undefined && perf.difficulty_rating !== null) {
                    html += `<div class="metric-item"><strong>Difficulty Rating:</strong> ${perf.difficulty_rating}/10</div>`;
                }
                
                if (perf.completion_date) {
                    html += `<div class="metric-item"><strong>Completed:</strong> ${new Date(perf.completion_date).toLocaleDateString()}</div>`;
                }
                
                // Show photos if available
                if (perf.photos && perf.photos.length > 0) {
                    html += `<div class="metric-item"><strong>Photos:</strong> ${perf.photos.length} photo(s)</div>`;
                }
                
                html += '</div>';
                detailedMetrics.innerHTML = html;
            }
            
            // Performance chart (always visible)
            if (perf.time_series && perf.time_series.length > 0) {
                const chartContainer = performanceSection.querySelector('.chart-container');
                const canvas = performanceSection.querySelector('#performance-chart');
                if (canvas && chartContainer) {
                    setTimeout(() => {
                        renderPerformanceChart(perf.time_series);
                    }, 100);
                }
            }
        }
    }
    
    function renderWeatherSection(weather) {
        console.log('renderWeatherSection called with:', weather);
        const weatherSection = document.getElementById('trail-weather-section');
        if (!weatherSection) {
            console.error('Weather section element not found');
            return;
        }
        
        if (weather && weather.forecast && weather.forecast.length > 0) {
            // Summary cards (today + next 3 days)
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
            
            // Full forecast (always visible)
            const fullForecast = weatherSection.querySelector('#weather-forecast-full');
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
        console.log('renderRecommendationsSection called with:', recommendations);
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
            const keyTips = recommendationsSection.querySelector('#recommendations-key-tips');
            if (keyTips) {
                keyTips.innerHTML = '<p>No recommendations available</p>';
            }
        }
    }
    
    // Legacy function - kept for compatibility but refactored internally
    function renderTrailDetails(trail, recommendations, weather, performance) {
        // Legacy compatibility - delegate to new section functions
        renderEnhancedHeader(trail);
        renderOverviewSection(trail);
        renderMapAndElevation(trail);
        renderPerformanceSection(performance);
        renderWeatherSection(weather);
        renderRecommendationsSection(recommendations);
        
        // Render image gallery if photos available
        if (performance && performance.completed && performance.performance && performance.performance.photos) {
            renderImageGallery(trail, performance.performance.photos);
        } else {
            renderImageGallery(trail, []);
        }
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
                loadTrails();
            } else {
                alert('Error starting trail');
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
                    if (data.profile_changed) {
                        showProfileChangeCelebration(data, loadTrails);
                    } else {
                        alert('Trail marked as completed!');
                        loadTrails();
                    }
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
    
    // setupDetailTabs function removed - no longer using tabs
    
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
        if (mode === 'timeline') mode = 'grid'; // timeline view removed
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
