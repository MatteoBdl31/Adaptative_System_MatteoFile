/**
 * Upload JavaScript
 * Handles file upload, validation, and trail matching
 */

const UploadManager = (function() {
    'use strict';
    
    let currentUserId = null;
    let currentUploadId = null;
    
    function init(userId) {
        currentUserId = userId;
        setupUploadForm();
    }
    
    function setupUploadForm() {
        const form = document.getElementById('upload-form');
        if (!form) return;
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            handleUpload();
        });
    }
    
    function handleUpload() {
        const fileInput = document.getElementById('trail-file');
        const file = fileInput.files[0];
        
        if (!file) {
            showStatus('Please select a file', 'error');
            return;
        }
        
        if (!file.name.endsWith('.json')) {
            showStatus('Please select a JSON file', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('format', 'json');
        
        showStatus('Uploading...', 'info');
        
        fetch(`/api/profile/${currentUserId}/upload`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showStatus(data.error, 'error');
                return;
            }
            
            currentUploadId = data.upload_id;
            showStatus('File uploaded successfully!', 'success');
            
            if (data.matched && data.trail_id) {
                // Auto-associate if matched
                associateTrail(data.trail_id);
            } else {
                // Show trail matching UI
                showTrailMatching(data.trail_id);
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            showStatus('Upload failed: ' + error.message, 'error');
        });
    }
    
    function showTrailMatching(matchedTrailId) {
        const matchingDiv = document.getElementById('upload-matching');
        const select = document.getElementById('trail-match-select');
        
        if (!matchingDiv || !select) return;
        
        // Load all trails for selection
        fetch('/api/trails')
            .then(response => {
                if (!response.ok) {
                    // Fallback: try getting trails from all_trails endpoint
                    return fetch('/trails').then(r => r.text()).then(() => ({ trails: [] }));
                }
                return response.json();
            })
            .then(data => {
                const trails = data.trails || [];
                select.innerHTML = '<option value="">Select a trail...</option>';
                trails.forEach(trail => {
                    const option = document.createElement('option');
                    option.value = trail.trail_id;
                    option.textContent = trail.name || trail.trail_id;
                    if (matchedTrailId && trail.trail_id === matchedTrailId) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });
                
                matchingDiv.style.display = 'block';
                
                // Setup associate button
                const associateBtn = document.getElementById('associate-trail-btn');
                if (associateBtn) {
                    associateBtn.onclick = function() {
                        const selectedTrailId = select.value;
                        if (selectedTrailId) {
                            associateTrail(selectedTrailId);
                        } else {
                            alert('Please select a trail');
                        }
                    };
                }
            })
            .catch(error => {
                console.error('Error loading trails:', error);
            });
    }
    
    function associateTrail(trailId) {
        if (!currentUploadId) {
            showStatus('No upload to associate', 'error');
            return;
        }
        
        showStatus('Associating trail data...', 'info');
        
        fetch(`/api/profile/${currentUserId}/upload/${currentUploadId}/associate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ trail_id: trailId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showStatus('Trail data associated successfully!', 'success');
                document.getElementById('upload-matching').style.display = 'none';
                
                // Reload trails
                if (typeof TrailListManager !== 'undefined') {
                    TrailListManager.loadTrails(currentUserId);
                }
                
                // Reset form
                document.getElementById('upload-form').reset();
                currentUploadId = null;
            } else {
                showStatus('Failed to associate trail data', 'error');
            }
        })
        .catch(error => {
            console.error('Association error:', error);
            showStatus('Association failed: ' + error.message, 'error');
        });
    }
    
    function showStatus(message, type) {
        const statusDiv = document.getElementById('upload-status');
        if (!statusDiv) return;
        
        statusDiv.textContent = message;
        statusDiv.className = `upload-status ${type}`;
        
        if (type === 'success') {
            setTimeout(() => {
                statusDiv.textContent = '';
                statusDiv.className = 'upload-status';
            }, 3000);
        }
    }
    
    return {
        init: init
    };
})();

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const userId = parseInt(document.querySelector('[data-user-id]')?.getAttribute('data-user-id')) || 
                   parseInt(window.location.pathname.split('/').pop());
    if (userId) {
        UploadManager.init(userId);
    }
});
