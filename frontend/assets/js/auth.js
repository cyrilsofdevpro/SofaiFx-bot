/**
 * Authentication System - Multi-Tab Support
 * Each tab/window has independent session using sessionStorage
 * Allows multiple accounts to be logged in simultaneously in different tabs
 * 
 * API Configuration:
 * - Uses APIConfig for base URL
 * - Production-ready: uses same origin as frontend
 */

function getAuthToken() {
    try {
        if (typeof AuthSystem !== 'undefined' && AuthSystem.token) {
            return AuthSystem.token;
        }
        return sessionStorage.getItem('access_token') || localStorage.getItem('access_token') || null;
    } catch (error) {
        console.warn('getAuthToken fallback failed:', error);
        return null;
    }
}

const AuthSystem = {
    // Get API base URL - MUST use APIConfig
    _getApiUrl() {
        if (typeof APIConfig !== 'undefined' && APIConfig.baseUrl) {
            return APIConfig.baseUrl;
        }
        // If APIConfig not loaded yet, try to get from window
        if (typeof window !== 'undefined' && window.APIConfig && window.APIConfig.baseUrl) {
            return window.APIConfig.baseUrl;
        }
        // Last resort - use current origin (works for production)
        return window.location.origin;
    },

    // Promise that resolves when auth initialization is complete
    _authReadyPromise: null,
    _authReadyResolve: null,
    
    // Detect sessionStorage support once and use it for tab-isolated auth
    _supportsSessionStorage: (() => {
        try {
            sessionStorage.setItem('__auth_test__', '1');
            sessionStorage.removeItem('__auth_test__');
            return true;
        } catch (e) {
            console.warn('⚠️ sessionStorage unavailable:', e.message);
            return false;
        }
    })(),

    // Get token from sessionStorage if supported, otherwise fallback to localStorage
    get token() {
        const sessionToken = sessionStorage.getItem('access_token');
        if (this._supportsSessionStorage) {
            return sessionToken || null;
        }
        return sessionToken || localStorage.getItem('access_token') || null;
    },
    
    // Get user from sessionStorage if supported, otherwise fallback to localStorage
    get user() {
        try {
            const userStr = sessionStorage.getItem('auth_user');
            if (this._supportsSessionStorage) {
                return JSON.parse(userStr || 'null');
            }
            return JSON.parse(userStr || localStorage.getItem('auth_user') || 'null');
        } catch {
            return null;
        }
    },
    
    /**
     * Wait for auth system to be ready (token validated, user switch handled)
     * Call this from other pages before loading user data
     */
    async waitForReady() {
        if (!this._authReadyPromise) {
            this._authReadyPromise = new Promise(resolve => {
                this._authReadyResolve = resolve;
            });
        }
        return this._authReadyPromise;
    },
    
    /**
     * Login user
     */
    async login(email, password) {
        try {
            console.log('🔐 Login attempt:', email);
            console.log('🔐 Using API URL:', this._getApiUrl());
            
            const apiUrl = this._getApiUrl();
            const response = await fetch(`${apiUrl}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                console.error('❌ Login failed:', response.status, data);
                throw new Error(data.error || `Login failed (${response.status})`);
            }
            
            console.log('✅ Login response:', data);
            
            // ✅ Save token using JWT interceptor (mobile-safe)
            if (typeof JWTInterceptor !== 'undefined') {
                console.log('💾 Using JWTInterceptor for token storage');
                JWTInterceptor.setToken(
                    data.access_token,
                    data.refresh_token || null,
                    data.expires_in || 3600
                );
            } else {
                console.log('💾 Using AuthSystem for token storage (fallback)');
            }
            
            // ✅ Save token and user
            this.setAuth(data.access_token, data.user);
            console.log('✅ Login successful for:', data.user.name);
            
            // Verify token was saved
            setTimeout(() => {
                const savedToken = (typeof getAuthToken === 'function' ? getAuthToken() : null) || sessionStorage.getItem('access_token');
                console.log('✅ Token saved:', savedToken ? 'YES' : 'NO');
            }, 100);
            
            // Hide modal immediately
            const modal = document.getElementById('auth-modal');
            if (modal) modal.classList.add('hidden');
            
            if (typeof showNotification === 'function') {
                showNotification(`✅ Welcome, ${data.user.name}!`, 'success');
            }
            
            // Update UI without reloading the page
            await this.updateUserInfo();
            this.updateAuthButtons();
            if (typeof checkAdminStatus !== 'undefined') {
                checkAdminStatus();
            }
            
            // Trigger a custom event that other scripts can listen to
            window.dispatchEvent(new CustomEvent('userLoggedIn', { detail: data.user }));
            
        } catch (error) {
            console.error('❌ Login error:', error);
            if (typeof showNotification === 'function') {
                showNotification(`❌ ${error.message}`, 'error');
            }
        }
    },
    
    /**
     * Register new user
     */
    async register(name, email, password, confirmPassword) {
        // Validate
        if (password !== confirmPassword) {
            showNotification?.('❌ Passwords do not match', 'error') || alert('Passwords do not match');
            return;
        }
        if (password.length < 6) {
            showNotification?.('❌ Password must be at least 6 characters', 'error') || alert('Password too short');
            return;
        }
        if (name.length < 2) {
            showNotification?.('❌ Name must be at least 2 characters', 'error') || alert('Name too short');
            return;
        }
        
        try {
            console.log('📝 Registration attempt:', email);
            
            const apiUrl = this._getApiUrl();
            const response = await fetch(`${apiUrl}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                console.error('❌ Registration failed:', response.status, data.error);
                throw new Error(data.error || 'Registration failed');
            }
            
            // ✅ Save token and user
            this.setAuth(data.access_token, data.user);
            console.log('✅ Registration successful:', data.user.name);
            
            // Hide modal - DON'T reload page, just update UI
            const modal = document.getElementById('auth-modal');
            if (modal) modal.classList.add('hidden');
            
            if (typeof showNotification === 'function') {
                showNotification(`✅ Account created! Welcome, ${data.user.name}!`, 'success');
            }
            
            // Update UI without reloading
            await this.updateUserInfo();
            this.updateAuthButtons();
            if (typeof checkAdminStatus !== 'undefined') {
                checkAdminStatus();
            }
            window.dispatchEvent(new CustomEvent('userLoggedIn', { detail: data.user }));
            
        } catch (error) {
            console.error('❌ Registration error:', error.message);
            if (typeof showNotification === 'function') {
                showNotification(`❌ ${error.message}`, 'error');
            }
        }
    },
    
    /**
     * Validate token with backend and verify user hasn't changed
     * Prevents cached user data from showing wrong account
     */
    async validateTokenWithBackend() {
        const token = this.token;
        if (!token) return false;
        
        try {
            const apiUrl = this._getApiUrl();
            const response = await fetch(`${apiUrl}/auth/verify`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                console.warn('⚠️ Token validation failed:', response.status);
                this.clearAuth();
                return false;
            }
            
            const data = await response.json();
            
            // Verify the stored user matches the token
            if (data.user) {
                const storedUser = this.user;
                if (storedUser && storedUser.email && storedUser.email !== data.user.email) {
                    console.warn('⚠️ User mismatch detected:', storedUser.email, 'vs', data.user.email);
                    // Update stored user to match token
                    this.setAuth(token, data.user);
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Token validation error:', error);
            return false;
        }
    },
    
    /**
     * Logout user
     */
    logout() {
        this.clearAuth();
        console.log('🚪 Logged out');
        if (typeof showNotification === 'function') {
            showNotification('✅ Logged out', 'success');
        }
        
        // Also clear JWTInterceptor tokens
        if (typeof JWTInterceptor !== 'undefined' && JWTInterceptor.clearTokens) {
            JWTInterceptor.clearTokens();
        }
        
        setTimeout(() => location.reload(), 500);
    },
    
    /**
     * Switch to a different account (logout and return to login)
     */
    switchAccount() {
        if (!confirm('Switch to a different account?\n\nYou will be logged out and returned to the login screen.')) {
            return;
        }
        
        console.log('🔄 Switching account...');
        this.clearAuth();
        sessionStorage.removeItem('last_user_email');
        sessionStorage.removeItem('user_switch_shown');
        
        // Also clear JWTInterceptor tokens
        if (typeof JWTInterceptor !== 'undefined' && JWTInterceptor.clearTokens) {
            JWTInterceptor.clearTokens();
        }
        
        if (typeof showNotification === 'function') {
            showNotification('Account switch initiated. Please log in with a different account.', 'info');
        }
        setTimeout(() => location.reload(), 500);
    },
    
    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.token;
    },
    
    /**
     * Get current token
     */
    getToken() {
        return this.token;
    },
    
    /**
     * Get current user
     */
    getUser() {
        return this.user;
    },
    
    /**
     * Set authentication (internal use)
     * Stores in sessionStorage for tab isolation, falling back to localStorage only if needed.
     */
    setAuth(token, user) {
        try {
            sessionStorage.setItem('access_token', token);
            sessionStorage.setItem('auth_user', JSON.stringify(user));
            sessionStorage.removeItem('refresh_token');
            sessionStorage.removeItem('token_expiry');
            localStorage.removeItem('access_token');
            localStorage.removeItem('auth_user');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('token_expiry');
            console.log('💾 Auth saved to sessionStorage');
        } catch (error) {
            console.warn('⚠️ sessionStorage unavailable, falling back to localStorage:', error.message);
            localStorage.setItem('access_token', token);
            localStorage.setItem('auth_user', JSON.stringify(user));
            console.log('💾 Auth saved to localStorage fallback');
        }
        console.log(`👤 User: ${user.name} (${user.email})`);
    },
    
    /**
     * Clear authentication (internal use)
     * Removes all user data from sessionStorage and localStorage
     */
    clearAuth() {
        // Clear both storages
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('auth_user');
        sessionStorage.removeItem('refresh_token');
        sessionStorage.removeItem('token_expiry');
        sessionStorage.removeItem('last_user_email');
        sessionStorage.removeItem('user_switch_shown');
        
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('token_expiry');
        localStorage.removeItem('auth_user');
        localStorage.removeItem('last_user_email');
        localStorage.removeItem('user_switch_shown');
        
        // Clear UI
        const userInfo = document.getElementById('user-info');
        const userName = document.getElementById('user-name');
        const userInfoMobile = document.getElementById('user-info-mobile');
        const userNameMobile = document.getElementById('user-name-mobile');
        if (userInfo) userInfo.classList.add('hidden');
        if (userName) userName.textContent = '';
        if (userInfoMobile) userInfoMobile.classList.add('hidden');
        if (userNameMobile) userNameMobile.textContent = '';
        
        // Reset login fields so the next login attempt is fresh
        const loginEmail = document.getElementById('login-email');
        const loginPassword = document.getElementById('login-password');
        if (loginEmail) loginEmail.value = '';
        if (loginPassword) loginPassword.value = '';
        
        if (typeof JWTInterceptor !== 'undefined' && JWTInterceptor.clearTokens) {
            JWTInterceptor.clearTokens();
        }
        
        console.log('🗑️ This tab\'s session cleared (other tabs unaffected)');
        this.updateAuthButtons();
    },

    /**
     * Update auth button visibility based on login state
     */
    updateAuthButtons() {
        const loginBtn = document.getElementById('login-btn');
        const logoutBtn = document.getElementById('logout-btn');
        const switchBtn = document.getElementById('switch-btn');
        const loginBtnMobile = document.getElementById('login-btn-mobile');
        const logoutBtnMobile = document.getElementById('logout-btn-mobile');
        const switchBtnMobile = document.getElementById('switch-btn-mobile');
        const userInfo = document.getElementById('user-info');

        const isLoggedIn = this.isAuthenticated();

        if (loginBtn) {
            loginBtn.classList.toggle('hidden', isLoggedIn);
        }
        if (loginBtnMobile) {
            loginBtnMobile.classList.toggle('hidden', isLoggedIn);
        }
        if (logoutBtn) {
            logoutBtn.classList.toggle('hidden', !isLoggedIn);
        }
        if (logoutBtnMobile) {
            logoutBtnMobile.classList.toggle('hidden', !isLoggedIn);
        }
        if (switchBtn) {
            switchBtn.classList.toggle('hidden', !isLoggedIn);
        }
        if (switchBtnMobile) {
            switchBtnMobile.classList.toggle('hidden', !isLoggedIn);
        }
        const adminBtn = document.getElementById('admin-btn');
        const adminBtnMobile = document.getElementById('admin-btn-mobile');
        const isAdmin = isLoggedIn && this.user && this.user.is_admin;
        if (adminBtn) {
            adminBtn.classList.toggle('hidden', !isAdmin);
        }
        if (adminBtnMobile) {
            adminBtnMobile.classList.toggle('hidden', !isAdmin);
        }

        if (userInfo && !isLoggedIn) {
            userInfo.classList.add('hidden');
        }
    },

    /**
     * Show authentication modal and switch to login tab
     */
    showAuthModal() {
        const authModal = document.getElementById('auth-modal');
        if (!authModal) return;
        authModal.classList.remove('hidden');
        this.showLoginTab();
    },

    /**
     * Show the login tab in the auth modal
     */
    showLoginTab() {
        const loginTab = document.getElementById('login-tab');
        const registerTab = document.getElementById('register-tab');
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        if (!loginTab || !registerTab || !loginForm || !registerForm) return;
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        loginTab.classList.add('border-b-2', 'border-green-500', 'text-white');
        loginTab.classList.remove('text-gray-400');
        registerTab.classList.remove('border-b-2', 'border-green-500', 'text-white');
        registerTab.classList.add('text-gray-400');
    },
    
    /**
     * Update user info in navbar
     */
    async updateUserInfo() {
        const userInfo = document.getElementById('user-info');
        const userName = document.getElementById('user-name');
        const tokenUsage = document.getElementById('token-usage');
        
        if (!userInfo || !userName) return;
        
        if (this.user && this.user.name) {
            userName.textContent = this.user.name;
            userInfo.classList.remove('hidden');
            
            // Fetch and display token usage
            await this.updateTokenUsage();
            
            // Also update mobile version if function exists
            if (typeof updateMobileUserInfo !== 'undefined') {
                updateMobileUserInfo(this.user.name);
            }

            const userNameMobile = document.getElementById('user-name-mobile');
            if (userNameMobile) {
                userNameMobile.textContent = this.user.name;
            }

            // Sync mobile token usage display after token usage refresh
            const tokenUsageMobile = document.getElementById('token-usage-mobile');
            if (tokenUsageMobile) {
                tokenUsageMobile.textContent = document.getElementById('token-usage')?.textContent || '';
            }
            console.log('👤 User info updated:', this.user.name);
        } else {
            userInfo.classList.add('hidden');
        }
    },
    
    /**
     * Update token usage display
     */
    async updateTokenUsage() {
        const tokenUsage = document.getElementById('token-usage');
        if (!tokenUsage) return;
        
        try {
            const token = this.token;
            if (!token) return;
            
            const response = await fetch(APIConfig.buildUrl('/api/user'), {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.token_usage) {
                    const { tokens_used_today, tokens_limit, tokens_remaining, plan } = data.token_usage;
                    
                    if (plan === 'enterprise') {
                        tokenUsage.textContent = '∞ Unlimited';
                        tokenUsage.className = 'ml-2 px-2 py-0.5 bg-purple-900 text-purple-300 rounded text-xs';
                    } else if (tokens_limit > 0) {
                        tokenUsage.textContent = `${tokens_remaining}/${tokens_limit} tokens`;
                        
                        // Color based on usage
                        const percentage = (tokens_used_today / tokens_limit) * 100;
                        if (percentage >= 90) {
                            tokenUsage.className = 'ml-2 px-2 py-0.5 bg-red-900 text-red-300 rounded text-xs';
                        } else if (percentage >= 70) {
                            tokenUsage.className = 'ml-2 px-2 py-0.5 bg-yellow-900 text-yellow-300 rounded text-xs';
                        } else {
                            tokenUsage.className = 'ml-2 px-2 py-0.5 bg-green-900 text-green-300 rounded text-xs';
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error fetching token usage:', error);
        }
    }
};

/**
 * Initialize authentication UI on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 DOM Content Loaded - Initializing Auth UI');
    console.log('📑 Multi-tab mode: Each tab has independent sessionStorage');
    
    // Setup tab switching
    const setupTabSwitching = () => {
        const loginTab = document.getElementById('login-tab');
        const registerTab = document.getElementById('register-tab');
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        
        if (!loginTab || !registerTab) return;
        
        loginTab.addEventListener('click', () => {
            loginForm?.classList.remove('hidden');
            registerForm?.classList.add('hidden');
            loginTab.classList.add('border-b-2', 'border-green-500', 'text-white');
            loginTab.classList.remove('text-gray-400');
            registerTab.classList.remove('border-b-2', 'border-green-500', 'text-white');
            registerTab.classList.add('text-gray-400');
        });
        
        registerTab.addEventListener('click', () => {
            registerForm?.classList.remove('hidden');
            loginForm?.classList.add('hidden');
            registerTab.classList.add('border-b-2', 'border-green-500', 'text-white');
            registerTab.classList.remove('text-gray-400');
            loginTab.classList.remove('border-b-2', 'border-green-500', 'text-white');
            loginTab.classList.add('text-gray-400');
        });
    };
    
    // Setup form submissions
    const setupFormSubmissions = () => {
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const email = document.getElementById('login-email').value;
                const password = document.getElementById('login-password').value;
                AuthSystem.login(email, password);
            });
        }
        
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const name = document.getElementById('register-name').value;
                const email = document.getElementById('register-email').value;
                const password = document.getElementById('register-password').value;
                const confirm = document.getElementById('register-confirm').value;
                AuthSystem.register(name, email, password, confirm);
            });
        }
    };
    
    // Check authentication status in THIS TAB (sessionStorage is per-tab)
    const checkAuthStatus = async () => {
        const authModal = document.getElementById('auth-modal');
        
        // Check sessionStorage for THIS TAB's session (not shared with other tabs)
        let sessionToken = sessionStorage.getItem('access_token');
        let sessionUser = sessionStorage.getItem('auth_user');
        console.log('🔍 This tab - Token:', sessionToken ? 'exists (tab-isolated)' : 'null');
        console.log('🔍 This tab - User:', sessionUser ? 'exists (tab-isolated)' : 'null');
        
        // If no session token, check if JWTInterceptor has valid tokens (from previous login)
        if (!sessionToken && typeof JWTInterceptor !== 'undefined') {
            const jwtToken = JWTInterceptor.getToken();
            if (jwtToken && !JWTInterceptor.isTokenExpired()) {
                console.log('🔄 Found valid JWT token, restoring session...');
                
                // Try to validate the JWT token with backend
                try {
                    const apiUrl = AuthSystem._getApiUrl();
                    const response = await fetch(`${apiUrl}/auth/verify`, {
                        method: 'GET',
                        headers: {
                            'Authorization': `Bearer ${jwtToken}`,
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        if (data.user) {
                            console.log('✅ JWT token validated, restoring user session');
                            // Restore the session with the validated user
                            AuthSystem.setAuth(jwtToken, data.user);
                            sessionToken = jwtToken;
                            sessionUser = JSON.stringify(data.user);
                        }
                    } else {
                        console.warn('⚠️ JWT token invalid, clearing...');
                        JWTInterceptor.clearTokens();
                    }
                } catch (error) {
                    console.error('❌ Error validating JWT token:', error);
                    JWTInterceptor.clearTokens();
                }
            }
        }
        
        if (AuthSystem.isAuthenticated()) {
            console.log('✅ Session found in this tab, validating with backend...');
            
            // Validate token with backend BEFORE showing UI
            const isValid = await AuthSystem.validateTokenWithBackend();
            
            if (!isValid) {
                console.warn('⚠️ Token validation failed - showing login modal');
                AuthSystem.showAuthModal();
                if (AuthSystem._authReadyResolve) {
                    AuthSystem._authReadyResolve();
                }
                return;
            }
            
            console.log('✅ Token validated, user:', AuthSystem.user?.name);
            
            if (authModal) authModal.classList.add('hidden');
            await AuthSystem.updateUserInfo();
            if (typeof checkAdminStatus !== 'undefined') {
                checkAdminStatus();
            }
        } else {
            console.log('⚠️ No session in this tab - showing login modal');
            console.log('💡 You can login with a different account in each tab');
            AuthSystem.showAuthModal();
        }
        
        // Auth check complete - notify listeners (e.g., dashboard.js)
        if (AuthSystem._authReadyResolve) {
            AuthSystem._authReadyResolve();
        }
    };
    
    // Initialize - use async IIFE for proper async handling
    (async () => {
        setupTabSwitching();
        setupFormSubmissions();
        if (typeof AuthSystem !== 'undefined' && AuthSystem.updateAuthButtons) {
            AuthSystem.updateAuthButtons();
        }
        await checkAuthStatus();
    })();
});

console.log('✅ auth.js loaded successfully');
