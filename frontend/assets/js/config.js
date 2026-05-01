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
            console.log('🌐 Custom API URL override:', customUrl);
            return customUrl;
        }

        // Production: Use SAME ORIGIN as frontend (frontend + backend together)
        if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
            // Use same origin - frontend and backend are deployed together
            const baseUrl = `${window.location.protocol}//${window.location.host}`;
            console.log('🌐 Production mode - Same origin API URL:', baseUrl);
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
        console.log('Custom Override:', sessionStorage.getItem('API_BASE_URL') || localStorage.getItem('API_BASE_URL') || 'None');
        console.groupEnd();
    },

    /**
     * Test backend connectivity
     */
    async testConnection() {
        console.log(`🧪 Testing connection to ${this.baseUrl}/health...`);
        try {
            const response = await fetch(`${this.baseUrl}/health`, {
                method: 'GET',
                timeout: 15000
            });
            const data = await response.json();
            console.log('✅ Backend is reachable:', data);
            return { success: true, data };
        } catch (error) {
            console.error('❌ Backend connection failed:', error.message);
            return { success: false, error: error.message };
        }
    }
};

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    APIConfig.init();
});

// Make globally available
window.APIConfig = APIConfig;
