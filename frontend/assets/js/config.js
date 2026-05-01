/**
 * API Configuration
 * Centralized URL and settings for all API calls
 * 
 * Supports multiple environments:
 * - Development: http://localhost:5000
 * - Testing: http://192.168.x.x:5000 (local network IP)
 * - Production: https://api.yourdomain.com
 */

const APIConfig = {
    // Detect environment and set base URL
    getBaseUrl() {
        // Check for custom URL in sessionStorage/localStorage (for testing)
        const customUrl = sessionStorage.getItem('API_BASE_URL') || localStorage.getItem('API_BASE_URL');
        if (customUrl) {
            console.log('🌐 Using custom API URL:', customUrl);
            return customUrl;
        }

        // Production: Use window.location for relative URLs
        if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
            // For deployed frontend, use same origin
            const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
            const baseUrl = `${protocol}//${window.location.host}`;
            console.log('🌐 Production mode - API URL:', baseUrl);
            return baseUrl;
        }

        // Development: Use localhost backend
        const url = 'http://localhost:5000';
        console.log('🌐 Development mode - API URL:', url);
        return url;
    },

    baseUrl: null,

    /**
     * Initialize API config
     * Call this on app startup
     */
    init() {
        this.baseUrl = this.getBaseUrl();
        console.log('✅ APIConfig initialized:', this.baseUrl);
    },

    /**
     * Set custom API URL (for testing)
     * Useful for testing with local network IP or staging servers
     */
    setCustomUrl(url) {
        sessionStorage.setItem('API_BASE_URL', url);
        this.baseUrl = url;
        console.log('✅ Custom API URL set:', url);
    },

    /**
     * Clear custom API URL
     */
    clearCustomUrl() {
        sessionStorage.removeItem('API_BASE_URL');
        localStorage.removeItem('API_BASE_URL');
        this.baseUrl = this.getBaseUrl();
        console.log('✅ Custom API URL cleared, using default:', this.baseUrl);
    },

    /**
     * Build full API URL
     */
    buildUrl(endpoint) {
        const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
        return url;
    },

    /**
     * Make API request with error logging
     */
    async fetch(endpoint, options = {}) {
        const url = this.buildUrl(endpoint);
        const method = options.method || 'GET';

        try {
            console.log(`📤 ${method} ${url}`);

            const response = await fetch(url, options);

            // Log response status
            console.log(`📥 ${method} ${url} → ${response.status}`);

            // Log error responses
            if (!response.ok) {
                const data = await response.json().catch(() => ({ error: 'Unknown error' }));
                console.error(`❌ ${method} ${url} → ${response.status}:`, data);

                // Return error response (don't throw, let caller handle)
                return {
                    ok: false,
                    status: response.status,
                    data: data
                };
            }

            const data = await response.json().catch(() => ({}));
            return {
                ok: true,
                status: response.status,
                data: data
            };

        } catch (error) {
            console.error(`❌ ${method} ${url} - Network Error:`, error.message);

            return {
                ok: false,
                status: 0,
                error: error.message,
                data: { error: error.message }
            };
        }
    },

    /**
     * Debug: Show current configuration
     */
    debug() {
        console.group('🔧 API Configuration');
        console.log('Base URL:', this.baseUrl);
        console.log('Environment:', window.location.hostname);
        console.log('Protocol:', window.location.protocol);
        console.groupEnd();
    }
};

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    APIConfig.init();
});

// Make globally available
window.APIConfig = APIConfig;
