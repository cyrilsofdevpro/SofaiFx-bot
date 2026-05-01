/**
 * Authentication System - Multi-Tab Support
 * Each tab/window has independent session using sessionStorage
 * Allows multiple accounts to be logged in simultaneously in different tabs
 * 
 * API Configuration:
 * - Uses APIConfig for base URL
 * - Falls back to localhost:5000 if APIConfig not loaded
 * - Supports custom API URLs via setApiUrl()
 */

const AuthSystem = {
    // Get API base URL (with fallback)
    _getApiUrl() {
        if (typeof APIConfig !== 'undefined' && APIConfig.baseUrl) {
            return APIConfig.baseUrl;
        }
        return 'http://localhost:5000';
    },

    // Promise that resolves when auth initialization is complete
    _authReadyPromise: null,
    _authReadyResolve: null,
    
    // Storage strategy: check sessionStorage first (per-tab), fallback to localStorage for Edge/Safari
    // Get token from sessionStorage (per-tab) or localStorage (backup for browsers with limited sessionStorage)
    get token() {
        return sessionStorage.getItem('access_token') || localStorage.getItem('access_token') || null;
    },
    
    // Get user from sessionStorage (per-tab) or localStorage
    get user() {
        try {
            const userStr = sessionStorage.getItem('auth_user') || localStorage.getItem('auth_user');
            return JSON.parse(userStr || 'null');
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
            
            const apiUrl = this._getApiUrl();
            const response = await fetch(`${apiUrl}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                console.error('❌ Login failed:', response.status, data.error);
                throw new Error(data.error || 'Login failed');
            }
            
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
            console.log('✅ Login successful:', data.user.name);
            
            // Verify token was saved after a small delay
            setTimeout(() => {
                const savedToken = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
                console.log('✅ Token verified:', savedToken ? 'yes' : 'no');
                if (typeof JWTInterceptor !== 'undefined') {
                    JWTInterceptor.debugAuthState();
                }
            }, 200);
            
            // Hide modal immediately
            const modal = document.getElementById('auth-modal');
            if (modal) modal.classList.add('hidden');
            
            if (typeof showNotification === 'function') {
                showNotification(`✅ Welcome, ${data.user.name}!`, 'success');
            }
            
            // Update UI without reloading the page
            this.updateUserInfo();
            
            // Trigger a custom event that other scripts can listen to
            window.dispatchEvent(new CustomEvent('userLoggedIn', { detail: data.user }));
            
        } catch (error) {
            console.error('❌ Login error:', error.message);
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
            
            // Hide modal and reload
            const modal = document.getElementById('auth-modal');
            if (modal) modal.classList.add('hidden');
            
            if (typeof showNotification === 'function') {
                showNotification(`✅ Account created! Welcome, ${data.user.name}!`, 'success');
            }
            
            setTimeout(() => location.reload(), 500);
            
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
     * Stores in both sessionStorage (primary) and localStorage (fallback for Edge/privacy browsers)
     */
    setAuth(token, user) {
        // Primary: sessionStorage for tab isolation
        sessionStorage.setItem('access_token', token);
        sessionStorage.setItem('auth_user', JSON.stringify(user));
        
        // Fallback: localStorage for browsers with limited sessionStorage (Edge, Safari, etc)
        localStorage.setItem('access_token', token);
        localStorage.setItem('auth_user', JSON.stringify(user));
        
        console.log(`💾 Auth saved to sessionStorage + localStorage (Edge/Chrome compatibility)`);
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
        sessionStorage.removeItem('last_user_email');
        sessionStorage.removeItem('user_switch_shown');
        
        localStorage.removeItem('access_token');
        localStorage.removeItem('auth_user');
        localStorage.removeItem('last_user_email');
        localStorage.removeItem('user_switch_shown');
        
        // Clear UI
        const userInfo = document.getElementById('user-info');
        const userName = document.getElementById('user-name');
        const userInfoMobile = document.getElementById('user-info-mobile');
        if (userInfo) userInfo.classList.add('hidden');
        if (userName) userName.textContent = '';
        if (userInfoMobile) userInfoMobile.classList.add('hidden');
        
        console.log('🗑️ This tab\'s session cleared (other tabs unaffected)');
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
            
            // Also update mobile token usage
            const tokenUsageMobile = document.getElementById('token-usage-mobile');
            if (tokenUsageMobile && data.token_usage) {
                const { tokens_used_today, tokens_limit, tokens_remaining, plan } = data.token_usage;
                
                if (plan === 'enterprise') {
                    tokenUsageMobile.textContent = '∞';
                } else if (tokens_limit > 0) {
                    tokenUsageMobile.textContent = `${tokens_remaining}`;
                }
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
            
            const response = await fetch('http://localhost:5000/api/user', {
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
        const sessionToken = sessionStorage.getItem('access_token');
        const sessionUser = sessionStorage.getItem('auth_user');
        console.log('🔍 This tab - Token:', sessionToken ? 'exists (tab-isolated)' : 'null');
        console.log('🔍 This tab - User:', sessionUser ? 'exists (tab-isolated)' : 'null');
        
        if (AuthSystem.isAuthenticated()) {
            console.log('✅ Session found in this tab, validating with backend...');
            
            // Validate token with backend BEFORE showing UI
            const isValid = await AuthSystem.validateTokenWithBackend();
            
            if (!isValid) {
                console.warn('⚠️ Token validation failed - showing login modal');
                if (authModal) authModal.classList.remove('hidden');
                // Auth check complete
                if (AuthSystem._authReadyResolve) {
                    AuthSystem._authReadyResolve();
                }
                return;
            }
            
            console.log('✅ Token validated, user:', AuthSystem.user?.name);
            
            if (authModal) authModal.classList.add('hidden');
            AuthSystem.updateUserInfo();
        } else {
            console.log('⚠️ No session in this tab - showing login modal');
            console.log('💡 You can login with a different account in each tab');
            if (authModal) authModal.classList.remove('hidden');
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
        await checkAuthStatus();
    })();
});

console.log('✅ auth.js loaded successfully');
