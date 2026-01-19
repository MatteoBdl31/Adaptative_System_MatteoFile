/**
 * Demo Page JavaScript
 * Handles multi-user comparison, form management, and results display
 */

(function() {
    'use strict';

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        const demoApp = new DemoApp();
        demoApp.init();
    });

    class DemoApp {
        constructor() {
            this.api = new ApiClient();
            this.formManager = null;
            this.mapManager = new MapManager();
            this.state = {
                compareMode: false,
                loading: false,
                connectionStrength: 'medium' // Default to medium until detected
            };
        }

        async init() {
            const form = document.getElementById('demo-form');
            if (!form) return;

            // Detect connection strength first
            await this.detectConnection();

            this.formManager = new FormManager(form);
            this.setupEventListeners();
            this.initializeResults();
        }

        setupEventListeners() {
            const form = document.getElementById('demo-form');
            const addUserBtn = document.getElementById('btn-add-user');
            const getTrailsBtn = document.getElementById('btn-get-trails');
            const removeUserBtns = document.querySelectorAll('.btn-remove-user');

            // Form submission
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.fetchResults();
            });

            // Add user button
            if (addUserBtn) {
                addUserBtn.addEventListener('click', () => this.addUser());
            }

            // Remove user buttons
            removeUserBtns.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const user = e.target.dataset.user;
                    this.removeUser(user);
                });
            });

            // Get trails button
            if (getTrailsBtn) {
                getTrailsBtn.addEventListener('click', () => this.fetchResults());
            }

            // Context info button clicks (using event delegation)
            document.addEventListener('click', (e) => {
                const infoBtn = e.target.closest('.context-info-btn');
                if (infoBtn) {
                    e.preventDefault();
                    const userId = infoBtn.dataset.user;
                    this.openContextModal(userId);
                    return;
                }

                // Close modal on backdrop or close button click
                const backdrop = e.target.closest('.context-modal__backdrop');
                const closeBtn = e.target.closest('.context-modal__close');
                if (backdrop || closeBtn) {
                    e.preventDefault();
                    const modal = backdrop ? backdrop.closest('.context-modal') : closeBtn.closest('.context-modal');
                    if (modal) {
                        this.closeContextModal(modal.id);
                    }
                }
            });

            // Close modal on Escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    const openModal = document.querySelector('.context-modal[aria-hidden="false"]');
                    if (openModal) {
                        this.closeContextModal(openModal.id);
                    }
                }
            });
        }

        openContextModal(userId) {
            const modal = document.getElementById(`context-modal-${userId}`);
            if (modal) {
                modal.setAttribute('aria-hidden', 'false');
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        }

        closeContextModal(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.setAttribute('aria-hidden', 'true');
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        }

        addUser() {
            const userBScenario = document.getElementById('user-scenario-b');
            const addUserBtn = document.getElementById('btn-add-user');
            const form = document.getElementById('demo-form');

            if (!userBScenario || userBScenario.classList.contains('hidden')) {
                // Show user B
                userBScenario.classList.remove('hidden');
                
                // Enable all user B fields
                const userBFields = userBScenario.querySelectorAll('input, select');
                userBFields.forEach(field => {
                    field.disabled = false;
                });

                // Copy user A values to user B
                this.copyUserValues('a', 'b');

                // Show remove button for user A
                const removeUserABtn = document.querySelector('[data-user="a"]');
                if (removeUserABtn) {
                    removeUserABtn.style.display = 'block';
                }

                // Hide add user button
                if (addUserBtn) {
                    addUserBtn.style.display = 'none';
                }

                this.state.compareMode = true;
                this.updateResultsLayout();
            }
        }

        removeUser(userToRemove) {
            const form = document.getElementById('demo-form');
            const userBScenario = document.getElementById('user-scenario-b');
            const addUserBtn = document.getElementById('btn-add-user');
            const removeUserABtn = document.querySelector('[data-user="a"]');

            if (userToRemove === 'b') {
                // Remove user B
                userBScenario.classList.add('hidden');
                
                // Disable all user B fields
                const userBFields = userBScenario.querySelectorAll('input, select');
                userBFields.forEach(field => {
                    field.disabled = true;
                });

                // Show add user button
                if (addUserBtn) {
                    addUserBtn.style.display = 'block';
                }

                // Hide remove button for user A
                if (removeUserABtn) {
                    removeUserABtn.style.display = 'none';
                }

                this.state.compareMode = false;
                this.updateResultsLayout();
            } else if (userToRemove === 'a') {
                // Move user B to user A position
                this.copyUserValues('b', 'a');
                this.removeUser('b');
            }

            // Fetch results after removing user
            this.fetchResults();
        }

        copyUserValues(fromPrefix, toPrefix) {
            const form = document.getElementById('demo-form');
            const fromInputs = form.querySelectorAll(`[name^="${fromPrefix}_"]`);
            
            fromInputs.forEach(fromInput => {
                const fieldName = fromInput.name.substring(2); // Remove prefix
                const toInput = form.querySelector(`[name="${toPrefix}_${fieldName}"]`);
                
                if (toInput) {
                    toInput.value = fromInput.value;
                }
            });

            // Copy user ID
            const fromUserSelect = form.querySelector(`[name="user_id_${fromPrefix}"]`);
            const toUserSelect = form.querySelector(`[name="user_id_${toPrefix}"]`);
            
            if (fromUserSelect && toUserSelect) {
                toUserSelect.value = fromUserSelect.value;
            }
        }

        async fetchResults() {
            const form = document.getElementById('demo-form');
            const getTrailsBtn = document.getElementById('btn-get-trails');
            const btnText = getTrailsBtn?.querySelector('.btn-text');
            const btnLoading = getTrailsBtn?.querySelector('.btn-loading');

            if (!form) return;

            // Show loading state
            this.state.loading = true;
            if (getTrailsBtn) {
                getTrailsBtn.disabled = true;
                if (btnText) btnText.classList.add('hidden');
                if (btnLoading) btnLoading.classList.remove('hidden');
            }

            // Check if user B is visible
            const userBScenario = document.getElementById('user-scenario-b');
            const isUserBVisible = userBScenario && !userBScenario.classList.contains('hidden');

            // Collect form data
            const params = new URLSearchParams();
            const allInputs = form.querySelectorAll('input, select');
            
            allInputs.forEach(input => {
                if (input.name && !input.disabled) {
                    // Only include b_ fields and user_id_b if user B is visible
                    if (input.name.startsWith('b_') || input.name === 'user_id_b') {
                        if (isUserBVisible) {
                            params.append(input.name, input.value);
                        }
                    } else {
                        // Always include a_ fields and user_id_a
                        params.append(input.name, input.value);
                    }
                }
            });

            try {
                const { data, error } = await this.api.getDemoResults(params);

                if (error) {
                    console.error('Error fetching results:', error);
                    this.showError(error);
                    return;
                }

                // Update results
                this.updateResults(data);

                // Update URL without reload
                const newUrl = new URL(window.location);
                params.forEach((value, key) => {
                    newUrl.searchParams.set(key, value);
                });
                window.history.pushState({}, '', newUrl);

            } catch (error) {
                console.error('Error fetching results:', error);
                this.showError(error.message);
            } finally {
                // Hide loading state
                this.state.loading = false;
                if (getTrailsBtn) {
                    getTrailsBtn.disabled = false;
                    if (btnText) btnText.classList.remove('hidden');
                    if (btnLoading) btnLoading.classList.add('hidden');
                }
            }
        }

        updateResults(data) {
            const resultsContainer = document.getElementById('demo-results');
            if (!resultsContainer || !data) return;

            // Clear existing results
            resultsContainer.innerHTML = '';

            // Update compare mode
            this.state.compareMode = data.compare_mode || false;
            this.updateResultsLayout();

            // Render primary result
            if (data.primary_result) {
                const panelA = this.renderResultPanel(data.primary_result, 'a', 'User A');
                resultsContainer.appendChild(panelA);
            }

            // Render secondary result if exists
            if (this.state.compareMode && data.secondary_result) {
                const panelB = this.renderResultPanel(data.secondary_result, 'b', 'User B');
                resultsContainer.appendChild(panelB);
            }

            // Initialize views after rendering
            setTimeout(() => {
                this.initializeViews();
            }, 100);
        }

        renderResultPanel(result, userId, userLabel) {
            const panel = document.createElement('div');
            panel.className = 'result-panel';
            panel.dataset.user = userId;

            // Format context for modal display
            const contextItems = this.formatContextForModal(result.context || {});

            const exactCount = (result.exact || []).length;
            const suggestionsCount = (result.suggestions || []).length;
            const isCompareMode = this.state.compareMode;

            // Determine default view based on connection strength
            const defaultView = this.getDefaultView();

            // Build view toggle buttons with connection-based default
            const viewToggleButtons = isCompareMode ? `
                <button type="button" class="view-toggle__button ${defaultView === 'map' ? 'active' : ''}" data-view="map" data-panel="${userId}">🗺️ Map</button>
                <button type="button" class="view-toggle__button ${defaultView === 'list' ? 'active' : ''}" data-view="list" data-panel="${userId}">📋 List</button>
            ` : `
                <button type="button" class="view-toggle__button ${defaultView === 'map' ? 'active' : ''}" data-view="map" data-panel="${userId}">🗺️ Map</button>
                <button type="button" class="view-toggle__button ${defaultView === 'list' ? 'active' : ''}" data-view="list" data-panel="${userId}">📋 List</button>
                <button type="button" class="view-toggle__button ${defaultView === 'cards' ? 'active' : ''}" data-view="cards" data-panel="${userId}">🃏 Cards</button>
            `;

            panel.innerHTML = `
                <div class="result-panel__header">
                    <div class="result-panel__title-wrapper">
                        <h2 class="result-panel__title">${result.scenario?.title || 'Custom Scenario'}</h2>
                        <button type="button" class="context-info-btn" aria-label="Show context information" data-user="${userId}">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5" fill="none"/>
                                <path d="M8 11V8M8 5H8.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <!-- Context Info Modal -->
                <div class="context-modal" id="context-modal-${userId}" role="dialog" aria-labelledby="context-modal-title-${userId}" aria-hidden="true">
                    <div class="context-modal__backdrop"></div>
                    <div class="context-modal__content">
                        <div class="context-modal__header">
                            <h3 class="context-modal__title" id="context-modal-title-${userId}">Search Context</h3>
                            <button type="button" class="context-modal__close" aria-label="Close modal">
                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                </svg>
                            </button>
                        </div>
                        <div class="context-modal__body">
                            <div class="context-modal__items">
                                ${contextItems}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="view-toggle">${viewToggleButtons}</div>
                <div class="view-sections" data-panel="${userId}">
                    ${this.renderMapView(result, userId, userLabel)}
                    ${this.renderListView(result, userId)}
                    ${!isCompareMode ? this.renderCardsView(result, userId) : ''}
                </div>
                <script type="application/json" class="trail-data" data-user="${userId}">
                    ${JSON.stringify({
                        exact: result.exact || [],
                        suggestions: result.suggestions || [],
                        user_label: userLabel,
                        user_id: userId
                    })}
                </script>
            `;

            return panel;
        }

        formatContextForModal(context) {
            const hiddenFields = ['hike_date', 'hike_start_date', 'hike_end_date'];
            return Object.entries(context)
                .filter(([key]) => !hiddenFields.includes(key))
                .map(([key, value]) => {
                    let displayValue = value;
                    let label = key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
                    
                    if (key === 'time_available') {
                        const totalMinutes = parseInt(value) || 0;
                        const days = Math.floor(totalMinutes / (24 * 60));
                        const hours = Math.floor((totalMinutes % (24 * 60)) / 60);
                        let timeText = '';
                        if (days > 0) timeText += `${days} day${days !== 1 ? 's' : ''}`;
                        if (hours > 0) {
                            if (days > 0) timeText += ' ';
                            timeText += `${hours} hour${hours !== 1 ? 's' : ''}`;
                        }
                        displayValue = timeText || '0 hours';
                    }
                    
                    return `
                        <div class="context-modal__item">
                            <span class="context-modal__label">${label}:</span>
                            <span class="context-modal__value">${displayValue}</span>
                        </div>
                    `;
                }).join('');
        }

        renderMapView(result, userId, userLabel) {
            const defaultView = this.getDefaultView();
            const isActive = defaultView === 'map';
            
            return `
                <div class="view-section ${isActive ? 'active' : ''}" data-view="map" data-panel="${userId}">
                    <div class="map-container">
                        <div class="map-canvas" id="demo-map-${userId}"></div>
                        <div class="map-legend">
                            <div class="map-legend__title">Trail Types</div>
                            <div class="map-legend__items">
                                <div class="map-legend__item">
                                    <span class="map-legend__marker" style="background-color: #5b8df9;"></span>
                                    <span class="map-legend__label">Recommended</span>
                                </div>
                                <div class="map-legend__item">
                                    <span class="map-legend__marker" style="background-color: #f59e0b;"></span>
                                    <span class="map-legend__label">Suggestions</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        renderListView(result, userId) {
            const defaultView = this.getDefaultView();
            const isActive = defaultView === 'list';
            const exactTrails = (result.exact || []).map(trail => this.renderTrailItem(trail, 'recommended')).join('');
            const suggestions = (result.suggestions || []).map(trail => this.renderTrailItem(trail, 'suggested')).join('');

            return `
                <div class="view-section ${isActive ? 'active' : ''}" data-view="list" data-panel="${userId}">
                    <div class="result-section">
                        <h3>🎯 Recommended (${(result.exact || []).length})</h3>
                        <div class="trail-list">${exactTrails || '<p class="empty-state">No direct matches</p>'}</div>
                    </div>
                    <div class="result-section">
                        <h3>✨ Suggestions (${(result.suggestions || []).length})</h3>
                        <div class="trail-list">${suggestions || '<p class="empty-state">No suggestions</p>'}</div>
                    </div>
                </div>
            `;
        }

        renderCardsView(result, userId) {
            const defaultView = this.getDefaultView();
            const isActive = defaultView === 'cards';
            const exactTrails = (result.exact || []).map(trail => this.renderTrailCard(trail, 'recommended')).join('');
            const suggestions = (result.suggestions || []).map(trail => this.renderTrailCard(trail, 'suggested')).join('');

            return `
                <div class="view-section ${isActive ? 'active' : ''}" data-view="cards" data-panel="${userId}">
                    <div class="result-section">
                        <h3>🎯 Recommended (${(result.exact || []).length})</h3>
                        <div class="trail-grid">${exactTrails || '<p class="empty-state">No direct matches</p>'}</div>
                    </div>
                    <div class="result-section">
                        <h3>✨ Suggestions (${(result.suggestions || []).length})</h3>
                        <div class="trail-grid">${suggestions || '<p class="empty-state">No suggestions</p>'}</div>
                    </div>
                </div>
            `;
        }

        renderTrailItem(trail, type) {
            const difficulty = trail.difficulty || 0;
            const difficultyClass = difficulty <= 3 ? 'easy' : difficulty <= 6 ? 'medium' : 'hard';
            const difficultyText = difficulty <= 3 ? 'Easy' : difficulty <= 6 ? 'Medium' : 'Hard';
            const relevance = type === 'suggested' ? `<span class="trail-item__relevance">${Math.round(trail.relevance_percentage || 0)}% match</span>` : '';
            
            // Truncate description if too long
            let description = trail.description || '';
            if (description && description.length > 120) {
                description = description.substring(0, 120) + '...';
            }
            
            // Format landscapes if available
            let landscapesHTML = '';
            if (trail.landscapes) {
                const landscapes = typeof trail.landscapes === 'string' 
                    ? trail.landscapes.split(',').map(l => l.trim())
                    : trail.landscapes;
                if (Array.isArray(landscapes) && landscapes.length > 0) {
                    landscapesHTML = `
                        <div class="trail-item__landscapes">
                            ${landscapes.slice(0, 3).map(landscape => 
                                `<span class="trail-item__landscape-tag">${landscape.trim().replace(/_/g, ' ')}</span>`
                            ).join('')}
                        </div>
                    `;
                }
            }

            return `
                <div class="trail-item ${type}">
                    <div class="trail-item__header">
                        <div class="trail-item__title-group">
                            <h4 class="trail-item__title">${trail.name || 'Unknown'}</h4>
                            ${relevance}
                        </div>
                        <span class="trail-item__difficulty difficulty-${difficultyClass}">${difficultyText}</span>
                    </div>
                    ${description ? `<p class="trail-item__description">${description}</p>` : ''}
                    ${landscapesHTML}
                    <div class="trail-item__stats">
                        <div class="trail-item__stat">
                            <span class="trail-item__stat-icon">📏</span>
                            <span class="trail-item__stat-label">Distance</span>
                            <span class="trail-item__stat-value">${trail.distance || '—'} km</span>
                        </div>
                        <div class="trail-item__stat">
                            <span class="trail-item__stat-icon">⏱</span>
                            <span class="trail-item__stat-label">Duration</span>
                            <span class="trail-item__stat-value">${Utils.formatDuration(trail.duration)}</span>
                        </div>
                        <div class="trail-item__stat">
                            <span class="trail-item__stat-icon">⛰</span>
                            <span class="trail-item__stat-label">Elevation</span>
                            <span class="trail-item__stat-value">${trail.elevation_gain || '—'} m</span>
                        </div>
                        ${trail.forecast_weather ? `
                        <div class="trail-item__stat">
                            <span class="trail-item__stat-icon">${this.getWeatherIcon(trail.forecast_weather)}</span>
                            <span class="trail-item__stat-label">Weather</span>
                            <span class="trail-item__stat-value">${trail.forecast_weather.charAt(0).toUpperCase() + trail.forecast_weather.slice(1).replace('_', ' ')}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        getWeatherIcon(weather) {
            const icons = {
                'sunny': '☀️',
                'cloudy': '☁️',
                'rainy': '🌧️',
                'snowy': '❄️',
                'storm_risk': '⛈️'
            };
            return icons[weather] || '🌤️';
        }

        renderTrailCard(trail, type) {
            const difficulty = trail.difficulty || 0;
            const difficultyClass = difficulty <= 3 ? 'easy' : difficulty <= 6 ? 'medium' : 'hard';
            const difficultyText = difficulty <= 3 ? 'Easy' : difficulty <= 6 ? 'Medium' : 'Hard';
            const relevance = type === 'suggested' ? `<span class="trail-card__relevance">${Math.round(trail.relevance_percentage || 0)}% match</span>` : '';

            // Truncate description if too long
            let description = trail.description || 'No description available';
            if (description && description.length > 150) {
                description = description.substring(0, 150) + '...';
            }

            // Format landscapes if available
            let landscapesHTML = '';
            if (trail.landscapes) {
                const landscapes = typeof trail.landscapes === 'string'
                    ? trail.landscapes.split(',').map(l => l.trim())
                    : trail.landscapes;
                if (Array.isArray(landscapes) && landscapes.length > 0) {
                    landscapesHTML = `
                        <div class="trail-card__landscapes">
                            ${landscapes.slice(0, 3).map(landscape =>
                                `<span class="trail-card__landscape-tag">${landscape.trim().replace(/_/g, ' ')}</span>`
                            ).join('')}
                        </div>
                    `;
                }
            }

            // Generate unique ID for minimap
            const mapId = `card-map-${trail.trail_id || Math.random().toString(36).substr(2, 9)}`;
            
            // Prepare coordinates for the minimap
            const coordinatesAttr = trail.coordinates ? `data-coordinates='${JSON.stringify(trail.coordinates)}'` : '';

            return `
                <div class="trail-card ${type}">
                    <div class="trail-card__map-container">
                        <div class="trail-card__mini-map" id="${mapId}" data-lat="${trail.latitude}" data-lng="${trail.longitude}" ${coordinatesAttr}></div>
                        ${relevance ? `<div class="trail-card__relevance-badge">${relevance}</div>` : ''}
                    </div>
                    <div class="trail-card__content">
                        <div class="trail-card__header">
                            <h3 class="trail-card__title">${trail.name || 'Unknown'}</h3>
                            <span class="trail-card__difficulty difficulty-${difficultyClass}">${difficultyText}</span>
                        </div>
                        <p class="trail-card__description">${description}</p>
                        ${landscapesHTML}
                        <div class="trail-card__stats">
                            <div class="trail-card__stat">
                                <span class="trail-card__stat-icon">📏</span>
                                <div class="trail-card__stat-info">
                                    <span class="trail-card__stat-label">Distance</span>
                                    <span class="trail-card__stat-value">${trail.distance || '—'} km</span>
                                </div>
                            </div>
                            <div class="trail-card__stat">
                                <span class="trail-card__stat-icon">⏱</span>
                                <div class="trail-card__stat-info">
                                    <span class="trail-card__stat-label">Duration</span>
                                    <span class="trail-card__stat-value">${Utils.formatDuration(trail.duration)}</span>
                                </div>
                            </div>
                            <div class="trail-card__stat">
                                <span class="trail-card__stat-icon">⛰</span>
                                <div class="trail-card__stat-info">
                                    <span class="trail-card__stat-label">Elevation</span>
                                    <span class="trail-card__stat-value">${trail.elevation_gain || '—'} m</span>
                                </div>
                            </div>
                            ${trail.forecast_weather ? `
                            <div class="trail-card__stat">
                                <span class="trail-card__stat-icon">${this.getWeatherIcon(trail.forecast_weather)}</span>
                                <div class="trail-card__stat-info">
                                    <span class="trail-card__stat-label">Weather</span>
                                    <span class="trail-card__stat-value">${trail.forecast_weather.charAt(0).toUpperCase() + trail.forecast_weather.slice(1).replace('_', ' ')}</span>
                                </div>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }

        initializeViews() {
            // Initialize view toggles
            document.querySelectorAll('.view-toggle__button').forEach(btn => {
                btn.addEventListener('click', () => {
                    const view = btn.dataset.view;
                    const panel = btn.dataset.panel;
                    this.switchView(panel, view);
                });
            });

            // Initialize maps for active map views
            document.querySelectorAll('.view-section[data-view="map"].active').forEach(section => {
                const panel = section.dataset.panel;
                const mapId = `demo-map-${panel}`;
                setTimeout(() => this.initializeMap(mapId, panel), 100);
            });

            // Initialize card minimaps for active cards views
            document.querySelectorAll('.view-section[data-view="cards"].active').forEach(section => {
                const panel = section.dataset.panel;
                setTimeout(() => this.initializeCardMinimaps(section), 100);
            });
        }

        switchView(panel, view) {
            // Select the view-sections container specifically, not just any element with data-panel
            const viewSectionsContainer = document.querySelector(`.view-sections[data-panel="${panel}"]`);
            
            if (!viewSectionsContainer) return;

            // Update buttons
            const buttons = viewSectionsContainer.closest('.result-panel').querySelectorAll('.view-toggle__button');
            
            buttons.forEach(btn => {
                if (btn.dataset.panel === panel && btn.dataset.view === view) {
                    btn.classList.add('active');
                } else if (btn.dataset.panel === panel) {
                    btn.classList.remove('active');
                }
            });

            // Update sections
            const sections = viewSectionsContainer.querySelectorAll('.view-section');
            
            sections.forEach(section => {
                if (section.dataset.view === view && section.dataset.panel === panel) {
                    section.classList.add('active');
                    section.classList.remove('hidden');

                    // Initialize map if switching to map view
                    if (view === 'map') {
                        const mapId = `demo-map-${panel}`;
                        setTimeout(() => this.initializeMap(mapId, panel), 100);
                    }

                    // Initialize card minimaps if switching to cards view
                    if (view === 'cards') {
                        setTimeout(() => this.initializeCardMinimaps(section), 100);
                    }
                } else if (section.dataset.panel === panel) {
                    section.classList.remove('active');
                    section.classList.add('hidden');
                }
            });
        }

        initializeMap(mapId, userId) {
            const mapContainer = document.getElementById(mapId);
            if (!mapContainer || typeof L === 'undefined') return;

            // Check if map already exists
            if (this.mapManager.maps.has(mapId)) {
                this.mapManager.invalidateSize(mapId);
                return;
            }

            const map = this.mapManager.initMap(mapId, {
                zoom: 8,
                center: [45.8, 6.5]
            });

            // Get trail data
            const dataScript = document.querySelector(`.trail-data[data-user="${userId}"]`);
            if (!dataScript) return;

            try {
                const trailData = JSON.parse(dataScript.textContent);
                const allTrails = [
                    ...(trailData.exact || []).map(t => ({ ...t, view_type: 'recommended' })),
                    ...(trailData.suggestions || []).map(t => ({ ...t, view_type: 'suggested' }))
                ];

                this.mapManager.addTrailMarkers(map, allTrails);
            } catch (e) {
                console.error('Failed to parse trail data:', e);
            }
        }

        initializeCardMinimaps(cardsSection) {
            if (typeof L === 'undefined') return;

            // Find all minimaps in this cards section
            const minimaps = cardsSection.querySelectorAll('.trail-card__mini-map');
            
            minimaps.forEach((minimapDiv, index) => {
                const mapId = minimapDiv.id;
                const lat = parseFloat(minimapDiv.dataset.lat);
                const lng = parseFloat(minimapDiv.dataset.lng);
                const coordinatesStr = minimapDiv.dataset.coordinates;

                // Skip if coordinates are invalid or map already exists
                if (!lat || !lng || this.mapManager.maps.has(mapId)) {
                    if (this.mapManager.maps.has(mapId)) {
                        this.mapManager.invalidateSize(mapId);
                    }
                    return;
                }

                // Initialize minimap
                const minimap = this.mapManager.initMap(mapId, {
                    zoom: 12,
                    center: [lat, lng],
                    scrollWheelZoom: false,
                    dragging: false,
                    zoomControl: false,
                    attributionControl: false
                });

                if (minimap) {
                    // Force map to recalculate size after it's rendered
                    setTimeout(() => minimap.invalidateSize(), 50);
                    // Try to parse and draw the trail coordinates if available
                    
                    if (coordinatesStr) {
                        try {
                            const parsed = JSON.parse(coordinatesStr);
                            // The coordinates might be wrapped in an object with a 'coordinates' key
                            const coordinates = parsed.coordinates || parsed;
                            
                            if (Array.isArray(coordinates) && coordinates.length > 0) {
                                // Draw the trail path
                                const polyline = L.polyline(coordinates, {
                                    color: '#5b8df9',
                                    weight: 3,
                                    opacity: 0.8
                                }).addTo(minimap);
                                
                                // Fit the map to show the entire trail
                                minimap.fitBounds(polyline.getBounds(), { padding: [10, 10] });
                            } else {
                                // Fall back to marker
                                L.marker([lat, lng], {
                                    icon: L.divIcon({
                                        className: 'trail-marker',
                                        html: '<div class="trail-marker__pin"></div>',
                                        iconSize: [24, 24],
                                        iconAnchor: [12, 24]
                                    })
                                }).addTo(minimap);
                            }
                        } catch (e) {
                            // If parsing fails, fall back to a single marker
                            L.marker([lat, lng], {
                                icon: L.divIcon({
                                    className: 'trail-marker',
                                    html: '<div class="trail-marker__pin"></div>',
                                    iconSize: [24, 24],
                                    iconAnchor: [12, 24]
                                })
                            }).addTo(minimap);
                        }
                    } else {
                        // No coordinates available, use a marker
                        L.marker([lat, lng], {
                            icon: L.divIcon({
                                className: 'trail-marker',
                                html: '<div class="trail-marker__pin"></div>',
                                iconSize: [24, 24],
                                iconAnchor: [12, 24]
                            })
                        }).addTo(minimap);
                    }
                }
            });
        }

        initializeResults() {
            // Initialize results if they exist on page load
            const resultsContainer = document.getElementById('demo-results');
            if (resultsContainer && resultsContainer.children.length > 0) {
                this.initializeViews();
            }
        }

        updateResultsLayout() {
            const resultsContainer = document.getElementById('demo-results');
            if (resultsContainer) {
                if (this.state.compareMode) {
                    resultsContainer.classList.add('compare');
                } else {
                    resultsContainer.classList.remove('compare');
                }
            }
        }

        showError(message) {
            // Simple error display - can be enhanced
            console.error('Error:', message);
            alert(`Error: ${message}`);
        }

        /**
         * Detect connection strength using Network Information API and fallback methods
         * @returns {Promise<string>} Connection strength: 'weak', 'medium', or 'strong'
         */
        async detectConnection() {
            try {
                // Check if navigator.connection is available (Network Information API)
                if ('connection' in navigator) {
                    const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
                    
                    if (conn && conn.effectiveType) {
                        const effectiveType = conn.effectiveType;
                        console.log('Network effectiveType:', effectiveType);
                        
                        // Map effectiveType to our connection strength levels
                        if (effectiveType === 'slow-2g' || effectiveType === '2g') {
                            this.state.connectionStrength = 'weak';
                            console.log('Connection detected: weak (2g)');
                            this.updateConnectionIndicator('weak');
                            return 'weak';
                        } else if (effectiveType === '3g') {
                            this.state.connectionStrength = 'medium';
                            console.log('Connection detected: medium (3g)');
                            this.updateConnectionIndicator('medium');
                            return 'medium';
                        } else if (effectiveType === '4g') {
                            // For 4g, test actual speed to determine if medium or strong
                            const isFast = await this.testConnectionSpeed();
                            this.state.connectionStrength = isFast ? 'strong' : 'medium';
                            console.log('Connection detected:', isFast ? 'strong (fast 4g)' : 'medium (slow 4g)');
                            this.updateConnectionIndicator(this.state.connectionStrength);
                            return this.state.connectionStrength;
                        } else {
                            // Unknown or very fast connection (e.g., 5g, wifi)
                            this.state.connectionStrength = 'strong';
                            console.log('Connection detected: strong (fast network)');
                            this.updateConnectionIndicator('strong');
                            return 'strong';
                        }
                    }
                }
                
                // Fallback: test connection speed with a small download
                const isFast = await this.testConnectionSpeed();
                this.state.connectionStrength = isFast ? 'strong' : 'medium';
                console.log('Connection detected (fallback):', this.state.connectionStrength);
                this.updateConnectionIndicator(this.state.connectionStrength);
                return this.state.connectionStrength;
            } catch (error) {
                console.warn('Error detecting connection, defaulting to medium:', error);
                this.state.connectionStrength = 'medium';
                this.updateConnectionIndicator('medium');
                return 'medium';
            }
        }

        /**
         * Test connection speed by downloading a small resource
         * @returns {Promise<boolean>} True if connection is fast, false otherwise
         */
        async testConnectionSpeed() {
            try {
                const startTime = performance.now();
                // Try to fetch a small resource from the server
                const response = await fetch('/static/style.css?t=' + Date.now(), { 
                    method: 'HEAD',
                    cache: 'no-cache'
                });
                const endTime = performance.now();
                const duration = endTime - startTime;
                
                // If the HEAD request takes more than 500ms, consider it slow
                const isFast = duration < 500;
                console.log(`Connection speed test: ${duration.toFixed(0)}ms (${isFast ? 'fast' : 'slow'})`);
                return isFast;
            } catch (error) {
                console.warn('Connection speed test failed, assuming slow connection:', error);
                // If fetch fails, assume weak connection
                return false;
            }
        }

        /**
         * Get the default view based on connection strength
         * @returns {string} View type: 'list', 'cards', or 'map'
         */
        getDefaultView() {
            const strength = this.state.connectionStrength;
            
            // Adaptive view selection:
            // - weak connection: list view (lightweight, no maps)
            // - medium connection: cards view (some graphics, mini maps optional)
            // - strong connection: map view (full interactive map)
            if (strength === 'weak') {
                console.log('Default view: list (weak connection)');
                return 'list';
            } else if (strength === 'medium') {
                console.log('Default view: cards (medium connection)');
                return 'cards';
            } else {
                console.log('Default view: map (strong connection)');
                return 'map';
            }
        }

        /**
         * Update the connection indicator UI
         * @param {string} strength Connection strength: 'weak', 'medium', or 'strong'
         */
        updateConnectionIndicator(strength) {
            const indicator = document.getElementById('connection-indicator');
            const icon = document.getElementById('connection-icon');
            const text = document.getElementById('connection-text');
            
            if (!indicator || !icon || !text) return;
            
            // Update icon and text based on strength
            const config = {
                weak: {
                    icon: '📶',
                    text: 'Weak connection - Using list view',
                    color: 'rgba(239, 68, 68, 0.15)' // Red tint
                },
                medium: {
                    icon: '📶',
                    text: 'Medium connection - Using card view',
                    color: 'rgba(245, 158, 11, 0.15)' // Orange tint
                },
                strong: {
                    icon: '📶',
                    text: 'Strong connection - Using map view',
                    color: 'rgba(34, 197, 94, 0.15)' // Green tint
                }
            };
            
            const settings = config[strength] || config.medium;
            icon.textContent = settings.icon;
            text.textContent = settings.text;
            indicator.style.background = settings.color;
        }
    }
})();
