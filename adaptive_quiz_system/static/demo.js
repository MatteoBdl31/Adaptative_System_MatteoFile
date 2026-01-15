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
                loading: false
            };
        }

        init() {
            const form = document.getElementById('demo-form');
            if (!form) return;

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

            // Update profile display when user selection changes
            const userSelectA = document.getElementById('user-select-a');
            const userSelectB = document.getElementById('user-select-b');
            
            if (userSelectA) {
                userSelectA.addEventListener('change', () => this.updateProfileDisplay('a'));
            }
            
            if (userSelectB) {
                userSelectB.addEventListener('change', () => this.updateProfileDisplay('b'));
            }
        }

        updateProfileDisplay(userIndex) {
            const select = document.getElementById(`user-select-${userIndex}`);
            const badge = document.getElementById(`profile-badge-${userIndex}`);
            const nameSpan = document.getElementById(`profile-name-${userIndex}`);
            
            if (!select || !badge || !nameSpan) return;
            
            const selectedOption = select.options[select.selectedIndex];
            const profileName = selectedOption.getAttribute('data-profile-name');
            
            if (profileName) {
                nameSpan.textContent = profileName;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
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
                
                // Update profile display for user B
                this.updateProfileDisplay('b');

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
                // Update profile display for the target user
                this.updateProfileDisplay(toPrefix);
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

            const contextPills = Object.entries(result.context || {}).map(([key, value]) => {
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
                    return `<span class="context-pill">Time: <strong>${timeText || '0 hours'}</strong></span>`;
                }
                return `<span class="context-pill">${key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}: <strong>${value}</strong></span>`;
            }).join('');

            const exactCount = (result.exact || []).length;
            const suggestionsCount = (result.suggestions || []).length;
            const isCompareMode = this.state.compareMode;

            // Build view toggle buttons
            const viewToggleButtons = isCompareMode ? `
                <button type="button" class="view-toggle__button active" data-view="map" data-panel="${userId}">🗺️ Map</button>
                <button type="button" class="view-toggle__button" data-view="list" data-panel="${userId}">📋 List</button>
            ` : `
                <button type="button" class="view-toggle__button active" data-view="map" data-panel="${userId}">🗺️ Map</button>
                <button type="button" class="view-toggle__button" data-view="list" data-panel="${userId}">📋 List</button>
                <button type="button" class="view-toggle__button" data-view="cards" data-panel="${userId}">🃏 Cards</button>
            `;

            panel.innerHTML = `
                <div class="result-panel__header">
                    <h2 class="result-panel__title">${result.scenario?.title || 'Custom Scenario'}</h2>
                    <p class="result-panel__description">${result.scenario?.description || 'User-defined context'}</p>
                </div>
                <div class="context-pills">${contextPills}</div>
                <div class="view-toggle">${viewToggleButtons}</div>
                <div class="view-sections" data-panel="${userId}">
                    ${this.renderMapView(result, userId, userLabel)}
                    ${this.renderListView(result)}
                    ${!isCompareMode ? this.renderCardsView(result) : ''}
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

        renderMapView(result, userId, userLabel) {
            return `
                <div class="view-section active" data-view="map" data-panel="${userId}">
                    <div class="map-container">
                        <div class="map-canvas" id="demo-map-${userId}"></div>
                    </div>
                </div>
            `;
        }

        renderListView(result) {
            const exactTrails = (result.exact || []).map(trail => this.renderTrailItem(trail, 'recommended')).join('');
            const suggestions = (result.suggestions || []).map(trail => this.renderTrailItem(trail, 'suggested')).join('');

            return `
                <div class="view-section" data-view="list">
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

        renderCardsView(result) {
            const exactTrails = (result.exact || []).map(trail => this.renderTrailCard(trail, 'recommended')).join('');
            const suggestions = (result.suggestions || []).map(trail => this.renderTrailCard(trail, 'suggested')).join('');

            return `
                <div class="view-section" data-view="cards">
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

            return `
                <div class="trail-item ${type}">
                    <div class="trail-item__header">
                        <h4>${trail.name || 'Unknown'}</h4>
                        <span class="pill">${difficultyText}</span>
                    </div>
                    <div class="trail-stats">
                        <span>${trail.distance || '—'} km</span>
                        <span>${Utils.formatDuration(trail.duration)}</span>
                        <span>${trail.elevation_gain || '—'} m</span>
                    </div>
                </div>
            `;
        }

        renderTrailCard(trail, type) {
            const difficulty = trail.difficulty || 0;
            const difficultyClass = difficulty <= 3 ? 'easy' : difficulty <= 6 ? 'medium' : 'hard';
            const difficultyText = difficulty <= 3 ? 'Easy' : difficulty <= 6 ? 'Medium' : 'Hard';
            const relevance = type === 'suggested' ? `<span class="badge">${Math.round(trail.relevance_percentage || 0)}% match</span>` : '';

            return `
                <div class="trail-card ${type}">
                    <div class="trail-card__header">
                        <h3 class="trail-card__title">${trail.name || 'Unknown'}</h3>
                        ${relevance}
                    </div>
                    <p class="trail-card__description">${trail.description || 'No description'}</p>
                    <div class="trail-card__stats">
                        <span>📏 ${trail.distance || '—'} km</span>
                        <span>⏱ ${Utils.formatDuration(trail.duration)}</span>
                        <span>⛰ ${trail.elevation_gain || '—'} m</span>
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
        }

        switchView(panel, view) {
            const panelElement = document.querySelector(`[data-panel="${panel}"]`);
            if (!panelElement) return;

            // Update buttons
            panelElement.closest('.result-panel').querySelectorAll('.view-toggle__button').forEach(btn => {
                if (btn.dataset.panel === panel && btn.dataset.view === view) {
                    btn.classList.add('active');
                } else if (btn.dataset.panel === panel) {
                    btn.classList.remove('active');
                }
            });

            // Update sections
            panelElement.querySelectorAll('.view-section').forEach(section => {
                if (section.dataset.view === view && section.dataset.panel === panel) {
                    section.classList.add('active');
                    section.classList.remove('hidden');

                    // Initialize map if switching to map view
                    if (view === 'map') {
                        const mapId = `demo-map-${panel}`;
                        setTimeout(() => this.initializeMap(mapId, panel), 100);
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
    }
})();
