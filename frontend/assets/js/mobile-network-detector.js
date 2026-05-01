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
        healthCheckTimeout: 20000,   // 20 seconds (allow for Render cold start)
        debounceDelay: 2000,         // 2 second debounce (reduce false positives)
        maxRetries: 5,               // More retries for cold starts
        initialRetryDelay: 2000      // 2s delay before first retry
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
                console.log('🟢 Device is ONLINE - checking backend...');
                // Reset retry count on network recovery
                this.state.retryCount = 0;
                this.checkBackendHealth();
                this._dispatchEvent('network:online', { isOnline: true });
            } else {
                console.warn('🔴 Device is OFFLINE');
                this.state.isBackendAvailable = false;
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

            console.log(`🏥 [Attempt ${this.state.retryCount + 1}] Checking backend health: ${healthUrl}`);

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.config.healthCheckTimeout);

            const startTime = performance.now();
            const response = await fetch(healthUrl, {
                method: 'GET',
                signal: controller.signal,
                headers: {
                    'Accept': 'application/json'
                }
            });

            clearTimeout(timeoutId);
            const duration = Math.round(performance.now() - startTime);

            if (response.ok) {
                this.state.isBackendAvailable = true;
                this.state.lastHealthCheck = new Date();
                this.state.retryCount = 0;
                this.state.lastError = null;

                console.log(`✅ Backend is HEALTHY (responded in ${duration}ms)`);
                this._dispatchEvent('backend:healthy', { available: true });

                return true;
            } else {
                throw new Error(`Health check failed: HTTP ${response.status}`);
            }

        } catch (error) {
            this.state.isBackendAvailable = false;
            this.state.lastError = error.message;
            this.state.retryCount++;

            console.warn(`⚠️ [Attempt ${this.state.retryCount}] Health check failed: ${error.message}`);

            if (this.state.retryCount < this.config.maxRetries) {
                // Calculate delay: initial short delay, then exponential backoff
                const delay = Math.min(5000, this.config.initialRetryDelay * Math.pow(1.5, this.state.retryCount - 1));
                console.log(`🔄 Retrying in ${delay}ms... (${this.state.retryCount}/${this.config.maxRetries})`);
                
                // Schedule retry
                setTimeout(() => {
                    if (this.state.isOnline) {
                        this.checkBackendHealth();
                    }
                }, delay);
            } else {
                console.error(`❌ Backend unavailable after ${this.state.retryCount} attempts`);
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
