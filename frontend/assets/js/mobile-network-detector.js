/**
 * Mobile Network Detection & Health Check
 * Monitors API connectivity and network state
 * 
 * Features:
 * - Debounced network state changes (prevents false positives)
 * - Periodic health checks
 * - Automatic backend availability detection
 * - Connection recovery suggestions
 */

const MobileNetworkDetector = {
    // Configuration
    config: {
        healthCheckInterval: 30000,  // 30 seconds
        healthCheckTimeout: 5000,    // 5 seconds timeout
        debounceDelay: 1500,         // 1.5 second debounce
        maxRetries: 3
    },

    // State tracking
    state: {
        isOnline: navigator.onLine,
        isBackendAvailable: false,
        lastHealthCheck: null,
        lastError: null,
        retryCount: 0
    },

    // Timers
    healthCheckTimer: null,
    debounceTimer: null,

    /**
     * Initialize network detector
     */
    init() {
        console.log('📡 Mobile Network Detector initialized');
        
        // Listen to online/offline events
        window.addEventListener('online', () => this._onNetworkChange('online'));
        window.addEventListener('offline', () => this._onNetworkChange('offline'));

        // Start periodic health checks
        this._startHealthChecks();

        // Initial health check
        this.checkBackendHealth();

        console.log('✅ Network detector ready');
    },

    /**
     * Handle network state change (with debounce)
     */
    _onNetworkChange(status) {
        console.log(`📡 Network state changed: ${status}`);

        // Clear existing debounce timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        // Debounce the state change
        this.debounceTimer = setTimeout(() => {
            const isOnline = status === 'online';
            this.state.isOnline = isOnline;

            console.log(`✅ Network state confirmed: ${status}`);

            if (isOnline) {
                console.log('🟢 Device is ONLINE');
                this.checkBackendHealth();
                this._dispatchEvent('network:online', { isOnline: true });
            } else {
                console.warn('🔴 Device is OFFLINE');
                this._dispatchEvent('network:offline', { isOnline: false });
            }
        }, this.config.debounceDelay);
    },

    /**
     * Check if backend is available
     */
    async checkBackendHealth() {
        try {
            const apiUrl = typeof APIConfig !== 'undefined' ? APIConfig.baseUrl : 'http://localhost:5000';
            const healthUrl = `${apiUrl}/health`;

            console.log(`🏥 Checking backend health: ${healthUrl}`);

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.config.healthCheckTimeout);

            const response = await fetch(healthUrl, {
                method: 'GET',
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                this.state.isBackendAvailable = true;
                this.state.lastHealthCheck = new Date();
                this.state.retryCount = 0;
                this.state.lastError = null;

                console.log('✅ Backend is HEALTHY');
                this._dispatchEvent('backend:healthy', { available: true });

                return true;
            } else {
                throw new Error(`Health check failed: ${response.status}`);
            }

        } catch (error) {
            this.state.isBackendAvailable = false;
            this.state.lastError = error.message;
            this.state.retryCount++;

            console.error(`❌ Backend health check failed: ${error.message}`);

            if (this.state.retryCount < this.config.maxRetries) {
                console.log(`🔄 Retry ${this.state.retryCount}/${this.config.maxRetries} in 5s...`);
            } else {
                console.error('❌ Backend unavailable after retries');
                this._dispatchEvent('backend:unavailable', {
                    available: false,
                    error: error.message,
                    retries: this.state.retryCount
                });
            }

            return false;
        }
    },

    /**
     * Start periodic health checks
     */
    _startHealthChecks() {
        this.healthCheckTimer = setInterval(() => {
            if (this.state.isOnline) {
                this.checkBackendHealth();
            }
        }, this.config.healthCheckInterval);
    },

    /**
     * Stop periodic health checks
     */
    stopHealthChecks() {
        if (this.healthCheckTimer) {
            clearInterval(this.healthCheckTimer);
            this.healthCheckTimer = null;
        }
    },

    /**
     * Dispatch custom events
     */
    _dispatchEvent(eventName, detail) {
        window.dispatchEvent(new CustomEvent(eventName, { detail }));
    },

    /**
     * Get connection status
     */
    getStatus() {
        return {
            isOnline: this.state.isOnline,
            isBackendAvailable: this.state.isBackendAvailable,
            lastHealthCheck: this.state.lastHealthCheck,
            lastError: this.state.lastError,
            retryCount: this.state.retryCount
        };
    },

    /**
     * Check if should show offline UI
     */
    shouldShowOfflineUI() {
        // Show offline only if both conditions are true:
        // 1. Device reports offline
        // 2. Backend health checks fail
        return !this.state.isOnline || !this.state.isBackendAvailable;
    },

    /**
     * Get user-friendly status message
     */
    getStatusMessage() {
        if (!this.state.isOnline) {
            return '📡 Device is offline - check your connection';
        }

        if (!this.state.isBackendAvailable) {
            return '🔧 Backend server is unavailable - trying to reconnect...';
        }

        return '✅ Connected to backend';
    },

    /**
     * Suggest fix for connection issues
     */
    getSuggestions() {
        const suggestions = [];

        if (!this.state.isOnline) {
            suggestions.push('✓ Check your WiFi or cellular connection');
            suggestions.push('✓ Try airplane mode on/off');
            suggestions.push('✓ Restart your app');
        }

        if (this.state.isOnline && !this.state.isBackendAvailable) {
            suggestions.push('✓ Backend server may be down - wait and retry');
            suggestions.push('✓ Check if backend URL is correct in settings');
            suggestions.push('✓ Try changing API URL in Settings → Debug');
        }

        return suggestions;
    },

    /**
     * Debug: Show current network state
     */
    debug() {
        console.group('📡 Network Detection Status');
        console.log('Device Online:', this.state.isOnline);
        console.log('Backend Available:', this.state.isBackendAvailable);
        console.log('Last Health Check:', this.state.lastHealthCheck);
        console.log('Last Error:', this.state.lastError);
        console.log('Retry Count:', this.state.retryCount);
        console.log('Status Message:', this.getStatusMessage());
        console.log('Suggestions:', this.getSuggestions());
        console.groupEnd();
    }
};

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    MobileNetworkDetector.init();
});

// Make globally available
window.MobileNetworkDetector = MobileNetworkDetector;
