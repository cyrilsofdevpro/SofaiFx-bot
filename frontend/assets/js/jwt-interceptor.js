/**
 * JWT Token Interceptor - Global Request/Response Handler
 * Handles token storage, authorization headers, and automatic token refresh
 * 
 * Features:
 * - Mobile-safe token storage (localStorage + sessionStorage fallback)
 * - Automatic Authorization header injection
 * - JWT refresh token flow for expired tokens
 * - CORS credential handling
 * - Debug logging for authentication issues
 */

const JWTInterceptor = {
    // Configuration
    config: {
        apiBaseUrl: 'http://localhost:5000',
        tokenKey: 'access_token',
        refreshTokenKey: 'refresh_token',
        tokenExpiryKey: 'token_expiry',
        maxRetries: 3,
        retryDelay: 500
    },

    // Track active requests to prevent refresh loop
    isRefreshing: false,
    refreshSubscribers: [],

    /**
     * Initialize interceptor
     * Call this on app startup (before making API calls)
     */
    init() {
        console.log('🔐 JWT Interceptor initialized');
        this.setupFetchInterceptor();
    },

    /**
     * Mobile-safe token storage with fallback
     * Try localStorage first, fallback to sessionStorage
     */
    setToken(token, refreshToken = null, expiresIn = 3600) {
        try {
            // Try localStorage (preferred)
            localStorage.setItem(this.config.tokenKey, token);
            if (refreshToken) {
                localStorage.setItem(this.config.refreshTokenKey, refreshToken);
            }
            
            // Calculate expiry time (current time + expiresIn seconds)
            const expiryTime = new Date().getTime() + (expiresIn * 1000);
            localStorage.setItem(this.config.tokenExpiryKey, expiryTime.toString());
            
            console.log('✅ Token stored in localStorage');
        } catch (e) {
            // Fallback to sessionStorage (for mobile or private browsing)
            console.warn('⚠️ localStorage failed, using sessionStorage:', e.message);
            sessionStorage.setItem(this.config.tokenKey, token);
            if (refreshToken) {
                sessionStorage.setItem(this.config.refreshTokenKey, refreshToken);
            }
            
            const expiryTime = new Date().getTime() + (expiresIn * 1000);
            sessionStorage.setItem(this.config.tokenExpiryKey, expiryTime.toString());
            
            console.log('✅ Token stored in sessionStorage (fallback)');
        }
    },

    /**
     * Get token from storage with fallback
     */
    getToken() {
        return localStorage.getItem(this.config.tokenKey) || 
               sessionStorage.getItem(this.config.tokenKey) || 
               null;
    },

    /**
     * Get refresh token from storage
     */
    getRefreshToken() {
        return localStorage.getItem(this.config.refreshTokenKey) || 
               sessionStorage.getItem(this.config.refreshTokenKey) || 
               null;
    },

    /**
     * Check if token is expired
     */
    isTokenExpired() {
        const expiryStr = localStorage.getItem(this.config.tokenExpiryKey) || 
                          sessionStorage.getItem(this.config.tokenExpiryKey);
        
        if (!expiryStr) return false;
        
        const expiryTime = parseInt(expiryStr, 10);
        const now = new Date().getTime();
        const isExpired = now > expiryTime;
        
        if (isExpired) {
            console.warn('⚠️ Token is expired');
        }
        
        return isExpired;
    },

    /**
     * Clear all tokens
     */
    clearTokens() {
        localStorage.removeItem(this.config.tokenKey);
        localStorage.removeItem(this.config.refreshTokenKey);
        localStorage.removeItem(this.config.tokenExpiryKey);
        
        sessionStorage.removeItem(this.config.tokenKey);
        sessionStorage.removeItem(this.config.refreshTokenKey);
        sessionStorage.removeItem(this.config.tokenExpiryKey);
        
        console.log('🗑️ Tokens cleared');
    },

    /**
     * Refresh access token using refresh token
     */
    async refreshAccessToken() {
        if (this.isRefreshing) {
            // Wait for ongoing refresh to complete
            return new Promise((resolve) => {
                this.refreshSubscribers.push(resolve);
            });
        }

        this.isRefreshing = true;
        const refreshToken = this.getRefreshToken();

        if (!refreshToken) {
            console.warn('⚠️ No refresh token available');
            this.isRefreshing = false;
            return null;
        }

        try {
            console.log('🔄 Refreshing access token...');
            
            const response = await fetch(`${this.config.apiBaseUrl}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    refresh_token: refreshToken 
                })
            });

            if (!response.ok) {
                throw new Error(`Token refresh failed: ${response.status}`);
            }

            const data = await response.json();
            
            // Store new tokens
            this.setToken(
                data.access_token,
                data.refresh_token || refreshToken,
                data.expires_in || 3600
            );

            console.log('✅ Access token refreshed successfully');

            // Notify all pending requests
            this.isRefreshing = false;
            this.refreshSubscribers.forEach(cb => cb(true));
            this.refreshSubscribers = [];

            return data.access_token;

        } catch (error) {
            console.error('❌ Token refresh failed:', error);
            
            // Clear tokens if refresh failed
            this.clearTokens();
            this.isRefreshing = false;
            
            // Notify pending requests of failure
            this.refreshSubscribers.forEach(cb => cb(false));
            this.refreshSubscribers = [];
            
            // Redirect to login
            if (typeof AuthSystem !== 'undefined') {
                AuthSystem.clearAuth();
            }
            
            return null;
        }
    },

    /**
     * Setup fetch API interceptor
     * Automatically adds Authorization header to all requests
     */
    setupFetchInterceptor() {
        const originalFetch = window.fetch;

        window.fetch = async (...args) => {
            let [resource, config] = args;
            
            // Only add auth header to API calls, not external resources
            if (typeof resource === 'string' && resource.includes('/api') || resource.includes('/auth')) {
                config = config || {};
                config.headers = config.headers || {};

                const token = this.getToken();
                if (token) {
                    config.headers['Authorization'] = `Bearer ${token}`;
                    console.debug('📤 Authorization header added');
                }
            }

            let response = await originalFetch(resource, config);

            // Handle 401 Unauthorized - token expired
            if (response.status === 401 && !config._retry) {
                console.warn('⚠️ Received 401 Unauthorized - attempting token refresh');
                
                config._retry = true;
                const newToken = await this.refreshAccessToken();

                if (newToken) {
                    config.headers['Authorization'] = `Bearer ${newToken}`;
                    response = await originalFetch(resource, config);
                } else {
                    console.error('❌ Token refresh failed - redirecting to login');
                }
            }

            return response;
        };

        console.log('✅ Fetch interceptor installed');
    },

    /**
     * Debug: Log current auth state
     */
    debugAuthState() {
        const token = this.getToken();
        const refreshToken = this.getRefreshToken();
        const expiryStr = localStorage.getItem(this.config.tokenExpiryKey) || 
                          sessionStorage.getItem(this.config.tokenExpiryKey);
        const isExpired = this.isTokenExpired();

        console.group('🔐 JWT Auth State');
        console.log('Access Token:', token ? `${token.substring(0, 20)}...` : 'None');
        console.log('Refresh Token:', refreshToken ? `${refreshToken.substring(0, 20)}...` : 'None');
        console.log('Token Expiry:', expiryStr ? new Date(parseInt(expiryStr, 10)).toLocaleString() : 'None');
        console.log('Is Expired:', isExpired);
        console.log('Storage Used:', token && localStorage.getItem(this.config.tokenKey) ? 'localStorage' : 'sessionStorage');
        console.groupEnd();
    }
};

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    JWTInterceptor.init();
});
