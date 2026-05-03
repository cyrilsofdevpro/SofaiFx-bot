/**
 * API Key Management System
 * Handles displaying, hiding, copying, and regenerating user API keys
 */

class APIKeyManager {
    constructor() {
        this.userInfo = null;
        this.isApiKeyVisible = false;
        this.isSaving = false;
    }

    /**
     * Initialize the API key manager
     */
    async init() {
        try {
            console.log('🔄 API Key Manager starting...');
            console.log('📦 localStorage keys:', Object.keys(localStorage));
            
            // Check if user is authenticated (try both key names for compatibility)
            const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
            console.log('🔑 Token found:', !!token);
            console.log('🔑 Token value (first 20 chars):', token ? token.substring(0, 20) + '...' : 'null');
            
            if (!token) {
                console.log('ℹ️ No authentication token found - user not logged in yet');
                this.showUnauthenticatedState();
                return;
            }
            
            // Show loading state
            this.showLoadingState();
            
            // Load user information
            console.log('📡 About to load user info...');
            await this.loadUserInfo();
            
            console.log('👤 User info object:', this.userInfo);
            
            if (!this.userInfo) {
                console.warn('⚠️ User info not loaded, showing error');
                this.showErrorState('Failed to load user information');
                return;
            }
            
            console.log('✏️ Rendering API key section...');
            // Render the API key section
            this.renderAPIKeySection();
            
            // Attach event listeners
            this.attachEventListeners();
            
            console.log('✅ API Key Manager initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing API Key Manager:', error);
            this.showErrorState(error.message);
        }
    }

    /**
     * Show unauthenticated state
     */
    showUnauthenticatedState() {
        const container = document.getElementById('api-key-section');
        if (!container) return;

        container.innerHTML = `
            <div class="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-lg">
                <div class="flex items-center gap-3 text-gray-400">
                    <i class="fas fa-lock text-lg"></i>
                    <p>Please log in to view your API Key</p>
                </div>
            </div>
        `;
    }

    /**
     * Show loading state
     */
    showLoadingState() {
        const container = document.getElementById('api-key-section');
        if (!container) {
            console.error('❌ Container #api-key-section not found!');
            return;
        }

        container.innerHTML = `
            <div class="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-lg">
                <div class="flex items-center gap-3">
                    <i class="fas fa-spinner animate-spin text-blue-400 text-xl"></i>
                    <p class="text-gray-300">Loading API Key...</p>
                </div>
            </div>
        `;
    }

    /**
     * Show error state
     */
    showErrorState(message) {
        const container = document.getElementById('api-key-section');
        if (!container) return;

        container.innerHTML = `
            <div class="bg-slate-800 border border-red-700 rounded-lg p-6 shadow-lg">
                <div class="flex items-center gap-3 text-red-400">
                    <i class="fas fa-exclamation-circle text-xl"></i>
                    <div>
                        <p class="font-semibold">API Key Error</p>
                        <p class="text-sm text-red-300 mt-1">${message}</p>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Load current user information from API
     */
    async loadUserInfo() {
        try {
            // Try both key names for compatibility
            const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
            if (!token) {
                throw new Error('Authentication token not found in session');
            }

            console.log('📡 Fetching user info from API...');
            console.log('🌐 URL: http://localhost:5000/api/user');
            console.log('🔐 Token:', token.substring(0, 20) + '...');
            
            const response = await fetch('http://localhost:5000/api/user', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            console.log('📊 API Response status:', response.status);
            console.log('📊 API Response ok:', response.ok);

            if (!response.ok) {
                const errorData = await response.json();
                console.error('❌ API Error data:', errorData);
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }

            this.userInfo = await response.json();
            console.log('✅ User info loaded successfully');
            console.log('✅ User email:', this.userInfo.email);
            console.log('✅ User has API key:', !!this.userInfo.api_key);
        } catch (error) {
            console.error('❌ Error loading user info:', error.message);
            throw error;
        }
    }

    /**
     * Render the API key section in the dashboard
     */
    renderAPIKeySection() {
        const container = document.getElementById('api-key-section');
        if (!container) {
            console.error('❌ Container #api-key-section not found!');
            return;
        }

        // If no user info, show appropriate message
        if (!this.userInfo) {
            container.innerHTML = `
                <div class="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-lg">
                    <div class="flex items-center gap-3 text-gray-400">
                        <i class="fas fa-lock text-lg"></i>
                        <p>Please log in to view your API Key</p>
                    </div>
                </div>
            `;
            return;
        }

        const apiKeyDisplay = this.userInfo.api_key ? 
            this.maskAPIKey(this.userInfo.api_key) : 
            'Not generated';

        const createdDate = new Date(this.userInfo.api_key_created_at).toLocaleDateString();
        const lastUsed = this.userInfo.api_key_last_used ? 
            new Date(this.userInfo.api_key_last_used).toLocaleString() : 
            'Never used';

        container.innerHTML = `
            <div class="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-lg">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-3">
                        <i class="fas fa-key text-blue-400 text-xl"></i>
                        <h3 class="text-xl font-bold text-white">API Key</h3>
                    </div>
                    <span class="px-3 py-1 bg-blue-500/20 border border-blue-500/50 rounded-full text-xs text-blue-300 font-medium">
                        <i class="fas fa-check-circle mr-1"></i>Active
                    </span>
                </div>

                <!-- API Key Display -->
                <div class="bg-slate-900 border border-slate-700 rounded-lg p-4 mb-4">
                    <div class="flex items-center justify-between mb-2">
                        <label class="text-sm text-gray-400 font-medium">Your API Key</label>
                        <button id="toggle-api-key-btn" class="text-sm text-blue-400 hover:text-blue-300 transition flex items-center gap-2">
                            <i id="toggle-api-key-icon" class="fas fa-eye"></i>
                            <span id="toggle-api-key-text">Show</span>
                        </button>
                    </div>
                    
                    <div class="flex items-center gap-2">
                        <input 
                            type="password" 
                            id="api-key-input" 
                            value="${this.userInfo.api_key}" 
                            readonly 
                            class="flex-1 px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-white font-mono text-sm focus:outline-none"
                            style="letter-spacing: 2px;"
                        >
                        <button id="copy-api-key-btn" class="px-4 py-3 bg-green-600 hover:bg-green-500 text-white font-semibold rounded-lg transition flex items-center gap-2 whitespace-nowrap">
                            <i class="fas fa-copy"></i>
                            <span>Copy</span>
                        </button>
                    </div>
                    <p id="copy-success-msg" class="text-xs text-green-400 mt-2 hidden">
                        <i class="fas fa-check mr-1"></i>Copied to clipboard!
                    </p>
                </div>

                <!-- API Key Metadata -->
                <div class="grid grid-cols-2 gap-4 mb-6">
                    <div class="bg-slate-900 rounded-lg p-3 border border-slate-700">
                        <p class="text-xs text-gray-400 font-medium mb-1">Created</p>
                        <p class="text-sm text-white font-semibold">${createdDate}</p>
                    </div>
                    <div class="bg-slate-900 rounded-lg p-3 border border-slate-700">
                        <p class="text-xs text-gray-400 font-medium mb-1">Last Used</p>
                        <p class="text-sm text-white font-semibold">${lastUsed}</p>
                    </div>
                </div>

                <!-- Security Tips -->
                <div class="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-6">
                    <div class="flex gap-3">
                        <i class="fas fa-shield-alt text-yellow-400 text-lg mt-0.5 flex-shrink-0"></i>
                        <div>
                            <h4 class="text-sm font-semibold text-yellow-300 mb-2">Security Tips</h4>
                            <ul class="text-xs text-yellow-200 space-y-1">
                                <li>✓ Never share your API key publicly</li>
                                <li>✓ Treat it like a password</li>
                                <li>✓ Regenerate if you suspect it's compromised</li>
                                <li>✓ Use only in server-to-server communication</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Regenerate Button -->
                <button id="regenerate-api-key-btn" class="w-full px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-600/50 font-semibold rounded-lg transition flex items-center justify-center gap-2">
                    <i class="fas fa-sync-alt"></i>
                    <span>Regenerate API Key</span>
                </button>
                <p class="text-xs text-gray-400 text-center mt-2">
                    ⚠️ This will invalidate your current API key
                </p>
            </div>
        `;
    }

    /**
     * Mask API key display (show only first and last 8 characters)
     */
    maskAPIKey(key) {
        if (!key || key.length < 16) return key;
        return key.substring(0, 8) + '•'.repeat(key.length - 16) + key.substring(key.length - 8);
    }

    /**
     * Attach event listeners to buttons
     */
    attachEventListeners() {
        // Toggle API key visibility
        const toggleBtn = document.getElementById('toggle-api-key-btn');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleAPIKeyVisibility());
        }

        // Copy API key to clipboard
        const copyBtn = document.getElementById('copy-api-key-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', () => this.copyAPIKey());
        }

        // Regenerate API key
        const regenerateBtn = document.getElementById('regenerate-api-key-btn');
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', () => this.showRegenerateConfirmation());
        }
    }

    /**
     * Toggle API key visibility
     */
    toggleAPIKeyVisibility() {
        const input = document.getElementById('api-key-input');
        const icon = document.getElementById('toggle-api-key-icon');
        const text = document.getElementById('toggle-api-key-text');

        if (this.isApiKeyVisible) {
            // Hide
            input.type = 'password';
            input.value = this.maskAPIKey(this.userInfo.api_key);
            icon.className = 'fas fa-eye';
            text.textContent = 'Show';
            this.isApiKeyVisible = false;
        } else {
            // Show
            input.type = 'text';
            input.value = this.userInfo.api_key;
            icon.className = 'fas fa-eye-slash';
            text.textContent = 'Hide';
            this.isApiKeyVisible = true;
        }
    }

    /**
     * Copy API key to clipboard
     */
    async copyAPIKey() {
        try {
            const key = this.userInfo.api_key;
            await navigator.clipboard.writeText(key);

            // Show success message
            const successMsg = document.getElementById('copy-success-msg');
            if (successMsg) {
                successMsg.classList.remove('hidden');
                
                // Hide after 3 seconds
                setTimeout(() => {
                    successMsg.classList.add('hidden');
                }, 3000);
            }

            console.log('✅ API key copied to clipboard');
        } catch (error) {
            console.error('Error copying to clipboard:', error);
            if (typeof showNotification === 'function') {
                showNotification('Failed to copy API key', 'error');
            }
        }
    }

    /**
     * Show confirmation dialog for regenerating API key
     */
    showRegenerateConfirmation() {
        if (confirm('⚠️ WARNING: This will invalidate your current API key!\n\nAre you sure you want to regenerate? Make sure to update any integrations using this key.')) {
            this.regenerateAPIKey();
        }
    }

    /**
     * Regenerate API key
     */
    async regenerateAPIKey() {
        if (this.isSaving) return;
        
        this.isSaving = true;
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                throw new Error('No authentication token');
            }

            const response = await fetch('http://localhost:5000/api/user/api-key/regenerate', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                
                // Update user info with new key
                this.userInfo.api_key = data.api_key;
                this.userInfo.api_key_created_at = data.api_key_created_at;
                this.userInfo.api_key_last_used = null;
                
                // Reset visibility
                this.isApiKeyVisible = false;
                
                // Re-render the section
                this.renderAPIKeySection();
                this.attachEventListeners();
                
                // Show success notification
                if (typeof showNotification === 'function') {
                    showNotification('✅ API key successfully regenerated!', 'success');
                }
                
                console.log('✅ API key regenerated successfully');
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Failed to regenerate API key');
            }
        } catch (error) {
            console.error('❌ Error regenerating API key:', error);
            if (typeof showNotification === 'function') {
                showNotification(`❌ ${error.message}`, 'error');
            }
        } finally {
            this.isSaving = false;
        }
    }
}

// Initialize API Key Manager when document is ready
let apiKeyManagerInstance = null;
let lastTokenState = null;

function initializeAPIKeyManager() {
    // Try both key names for compatibility
    const token = sessionStorage.getItem('access_token') || sessionStorage.getItem('auth_token');
    
    console.log('🔑 API Key Manager init - User authenticated:', !!token);
    
    if (!apiKeyManagerInstance) {
        apiKeyManagerInstance = new APIKeyManager();
    }
    apiKeyManagerInstance.init();
    lastTokenState = !!token;
}

// Watch for token changes (detects login/logout)
function watchForTokenChanges() {
    setInterval(() => {
        // Try both key names for compatibility
        const token = sessionStorage.getItem('access_token') || sessionStorage.getItem('auth_token');
        const currentTokenState = !!token;
        
        if (currentTokenState !== lastTokenState) {
            console.log('🔄 Token state changed - reinitializing API Key Manager');
            if (apiKeyManagerInstance) {
                apiKeyManagerInstance.init();
            }
            lastTokenState = currentTokenState;
        }
    }, 1000);
}

// Initialize immediately when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('📄 DOM Content Loaded - initializing API Key Manager');
        setTimeout(() => {
            initializeAPIKeyManager();
            watchForTokenChanges();
        }, 500);
    });
} else {
    console.log('📄 DOM already loaded - initializing API Key Manager');
    setTimeout(() => {
        initializeAPIKeyManager();
        watchForTokenChanges();
    }, 500);
}
