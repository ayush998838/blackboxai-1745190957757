/**
 * Dexent.ai Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            e.preventDefault();
            const target = document.querySelector(targetId);
            if (target) {
                window.scrollTo({
                    top: target.offsetTop - 72,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Feature cards animation on scroll
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.animate-on-scroll');
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementBottom = element.getBoundingClientRect().bottom;
            const isVisible = (elementTop < window.innerHeight) && (elementBottom > 0);
            
            if (isVisible) {
                element.classList.add('animated');
            }
        });
    };

    // Run on initial load
    animateOnScroll();
    
    // Run on scroll
    window.addEventListener('scroll', animateOnScroll);

    // Firebase Authentication Integration (if available)
    try {
        if (typeof firebase !== 'undefined' && firebase.auth) {
            // Set up Firebase auth state observer
            firebase.auth().onAuthStateChanged(function(user) {
                if (user) {
                    // User is signed in
                    console.log('User signed in: ', user.displayName);
                    updateUIForSignedInUser(user);
                } else {
                    // User is signed out
                    console.log('User signed out');
                    updateUIForSignedOutUser();
                }
            });
        }
    } catch (e) {
        console.log('Firebase not initialized');
    }

    // Handle login with Google
    const googleLoginButtons = document.querySelectorAll('.google-login-btn');
    googleLoginButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            if (typeof firebase !== 'undefined' && firebase.auth) {
                const provider = new firebase.auth.GoogleAuthProvider();
                firebase.auth().signInWithPopup(provider).catch(function(error) {
                    console.error('Error signing in with Google:', error);
                });
            } else {
                // Fallback to traditional login
                window.location.href = '/login/google';
            }
        });
    });

    // Record voice sample functionality
    window.recordVoiceSample = function() {
        const modal = new bootstrap.Modal(document.getElementById('recordVoiceModal'));
        if (modal) {
            modal.show();
        } else {
            alert('Voice recording feature will be available soon!');
        }
    };

    // Launch desktop app
    window.launchSystemTray = function() {
        fetch('/api/launch_desktop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showNotification('Desktop app launched successfully!', 'success');
            } else {
                showNotification('Failed to launch desktop app. Please download and install it first.', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred. Please try again.', 'error');
        });
    };

    // Custom notification
    window.showNotification = function(message, type = 'info') {
        const notificationContainer = document.getElementById('notification-container');
        
        if (!notificationContainer) {
            // Create container if it doesn't exist
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.style.position = 'fixed';
            container.style.top = '20px';
            container.style.right = '20px';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.role = 'alert';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        document.getElementById('notification-container').appendChild(notification);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 150);
        }, 5000);
    };

    // Handle form submissions with AJAX
    const ajaxForms = document.querySelectorAll('form[data-ajax="true"]');
    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitButton = form.querySelector('button[type="submit"]');
            
            if (submitButton) {
                const originalText = submitButton.innerHTML;
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            }
            
            fetch(form.action, {
                method: form.method,
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showNotification(data.message || 'Success!', 'success');
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    }
                    if (data.refresh) {
                        window.location.reload();
                    }
                    if (data.reset) {
                        form.reset();
                    }
                } else {
                    showNotification(data.message || 'An error occurred.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('An error occurred. Please try again.', 'danger');
            })
            .finally(() => {
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalText;
                }
            });
        });
    });

    // Handle audio processing toggle
    const processingToggle = document.getElementById('processingToggle');
    if (processingToggle) {
        processingToggle.addEventListener('change', function() {
            const action = this.checked ? 'start_processing' : 'stop_processing';
            
            fetch(`/api/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showNotification(`Audio processing ${this.checked ? 'started' : 'stopped'} successfully!`, 'success');
                } else {
                    this.checked = !this.checked;
                    showNotification(data.message || 'Failed to update audio processing state.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.checked = !this.checked;
                showNotification('An error occurred. Please try again.', 'danger');
            });
        });
    }

    // Update user settings
    const saveSettingsButton = document.querySelector('.save-settings-btn');
    if (saveSettingsButton) {
        saveSettingsButton.addEventListener('click', function() {
            const settings = {
                noise_suppression: document.getElementById('noiseSuppression').checked,
                noise_suppression_level: document.getElementById('noiseSuppressionLevel').value,
                accent_conversion: document.getElementById('accentConversion').checked,
                target_accent: document.querySelector('input[name="targetAccent"]:checked').value,
                identity_preservation: document.getElementById('identityPreservation').checked,
                input_device: document.getElementById('inputDevice').value,
                output_device: document.getElementById('outputDevice').value
            };
            
            fetch('/api/update_settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showNotification('Settings updated successfully!', 'success');
                } else {
                    showNotification(data.message || 'Failed to update settings.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('An error occurred. Please try again.', 'danger');
            });
        });
    }

    // Helper functions for UI updates
    function updateUIForSignedInUser(user) {
        const userDisplayElements = document.querySelectorAll('.user-display-name');
        userDisplayElements.forEach(element => {
            element.textContent = user.displayName || user.email;
        });
        
        const userAvatarElements = document.querySelectorAll('.user-avatar');
        userAvatarElements.forEach(element => {
            if (user.photoURL) {
                element.src = user.photoURL;
            } else {
                element.src = '/static/assets/default-avatar.svg';
            }
        });
        
        document.body.classList.add('user-logged-in');
        document.body.classList.remove('user-logged-out');
    }
    
    function updateUIForSignedOutUser() {
        document.body.classList.remove('user-logged-in');
        document.body.classList.add('user-logged-out');
    }
});