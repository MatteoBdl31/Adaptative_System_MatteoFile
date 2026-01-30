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
            this.setupDateInputs();

        }

        setupDateInputs() {
            // Replace all date inputs with custom DD/MM/YYYY inputs
            this.replaceDateInputs();
            
            // Use MutationObserver to handle dynamically added date inputs
            const observer = new MutationObserver(() => {
                this.replaceDateInputs();
            });
            
            const form = document.getElementById('demo-form');
            if (form) {
                observer.observe(form, { childList: true, subtree: true });
            }
        }

        replaceDateInputs() {
            const dateInputs = document.querySelectorAll('input[type="date"]');
            dateInputs.forEach(input => {
                // Skip if already replaced
                if (input.dataset.replaced === 'true') {
                    return;
                }
                
                // Mark as replaced
                input.dataset.replaced = 'true';
                
                // Create a text input that displays DD/MM/YYYY
                const textInput = document.createElement('input');
                textInput.type = 'text';
                textInput.className = input.className;
                textInput.name = input.name + '_display';
                textInput.placeholder = 'DD/MM/YYYY';
                textInput.style.cssText = input.style.cssText || '';
                
                // Convert YYYY-MM-DD to DD/MM/YYYY for display
                if (input.value) {
                    const [year, month, day] = input.value.split('-');
                    if (year && month && day) {
                        textInput.value = `${day}/${month}/${year}`;
                    }
                }
                
                // Hide the original date input but keep it for form submission
                input.style.position = 'absolute';
                input.style.opacity = '0';
                input.style.width = '1px';
                input.style.height = '1px';
                input.style.pointerEvents = 'none';
                
                // Create a wrapper div for the input group
                const wrapper = document.createElement('div');
                wrapper.style.position = 'relative';
                wrapper.style.display = 'flex';
                wrapper.style.alignItems = 'center';
                wrapper.style.gap = '8px';
                wrapper.style.width = '100%';
                
                // Create calendar button
                const calendarBtn = document.createElement('button');
                calendarBtn.type = 'button';
                calendarBtn.innerHTML = '📅';
                calendarBtn.style.cssText = 'background: none; border: 1px solid var(--color-border); border-radius: 4px; padding: 8px 12px; cursor: pointer; font-size: 1.2em; flex-shrink: 0;';
                calendarBtn.title = 'Open calendar';
                calendarBtn.addEventListener('click', () => {
                    input.showPicker?.();
                });
                
                // Insert wrapper before input
                input.parentNode.insertBefore(wrapper, input);
                
                // Move inputs into wrapper
                wrapper.appendChild(textInput);
                wrapper.appendChild(calendarBtn);
                wrapper.appendChild(input);
                
                // Make text input take available space
                textInput.style.flex = '1';
                
                // Handle text input changes - convert DD/MM/YYYY to YYYY-MM-DD
                textInput.addEventListener('input', (e) => {
                    const value = e.target.value.replace(/\D/g, ''); // Remove non-digits
                    if (value.length <= 8) {
                        // Format as DD/MM/YYYY
                        let formatted = value;
                        if (value.length > 2) {
                            formatted = value.substring(0, 2) + '/' + value.substring(2);
                        }
                        if (value.length > 4) {
                            formatted = value.substring(0, 2) + '/' + value.substring(2, 4) + '/' + value.substring(4);
                        }
                        e.target.value = formatted;
                        
                        // Update hidden date input if valid
                        if (value.length === 8) {
                            const day = value.substring(0, 2);
                            const month = value.substring(2, 4);
                            const year = value.substring(4, 8);
                            
                            // Validate date
                            if (this.isValidDate(day, month, year)) {
                                input.value = `${year}-${month}-${day}`;
                                // Trigger change event on original input for other listeners
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        }
                    }
                });
                
                // Handle blur - validate and format
                textInput.addEventListener('blur', () => {
                    const value = textInput.value.replace(/\D/g, '');
                    if (value.length === 8) {
                        const day = value.substring(0, 2);
                        const month = value.substring(2, 4);
                        const year = value.substring(4, 8);
                        
                        if (this.isValidDate(day, month, year)) {
                            input.value = `${year}-${month}-${day}`;
                            textInput.value = `${day}/${month}/${year}`;
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                        } else {
                            // Invalid date, revert to original
                            if (input.value) {
                                const [y, m, d] = input.value.split('-');
                                textInput.value = `${d}/${m}/${y}`;
                            } else {
                                textInput.value = '';
                            }
                        }
                    } else if (value.length > 0 && value.length < 8) {
                        // Incomplete date, clear if not valid
                        textInput.value = '';
                        input.value = '';
                    }
                });
                
                // Sync when date input changes (from other sources)
                input.addEventListener('change', () => {
                    if (input.value) {
                        const [year, month, day] = input.value.split('-');
                        if (year && month && day) {
                            textInput.value = `${day}/${month}/${year}`;
                        }
                    } else {
                        textInput.value = '';
                    }
                });
            });
        }

        isValidDate(day, month, year) {
            const d = parseInt(day, 10);
            const m = parseInt(month, 10);
            const y = parseInt(year, 10);
            
            if (d < 1 || d > 31 || m < 1 || m > 12 || y < 1900 || y > 2100) {
                return false;
            }
            
            const date = new Date(y, m - 1, d);
            return date.getDate() === d && date.getMonth() === m - 1 && date.getFullYear() === y;
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

            // Context info, view toggle, and other delegated clicks
            document.addEventListener('click', (e) => {
                // View toggle (List / Map / Cards) for server-rendered demo panels
                const viewToggleBtn = e.target.closest('.view-toggle-btn');
                if (viewToggleBtn) {
                    e.preventDefault();
                    const view = viewToggleBtn.dataset.view;
                    const panel = viewToggleBtn.closest('.demo-panel, .result-panel');
                    if (panel && view) {
                        const viewSections = panel.querySelector('.demo-results[data-panel-id], .view-sections');
                        if (viewSections) {
                            viewSections.querySelectorAll('.demo-view-section, .view-section').forEach((section) => {
                                if (section.dataset.view === view) {
                                    section.classList.add('active');
                                    section.classList.remove('hidden');
                                } else {
                                    section.classList.remove('active');
                                    section.classList.add('hidden');
                                }
                            });
                            panel.querySelectorAll('.view-toggle-btn, .view-toggle__button').forEach((b) => {
                                b.classList.toggle('active', b === viewToggleBtn);
                            });
                        }
                    }
                    return;
                }

                const infoBtn = e.target.closest('.context-info-btn');
                if (infoBtn) {
                    e.preventDefault();
                    // Try to get user ID from button, or from parent panel
                    let userId = infoBtn.dataset.user || infoBtn.dataset.userIdx;
                    if (!userId) {
                        const panel = infoBtn.closest('.result-panel, .demo-panel');
                        userId = panel?.dataset.user || 'a';
                    }
                    this.openContextModal(userId);
                    return;
                }

                // Tab switching
                const tab = e.target.closest('.context-modal__tab');
                if (tab) {
                    e.preventDefault();
                    const modal = tab.closest('.context-modal');
                    if (modal) {
                        this.switchTab(modal, tab.dataset.tab);
                    }
                    return;
                }

                // Trail explanation button clicks
                const trailExplanationBtn = e.target.closest('.trail-explanation-btn');
                if (trailExplanationBtn) {
                    e.preventDefault();
                    const trailId = trailExplanationBtn.dataset.trailId;
                    const userId = trailExplanationBtn.dataset.userIdx || 
                                 trailExplanationBtn.dataset.userId ||
                                 trailExplanationBtn.closest('.result-panel, .demo-panel')?.dataset.user || 
                                 'a';
                    this.toggleTrailExplanation(trailId, userId, trailExplanationBtn);
                    return;
                }

                // Save Trail button (demo list/cards)
                const saveTrailBtn = e.target.closest('.btn-save-trail-demo');
                if (saveTrailBtn) {
                    e.preventDefault();
                    const trailId = saveTrailBtn.dataset.trailId;
                    const userId = saveTrailBtn.dataset.userId;
                    if (!userId || !trailId) return;
                    fetch(`/api/profile/${userId}/trails/save`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ trail_id: trailId })
                    })
                        .then(r => r.json())
                        .then(d => {
                            if (d.success) {
                                saveTrailBtn.textContent = 'Saved!';
                                saveTrailBtn.disabled = true;
                                if (typeof window.showToast === 'function') window.showToast('Trail added to My Trails successfully.', 3500, { linkUrl: '/profile/' + userId + '/trail/' + trailId, linkText: 'View trail' });
                            } else {
                                saveTrailBtn.textContent = 'Already saved';
                                saveTrailBtn.disabled = true;
                            }
                        })
                        .catch(() => { saveTrailBtn.textContent = 'Error'; });
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

            // Update profile display when user selection changes
            const userSelectA = document.getElementById('user-select-a');
            const userSelectB = document.getElementById('user-select-b');
            
            if (userSelectA) {
                userSelectA.addEventListener('change', () => {
                    this.updateProfileDisplay('a');
                    this.updateProfileLink('a');
                });
            }
            
            if (userSelectB) {
                userSelectB.addEventListener('change', () => {
                    this.updateProfileDisplay('b');
                    this.updateProfileLink('b');
                });
            }
            
            // Initial update of profile links
            this.updateProfileLink('a');
            if (userSelectB && !userSelectB.disabled) {
                this.updateProfileLink('b');
            }
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

        switchTab(modal, tabName) {
            // Update tab buttons
            const tabs = modal.querySelectorAll('.context-modal__tab');
            tabs.forEach(tab => {
                if (tab.dataset.tab === tabName) {
                    tab.classList.add('active');
                } else {
                    tab.classList.remove('active');
                }
            });

            // Update tab content
            const contents = modal.querySelectorAll('.context-modal__tab-content');
            contents.forEach(content => {
                if (content.dataset.content === tabName) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });

            // If switching to explanation tab, fetch explanation
            if (tabName === 'explanation') {
                const userId = modal.id.replace('context-modal-', '');
                this.fetchGeneralExplanation(userId, modal);
            }
        }

        async fetchGeneralExplanation(userId, modal) {
            // Find the appropriate loading/loaded/error divs (handle both idx and userId patterns)
            const loadedDiv = modal.querySelector(`#explanation-loaded-${userId}`) || 
                            modal.querySelector('#explanation-loaded-idx');
            const loadingDiv = modal.querySelector(`#explanation-loading-${userId}`) || 
                             modal.querySelector('#explanation-loading-idx');
            const errorDiv = modal.querySelector(`#explanation-error-${userId}`) || 
                           modal.querySelector('#explanation-error-idx');
            
            if (loadedDiv && loadedDiv.style.display !== 'none') {
                // Already loaded, don't fetch again
                return;
            }

            // Show loading state
            if (loadingDiv) loadingDiv.style.display = 'block';
            if (loadedDiv) loadedDiv.style.display = 'none';
            if (errorDiv) errorDiv.style.display = 'none';

            try {
                // Build context from current form or URL params
                const context = this.buildContextFromRequest();
                
                // Get user_id from form or URL params
                const params = new URLSearchParams(window.location.search);
                const form = document.getElementById('demo-form');
                const userSelect = form?.querySelector(`#user-select-${userId}`);
                const user_id = userSelect?.value || params.get(`user_id_${userId}`) || params.get('user_id_a') || '';
                
                // Add user_id to context
                if (user_id) {
                    context[`user_id_${userId}`] = user_id;
                }
                
                const queryString = new URLSearchParams(context).toString();
                
                const response = await fetch(`/api/explanations/general/${userId}?${queryString}`);
                const data = await response.json();

                if (data.explanation_text) {
                    // Display explanation
                    const textEl = modal.querySelector(`#explanation-text-${userId}`) || 
                                 modal.querySelector('#explanation-text-idx');
                    const factorsEl = modal.querySelector(`#explanation-factors-${userId}`) || 
                                    modal.querySelector('#explanation-factors-idx');
                    
                    if (textEl) {
                        textEl.textContent = data.explanation_text;
                    }
                    
                    if (factorsEl && data.key_factors) {
                        factorsEl.innerHTML = '';
                        data.key_factors.forEach(factor => {
                            const li = document.createElement('li');
                            li.textContent = factor;
                            factorsEl.appendChild(li);
                        });
                    }

                    // Show loaded content
                    if (loadingDiv) loadingDiv.style.display = 'none';
                    if (loadedDiv) loadedDiv.style.display = 'block';
                } else {
                    throw new Error('Invalid response format');
                }
            } catch (error) {
                console.error('Error fetching general explanation:', error);
                // Show error state
                if (loadingDiv) loadingDiv.style.display = 'none';
                if (errorDiv) errorDiv.style.display = 'block';
            }
        }

        buildContextFromRequest() {
            // Build context from current URL params or form
            const params = new URLSearchParams(window.location.search);
            const context = {};
            
            // Extract context parameters
            const contextKeys = ['time_available_days', 'time_available_hours', 'device', 'weather', 
                               'connection', 'season', 'hike_start_date', 'hike_end_date'];
            
            contextKeys.forEach(key => {
                const value = params.get(`a_${key}`) || params.get(key);
                if (value) {
                    context[key] = value;
                }
            });

            return context;
        }

        async toggleTrailExplanation(trailId, userId, button) {
            // Find the explanation content div
            const explanationDiv = document.getElementById(`trail-explanation-${trailId}`);
            if (!explanationDiv) return;

            const loadingDiv = explanationDiv.querySelector('.trail-explanation-loading');
            const loadedDiv = explanationDiv.querySelector('.trail-explanation-loaded');
            const textEl = loadedDiv?.querySelector('.trail-explanation-text');
            const factorsEl = loadedDiv?.querySelector('.trail-explanation-factors');

            // Get userId from button or parent panel if not provided
            if (!userId || userId === 'idx') {
                const panel = button.closest('.result-panel, .demo-panel');
                userId = panel?.dataset.user || button.dataset.userIdx || 'a';
            }

            // Toggle visibility
            if (explanationDiv.style.display === 'none' || !explanationDiv.style.display) {
                // Show and fetch explanation
                explanationDiv.style.display = 'block';
                
                // Check if already loaded
                if (loadedDiv && loadedDiv.style.display !== 'none' && textEl?.textContent) {
                    return; // Already loaded
                }

                // Show loading
                if (loadingDiv) loadingDiv.style.display = 'block';
                if (loadedDiv) loadedDiv.style.display = 'none';
                button.classList.add('loading');

                try {
                    const context = this.buildContextFromRequest();
                    
                    // Get user_id from form or URL params
                    const params = new URLSearchParams(window.location.search);
                    const form = document.getElementById('demo-form');
                    const userSelect = form?.querySelector(`#user-select-${userId}`);
                    const user_id = userSelect?.value || params.get(`user_id_${userId}`) || params.get('user_id_a') || '';
                    
                    // Add user_id to context
                    if (user_id) {
                        context[`user_id_${userId}`] = user_id;
                    }
                    
                    const queryString = new URLSearchParams(context).toString();
                    
                    const response = await fetch(`/api/explanations/trail/${userId}/${trailId}?${queryString}`);
                    const data = await response.json();

                    if (data.explanation_text) {
                        // Display explanation
                        if (textEl) {
                            textEl.textContent = data.explanation_text;
                        }
                        
                        if (factorsEl && data.key_factors) {
                            factorsEl.innerHTML = '';
                            data.key_factors.forEach(factor => {
                                const li = document.createElement('li');
                                li.textContent = '• ' + factor;
                                li.style.padding = 'var(--space-xs) 0';
                                li.style.color = 'var(--color-text)';
                                li.style.fontSize = 'var(--font-size-sm)';
                                factorsEl.appendChild(li);
                            });
                        }

                        // Show loaded content
                        if (loadingDiv) loadingDiv.style.display = 'none';
                        if (loadedDiv) loadedDiv.style.display = 'block';
                    } else {
                        throw new Error('Invalid response format');
                    }
                } catch (error) {
                    console.error('Error fetching trail explanation:', error);
                    // Show error message
                    if (loadingDiv) {
                        loadingDiv.textContent = 'Unable to load explanation. Please try again.';
                    }
                } finally {
                    button.classList.remove('loading');
                }
            } else {
                // Hide explanation and remove focus so the green circle outline disappears
                explanationDiv.style.display = 'none';
                if (button && typeof button.blur === 'function') {
                    button.blur();
                }
            }
        }

        async fetchTrailExplanation(userId, trailId, context) {
            try {
                const queryString = new URLSearchParams(context).toString();
                const response = await fetch(`/api/explanations/trail/${userId}/${trailId}?${queryString}`);
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Error fetching trail explanation:', error);
                return null;
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

        updateProfileLink(userIndex) {
            const select = document.getElementById(`user-select-${userIndex}`);
            const userScenario = document.querySelector(`[data-user-index="${userIndex}"]`);
            
            if (!select || !userScenario) return;
            
            const selectedUserId = select.value;
            const profileLink = userScenario.querySelector('a[href*="/profile/"]');
            
            if (profileLink && selectedUserId) {
                profileLink.href = `/profile/${selectedUserId}`;
                profileLink.style.display = 'inline-flex';
            } else if (profileLink) {
                profileLink.style.display = 'none';
            }
            
            // Also update header profile and my-trails links if this is user A (primary user)
            if (userIndex === 'a' && selectedUserId) {
                const headerProfileLink = document.getElementById('header-profile-link');
                if (headerProfileLink) headerProfileLink.href = `/profile/${selectedUserId}`;
                const headerMyTrailsLink = document.getElementById('header-my-trails-link');
                if (headerMyTrailsLink) headerMyTrailsLink.href = `/profile/${selectedUserId}/my-trails`;
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
                this.updateProfileLink('b');

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
                
                // Replace date inputs for newly added user B
                this.replaceDateInputs();
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
                    // Skip display inputs (they have _display suffix)
                    if (input.name.endsWith('_display')) {
                        return;
                    }
                    
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

            // Determine default view based on connection strength from form/search context
            // Use connection from result context, fallback to detected connection
            const connectionFromContext = (result.context || {}).connection || this.state.connectionStrength;
            const defaultView = this.getDefaultView(connectionFromContext);

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
                <div class="result-panel__content">
                    <div class="result-panel__header">
                        <div class="result-panel__title-wrapper">
                            <h2 class="result-panel__title">${result.scenario?.title || 'Custom Scenario'}</h2>
                            <button type="button" class="context-info-btn" aria-label="Show context information and recommendations" data-user="${userId}">
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5" fill="none"/>
                                    <path d="M8 11V8M8 5H8.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div class="view-toggle">${viewToggleButtons}</div>
                    <div class="view-sections" data-panel="${userId}">
                        ${this.renderMapView(result, userId, userLabel, defaultView)}
                        ${this.renderListView(result, userId, defaultView)}
                        ${!isCompareMode ? this.renderCardsView(result, userId, defaultView) : ''}
                    </div>
                </div>
                <div class="context-modal" id="context-modal-${userId}" role="dialog" aria-labelledby="context-modal-title-${userId}" aria-hidden="true">
                    <div class="context-modal__backdrop"></div>
                    <div class="context-modal__content">
                        <div class="context-modal__header">
                            <h3 class="context-modal__title" id="context-modal-title-${userId}">Information</h3>
                            <button type="button" class="context-modal__close" aria-label="Close modal">
                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                </svg>
                            </button>
                        </div>
                        <div class="context-modal__tabs">
                            <button type="button" class="context-modal__tab active" data-tab="context">Search Context</button>
                            <button type="button" class="context-modal__tab" data-tab="explanation">Why Recommended</button>
                        </div>
                        <div class="context-modal__body">
                            <div class="context-modal__tab-content active" data-content="context">
                                <div class="context-modal__items">
                                    ${contextItems}
                                </div>
                            </div>
                            <div class="context-modal__tab-content" data-content="explanation">
                                <div class="explanation-content" id="explanation-content-${userId}">
                                    <div class="explanation-loading" id="explanation-loading-${userId}">
                                        <p><span class="spinner">⏳</span><br>Generating explanation...</p>
                                    </div>
                                    <div class="explanation-loaded" id="explanation-loaded-${userId}">
                                        <p class="explanation-text" id="explanation-text-${userId}"></p>
                                        <div class="explanation-details">
                                            <h4 class="explanation-details__title">Key Matching Factors:</h4>
                                            <ul class="explanation-details__list" id="explanation-factors-${userId}"></ul>
                                        </div>
                                    </div>
                                    <div class="explanation-error" id="explanation-error-${userId}">
                                        <p>Unable to generate explanation. Please try again later.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <script type="application/json" class="trail-data" data-user="${userId}">
                    ${JSON.stringify({
                        exact: result.exact || [],
                        suggestions: result.suggestions || [],
                        collaborative: result.collaborative || [],
                        user_label: userLabel,
                        user_id: userId,
                        actual_user_id: result.scenario?.user_id ?? result.user_id ?? (userId === 'a' || userId === 'b' ? null : userId)
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

        renderMapView(result, userId, userLabel, defaultView) {
            const isActive = defaultView === 'map';
            
            return `
                <div class="view-section ${isActive ? 'active' : ''}" data-view="map" data-panel="${userId}">
                    <div class="map-container">
                        <div class="map-canvas demo-map" id="demo-map-${userId}"></div>
                        <div class="map-legend">
                        <div class="legend-item">
                            <span class="legend-marker exact-marker"></span>
                            <span>Recommended</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-marker suggestion-marker"></span>
                            <span>Suggestions</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-marker legend-marker--with-ring">
                                <svg width="18" height="18" viewBox="0 0 18 18">
                                    <circle cx="9" cy="9" r="8" fill="none"/>
                                </svg>
                            </span>
                            <span>Collaborative (with ring)</span>
                        </div>
                        </div>
                    </div>
                </div>
            `;
        }

        /** Resolve "a"/"b" to numeric profile id for profile URLs and save API. */
        resolveNumericUserId(userId, result) {
            if (userId === 'a' || userId === 'b') {
                const fromResult = result?.scenario?.user_id ?? result?.user_id ?? result?.actual_user_id;
                if (fromResult != null) return String(fromResult);
                const sel = document.getElementById('demo-form')?.querySelector(`#user-select-${userId}`);
                if (sel?.value) return sel.value;
                return userId;
            }
            if (userId != null && userId !== '') return String(userId);
            const fromResult = result?.actual_user_id ?? result?.user_id ?? result?.scenario?.user_id;
            return fromResult != null ? String(fromResult) : '';
        }

        renderListView(result, userId, defaultView) {
            const isActive = defaultView === 'list';
            const uid = this.resolveNumericUserId(userId, result);
            const exactTrails = (result.exact || []).map(trail => this.renderTrailItem(trail, 'recommended', uid)).join('');
            const suggestions = (result.suggestions || []).map(trail => this.renderTrailItem(trail, 'suggested', uid)).join('');
            const collaborative = (result.collaborative || []).map(trail => this.renderTrailItem(trail, 'collaborative', uid)).join('');

            return `
                <div class="view-section ${isActive ? 'active' : ''}" data-view="list" data-panel="${userId}">
                    <div class="result-section">
                        <div class="section-header">
                            <h3>🎯 Recommended (${(result.exact || []).length})</h3>
                            <small>Perfect matches for this situation</small>
                        </div>
                        <div class="trail-list modern">${exactTrails || '<p class="empty-state">No direct matches</p>'}</div>
                    </div>
                    <div class="result-section">
                        <div class="section-header">
                            <h3>✨ Suggestions (${(result.suggestions || []).length})</h3>
                            <small>High potential even if slightly off the brief</small>
                        </div>
                        <div class="trail-list modern">${suggestions || '<p class="empty-state">No suggestions</p>'}</div>
                    </div>
                    ${(result.collaborative || []).length > 0 ? `
                    <div class="result-section">
                        <div class="section-header">
                            <h3>👥 Popular with Similar Hikers (${(result.collaborative || []).length})</h3>
                            <small>Trails loved by other users with the same profile</small>
                        </div>
                        <div class="trail-list modern">${collaborative || '<p class="empty-state">No collaborative recommendations</p>'}</div>
                    </div>
                    ` : ''}
                </div>
            `;
        }

        renderCardsView(result, userId, defaultView) {
            const isActive = defaultView === 'cards';
            const uid = this.resolveNumericUserId(userId, result);
            const exactTrails = (result.exact || []).map(trail => this.renderTrailCard(trail, 'recommended', uid)).join('');
            const suggestions = (result.suggestions || []).map(trail => this.renderTrailCard(trail, 'suggested', uid)).join('');
            const collaborative = (result.collaborative || []).map(trail => this.renderTrailCard(trail, 'collaborative', uid)).join('');

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
                    ${(result.collaborative || []).length > 0 ? `
                    <div class="result-section">
                        <h3>👥 Popular with Similar Hikers (${(result.collaborative || []).length})</h3>
                        <div class="trail-grid">${collaborative || '<p class="empty-state">No collaborative recommendations</p>'}</div>
                    </div>
                    ` : ''}
                </div>
            `;
        }

        renderTrailItem(trail, type, userId) {
            const uid = userId != null && userId !== '' ? String(userId) : '';
            const detailUrl = uid ? `/profile/${uid}/trail/${trail.trail_id || ''}` : '#';
            const difficulty = trail.difficulty || 0;
            const difficultyClass = difficulty <= 3 ? 'easy' : difficulty <= 6 ? 'medium' : 'hard';
            const difficultyText = difficulty <= 3 ? 'Easy' : difficulty <= 6 ? 'Medium' : 'Hard';

            const isCollaborative = trail.is_collaborative || (trail.view_type && trail.view_type.includes('collaborative'));
            const collaborativeIcon = isCollaborative ?
                `<div class="collaborative-icon-wrapper" tabindex="0" role="img" aria-label="Similar profiles like it">
                    <svg class="collaborative-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="10" cy="10" r="9" fill="rgb(14, 165, 233)" stroke="#fff" stroke-width="1"/>
                        <path d="M10 4.5L11.8 8.2L15.9 9.1L13.1 11.8L13.6 15.9L10 14.2L6.4 15.9L6.9 11.8L4.1 9.1L8.2 8.2L10 4.5Z" fill="#fff"/>
                    </svg>
                    <span class="collaborative-icon-tooltip">Similar profiles likes it</span>
                </div>` : '';

            const relevanceBadge = type === 'suggested' ? `<span class="relevance-badge">${Math.round(trail.relevance_percentage || 0)}%</span>` : '';
            const collaborativeBadge = type === 'collaborative' && trail.collaborative_avg_rating ?
                `<span class="badge badge--collaborative">⭐ ${(trail.collaborative_avg_rating).toFixed(1)}/5 (${trail.collaborative_user_count || 0} users)</span>` : '';

            const weatherSpan = trail.forecast_weather
                ? `<span>${this.getWeatherIcon(trail.forecast_weather)} ${(trail.forecast_weather).charAt(0).toUpperCase() + (trail.forecast_weather).slice(1).replace('_', ' ')}</span>`
                : '';

            // Match server-rendered list structure: name as link, Save in meta, compact stats row
            return `
                <div class="trail-card modern ${type}" data-trail-id="${trail.trail_id || ''}">
                    <div class="card-heading">
                        <a href="${detailUrl}" class="trail-name-link">${(trail.name || 'Unknown').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</a>
                        <div class="card-heading__meta">
                            <button type="button" class="btn-save-trail-demo btn btn-secondary btn--sm" data-trail-id="${trail.trail_id || ''}" data-user-id="${uid}">Save Trail</button>
                            ${collaborativeIcon}
                            ${collaborativeBadge}
                            ${relevanceBadge}
                            <span class="pill difficulty-${difficultyClass}">${difficultyText}</span>
                            <button type="button" class="trail-explanation-btn" aria-label="Why was this recommended?" data-trail-id="${trail.trail_id || ''}" data-user-id="${uid}">
                                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M8 2C4.69 2 2 4.69 2 8C2 11.31 4.69 14 8 14C11.31 14 14 11.31 14 8C14 4.69 11.31 2 8 2Z" stroke="currentColor" stroke-width="1.5" fill="none"/>
                                    <path d="M8 5.5V8.5M8 11H8.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div class="trail-stats">
                        <span>${trail.distance || '—'} km</span>
                        <span>${Utils.formatDuration(trail.duration)}</span>
                        <span>${trail.elevation_gain || '—'} m</span>
                        ${weatherSpan}
                    </div>
                    <div class="trail-explanation-content" id="trail-explanation-${trail.trail_id || ''}">
                        <div class="trail-explanation-loading"><span class="spinner">⏳</span> Generating...</div>
                        <div class="trail-explanation-loaded">
                            <p class="trail-explanation-text"></p>
                            <ul class="trail-explanation-factors"></ul>
                        </div>
                    </div>
                    ${type === 'collaborative' && trail.recommendation_reason ? `<div class="alert--collaborative"><small class="alert-title">💡 ${(trail.recommendation_reason).replace(/</g, '&lt;').replace(/>/g, '&gt;')}</small></div>` : ''}
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

        renderTrailCard(trail, type, userId) {
            const uid = userId != null && userId !== '' ? String(userId) : '';
            const detailUrl = uid ? `/profile/${uid}/trail/${trail.trail_id || ''}` : '#';
            const difficulty = trail.difficulty || 0;
            const difficultyClass = difficulty <= 3 ? 'easy' : difficulty <= 6 ? 'medium' : 'hard';
            const difficultyText = difficulty <= 3 ? 'Easy' : difficulty <= 6 ? 'Medium' : 'Hard';
            const relevance = type === 'suggested' ? `<span class="trail-card__relevance">${Math.round(trail.relevance_percentage || 0)}% match</span>` : '';
            
            // Check if trail is collaborative (for any type, not just 'collaborative')
            const isCollaborative = trail.is_collaborative || (trail.view_type && trail.view_type.includes('collaborative'));
            const collaborativeIcon = isCollaborative ? 
                `<div class="collaborative-icon-wrapper" tabindex="0" role="img" aria-label="Similar profiles like it">
                    <svg class="collaborative-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="10" cy="10" r="9" fill="rgb(14, 165, 233)" stroke="#fff" stroke-width="1"/>
                        <path d="M10 4.5L11.8 8.2L15.9 9.1L13.1 11.8L13.6 15.9L10 14.2L6.4 15.9L6.9 11.8L4.1 9.1L8.2 8.2L10 4.5Z" fill="#fff"/>
                    </svg>
                    <span class="collaborative-icon-tooltip">Similar profiles likes it</span>
                </div>` : '';
            
            const collaborativeBadge = type === 'collaborative' && trail.collaborative_avg_rating ? 
                `<span class="badge badge--collaborative">⭐ ${trail.collaborative_avg_rating.toFixed(1)}/5 (${trail.collaborative_user_count || 0} users)</span>` : '';

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
            const nameEscaped = (trail.name || 'Unknown').replace(/</g, '&lt;').replace(/>/g, '&gt;');

            return `
                <div class="trail-card ${type}" data-trail-id="${trail.trail_id || ''}">
                    <div class="trail-card__map-container">
                        <div class="trail-card__mini-map" id="${mapId}" data-lat="${trail.latitude}" data-lng="${trail.longitude}" ${coordinatesAttr}></div>
                        ${relevance ? `<div class="trail-card__relevance-badge">${relevance}</div>` : ''}
                    </div>
                    <div class="trail-card__content">
                        <div class="trail-card__header">
                            <h3 class="trail-card__title"><a href="${detailUrl}" class="trail-name-link">${nameEscaped}</a></h3>
                            <div class="card-heading__meta">
                                <button type="button" class="btn-save-trail-demo btn btn-secondary btn--sm" data-trail-id="${trail.trail_id || ''}" data-user-id="${uid}">Save Trail</button>
                                ${collaborativeIcon}
                                ${collaborativeBadge}
                                <span class="trail-card__difficulty difficulty-${difficultyClass}">${difficultyText}</span>
                                <button type="button" class="trail-explanation-btn" aria-label="Why was this recommended?" data-trail-id="${trail.trail_id || ''}" data-user-id="${uid}">
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M8 2C4.69 2 2 4.69 2 8C2 11.31 4.69 14 8 14C11.31 14 14 11.31 14 8C14 4.69 11.31 2 8 2Z" stroke="currentColor" stroke-width="1.5" fill="none"/>
                                        <path d="M8 5.5V8.5M8 11H8.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                    </svg>
                                </button>
                            </div>
                        </div>
                        <p class="trail-card__description">${description}</p>
                        ${landscapesHTML}
                        ${type === 'collaborative' && trail.recommendation_reason ? `
                        <div class="alert--collaborative"><small class="alert-title">💡 ${trail.recommendation_reason}</small></div>
                        ` : ''}
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
                        <div class="trail-explanation-content" id="trail-explanation-${trail.trail_id || ''}">
                            <div class="trail-explanation-loading"><span class="spinner">⏳</span> Generating...</div>
                            <div class="trail-explanation-loaded">
                                <p class="trail-explanation-text"></p>
                                <ul class="trail-explanation-factors"></ul>
                            </div>
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
                // Remove existing map and reinitialize to ensure fresh state
                this.mapManager.removeMap(mapId);
                // Clear container if it has Leaflet ID
                if (mapContainer._leaflet_id) {
                    mapContainer.innerHTML = '';
                    delete mapContainer._leaflet_id;
                }
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
                    ...(trailData.exact || []).map(t => ({
                        ...t,
                        view_type: t.view_type && t.view_type.includes('collaborative') ? t.view_type : 'recommended'
                    })),
                    ...(trailData.suggestions || []).map(t => ({
                        ...t,
                        // Preserve view_type if it includes 'collaborative', otherwise set to 'suggested'
                        view_type: t.view_type && t.view_type.includes('collaborative') ? t.view_type : 'suggested'
                    })),
                    ...(trailData.collaborative || []).map(t => ({ ...t, view_type: 'collaborative', is_collaborative: true }))
                ];

                // Use numeric user id for profile/save links: resolve "a"/"b" from form selection
                const numericUserId = (userId === 'a' || userId === 'b')
                    ? (document.getElementById('demo-form')?.querySelector(`#user-select-${userId}`)?.value || trailData.actual_user_id || trailData.user_id || userId)
                    : (trailData.actual_user_id ?? trailData.user_id ?? userId);

                this.mapManager.addTrailMarkers(map, allTrails, { userId: numericUserId });
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
                // Set default view based on connection from server-rendered results
                this.initializeServerRenderedViews();
                this.initializeViews();
            }
        }

        initializeServerRenderedViews() {
            // Get connection value from URL parameters (for server-rendered results)
            const urlParams = new URLSearchParams(window.location.search);
            const connectionFromUrl = urlParams.get('a_connection') || urlParams.get('connection') || null;
            
            // Handle server-rendered results (from demo_panel.html partial)
            // Find all result panels with data-connection attribute
            const serverRenderedPanels = document.querySelectorAll('.demo-panel[data-connection], .result-panel[data-connection]');
            
            serverRenderedPanels.forEach(panel => {
                // Prefer connection from URL, then from data attribute, then fallback
                const connection = connectionFromUrl || panel.dataset.connection || 'medium';
                const defaultView = this.getDefaultView(connection);
                
                // Find the view toggle buttons and sections for this panel
                const panelId = panel.dataset.panelId || panel.id || panel.dataset.userIndex || 'default';
                const viewToggle = panel.querySelector('.demo-view-toggle') || panel.querySelector('.view-toggle');
                const viewSections = panel.querySelector('.demo-results[data-panel-id]') || panel.querySelector('.view-sections');
                
                if (viewToggle && viewSections) {
                    // Set active button
                    const buttons = viewToggle.querySelectorAll('.view-toggle-btn, .view-toggle__button');
                    buttons.forEach(btn => {
                        if (btn.dataset.view === defaultView) {
                            btn.classList.add('active');
                        } else {
                            btn.classList.remove('active');
                        }
                    });
                    
                    // Set active section
                    const sections = viewSections.querySelectorAll('.demo-view-section, .view-section');
                    sections.forEach(section => {
                        if (section.dataset.view === defaultView) {
                            section.classList.add('active');
                            section.classList.remove('hidden');
                        } else {
                            section.classList.remove('active');
                            section.classList.add('hidden');
                        }
                    });
                }
            });
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
                        // Map effectiveType to our connection strength levels
                        if (effectiveType === 'slow-2g' || effectiveType === '2g') {
                            this.state.connectionStrength = 'weak';
                            this.updateConnectionIndicator('weak');
                            return 'weak';
                        } else if (effectiveType === '3g') {
                            this.state.connectionStrength = 'medium';
                            this.updateConnectionIndicator('medium');
                            return 'medium';
                        } else if (effectiveType === '4g') {
                            // For 4g, test actual speed to determine if medium or strong
                            const isFast = await this.testConnectionSpeed();
                            this.state.connectionStrength = isFast ? 'strong' : 'medium';
                            this.updateConnectionIndicator(this.state.connectionStrength);
                            return this.state.connectionStrength;
                        } else {
                            // Unknown or very fast connection (e.g., 5g, wifi)
                            this.state.connectionStrength = 'strong';
                            this.updateConnectionIndicator('strong');
                            return 'strong';
                        }
                    }
                }
                
                // Fallback: test connection speed with a small download
                const isFast = await this.testConnectionSpeed();
                this.state.connectionStrength = isFast ? 'strong' : 'medium';
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
                return isFast;
            } catch (error) {
                console.warn('Connection speed test failed, assuming slow connection:', error);
                // If fetch fails, assume weak connection
                return false;
            }
        }

        /**
         * Get the default view based on connection strength
         * @param {string} connectionStrength - Connection strength from form/search context ('weak', 'medium', 'strong')
         * @returns {string} View type: 'list', 'cards', or 'map'
         */
        getDefaultView(connectionStrength) {
            // Use provided connection strength, or fallback to detected connection
            const strength = connectionStrength || this.state.connectionStrength;
            
            // Adaptive view selection based on form/search connection value:
            // - strong connection: map view (full interactive map)
            // - medium connection: cards view (some graphics, mini maps optional)
            // - weak connection: list view (lightweight, no maps)
            if (strength === 'strong') {
                return 'map';
            } else if (strength === 'medium') {
                return 'cards';
            } else {
                // Default to list for weak or unknown connection
                return 'list';
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
