/**
 * UI Utility Functions
 * Shared helper functions for dashboard features
 */

/**
 * Analyze a specific currency pair
 */
async function analyzeSymbol(symbol) {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            alert('Please login to analyze');
            return;
        }

        // Show loading state
        const btn = event?.target;
        if (btn) {
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner animate-spin"></i> Analyzing...';
            btn.disabled = true;
        }

        const response = await fetch('http://localhost:5000/api/analyze', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ symbol: symbol })
        });

        if (response.ok) {
            const data = await response.json();
            showNotification(`✅ ${symbol} analyzed: ${data.signal} (${data.confidence}%)`, 'success');
            
            // Refresh recommendations
            if (typeof recommendationsManager !== 'undefined') {
                setTimeout(() => recommendationsManager.refresh(), 500);
            }
        } else {
            showNotification('Failed to analyze symbol', 'error');
        }
    } catch (error) {
        console.error('Error analyzing symbol:', error);
        showNotification('Error analyzing symbol', 'error');
    } finally {
        if (event?.target) {
            event.target.disabled = false;
            event.target.innerHTML = '<i class="fas fa-play"></i> Analyze';
        }
    }
}

/**
 * Add pair to monitored list
 */
async function addToMonitored(symbol) {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        // Get current monitored pairs
        const response = await fetch('http://localhost:5000/api/preferences', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const prefs = await response.json();
            const currentPairs = prefs.monitored_pairs || [];
            
            // Check if already monitored
            if (currentPairs.includes(symbol)) {
                showNotification(`${symbol} is already monitored`, 'info');
                return;
            }

            // Add to list
            const updatedPairs = [...currentPairs, symbol];

            // Save updated preferences
            const updateResponse = await fetch('http://localhost:5000/api/preferences', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    monitored_pairs: updatedPairs,
                    auto_analysis_enabled: prefs.auto_analysis_enabled,
                    auto_analysis_interval: prefs.auto_analysis_interval
                })
            });

            if (updateResponse.ok) {
                showNotification(`✅ ${symbol} added to monitored pairs`, 'success');
                // Refresh settings display
                if (typeof settingsManager !== 'undefined') {
                    settingsManager.loadPreferences();
                }
            }
        }
    } catch (error) {
        console.error('Error adding to monitored:', error);
        showNotification('Error updating preferences', 'error');
    }
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    const colors = {
        success: 'bg-green-600 text-white',
        error: 'bg-red-600 text-white',
        info: 'bg-blue-600 text-white',
        warning: 'bg-yellow-600 text-white'
    };

    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        info: 'fas fa-info-circle',
        warning: 'fas fa-exclamation-triangle'
    };

    const notification = document.createElement('div');
    notification.className = `fixed bottom-4 right-4 ${colors[type] || colors.info} px-6 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-fadeIn z-50 max-w-sm`;
    notification.innerHTML = `
        <i class="${icons[type]}"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" class="ml-auto text-lg hover:opacity-70">
            ×
        </button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 4000);
}

/**
 * Format time for display
 */
function formatTime(date) {
    if (!date) return '--';
    return new Date(date).toLocaleTimeString();
}

/**
 * Format large numbers with commas
 */
function formatNumber(num) {
    return num?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') || '0';
}

/**
 * Get confidence color
 */
function getConfidenceColor(confidence) {
    if (confidence >= 80) return 'text-green-400';
    if (confidence >= 60) return 'text-yellow-400';
    if (confidence >= 40) return 'text-orange-400';
    return 'text-red-400';
}

/**
 * Get signal type color
 */
function getSignalColor(signal) {
    const colors = {
        'BUY': 'bg-green-900/30 text-green-400 border-green-500/50',
        'SELL': 'bg-red-900/30 text-red-400 border-red-500/50',
        'HOLD': 'bg-yellow-900/30 text-yellow-400 border-yellow-500/50'
    };
    return colors[signal] || 'bg-gray-900/30 text-gray-400';
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Copied to clipboard', 'success');
    } catch (error) {
        console.error('Failed to copy:', error);
        showNotification('Failed to copy', 'error');
    }
}

/**
 * Debounce function for API calls
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Format date for display
 */
function formatDate(date) {
    if (!date) return '--';
    const d = new Date(date);
    return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

/**
 * Parse JWT token to get user info
 */
function parseJWT(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split('')
                .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
        );
        return JSON.parse(jsonPayload);
    } catch (error) {
        console.error('Invalid token:', error);
        return null;
    }
}

/**
 * Get current user ID from token
 */
function getCurrentUserId() {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    const payload = parseJWT(token);
    return payload?.sub || payload?.user_id || null;
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!localStorage.getItem('access_token');
}

/**
 * Handle API errors consistently
 */
function handleAPIError(error, context = '') {
    console.error(`API Error (${context}):`, error);
    
    if (error.message.includes('401')) {
        showNotification('Session expired. Please login again.', 'warning');
        sessionStorage.removeItem('access_token');
        setTimeout(() => location.reload(), 2000);
    } else if (error.message.includes('403')) {
        showNotification('You do not have permission for this action.', 'error');
    } else if (error.message.includes('404')) {
        showNotification('Resource not found.', 'error');
    } else if (error.message.includes('500')) {
        showNotification('Server error. Please try again later.', 'error');
    } else {
        showNotification('An error occurred. Please try again.', 'error');
    }
}

/**
 * Create a modal dialog
 */
function showModal(title, message, buttons = []) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-fadeIn';
    
    const defaultButtons = buttons.length === 0 ? [
        { label: 'OK', action: () => modal.remove() }
    ] : buttons;

    modal.innerHTML = `
        <div class="bg-slate-900 border border-slate-700 rounded-lg p-6 max-w-md w-full shadow-2xl">
            <h3 class="text-lg font-bold text-white mb-2">${title}</h3>
            <p class="text-gray-400 mb-6">${message}</p>
            <div class="flex gap-3">
                ${defaultButtons.map((btn, i) => `
                    <button onclick="event.target.closest('.fixed').remove(); ${btn.action || ''}" 
                            class="flex-1 px-4 py-2 ${i === 0 ? 'bg-green-600 hover:bg-green-500' : 'bg-gray-600 hover:bg-gray-500'} text-white font-semibold rounded-lg transition">
                        ${btn.label}
                    </button>
                `).join('')}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

/**
 * Initialize all feature managers on page load
 */
function initializeFeatures() {
    if (!isAuthenticated()) {
        console.log('User not authenticated, features will load after login');
        return;
    }

    // Initialize all managers
    if (typeof recommendationsManager !== 'undefined') {
        recommendationsManager.renderRecommendations();
    }
    
    if (typeof settingsManager !== 'undefined') {
        settingsManager.loadPreferences();
    }
    
    if (typeof schedulerManager !== 'undefined') {
        schedulerManager.renderSchedulerControls();
        schedulerManager.getJobStatus();
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(initializeFeatures, 1500);
});

// Export for use in other modules
window.UIUtils = {
    analyzeSymbol,
    addToMonitored,
    showNotification,
    formatTime,
    formatNumber,
    getConfidenceColor,
    getSignalColor,
    isValidEmail,
    copyToClipboard,
    debounce,
    formatDate,
    parseJWT,
    getCurrentUserId,
    isAuthenticated,
    handleAPIError,
    showModal,
    initializeFeatures
};
