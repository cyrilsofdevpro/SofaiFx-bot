/**
 * MT5 Connection Manager
 * Handles user MT5 account connection form and status
 */

const MT5ConnectionManager = {
    mt5Servers: [],
    isConnecting: false,
    connectionCheckInterval: null,
    
    /**
     * Initialize connection manager and load servers
     */
    async init() {
        console.log('🔌 Initializing MT5 Connection Manager');
        await this.loadServers();
        this.setupEventListeners();
        this.checkConnectionStatus();
        this.startConnectionStatusCheck();
    },
    
    /**
     * Load available MT5 servers with retry logic
     */
    async loadServers(retries = 5, delay = 1000) {
        for (let attempt = 1; attempt <= retries; attempt++) {
            try {
                console.log(`📡 Attempting to load MT5 servers (attempt ${attempt}/${retries})...`);
                const response = await fetch('http://localhost:5000/api/mt5/servers', {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.success && data.servers) {
                    this.mt5Servers = data.servers;
                    console.log(`✅ Loaded ${data.servers.length} MT5 servers`);
                    this.populateServerDropdown();
                    return; // Success - exit retry loop
                } else {
                    throw new Error(data.error || 'Invalid server list response');
                }
            } catch (error) {
                console.warn(`⚠️ Attempt ${attempt} failed:`, error.message);
                
                if (attempt < retries) {
                    console.log(`⏳ Retrying in ${delay}ms...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                } else {
                    console.error('❌ Failed to load servers after all retries');
                    this.displayServerLoadError();
                }
            }
        }
    },
    
    /**
     * Display error message when servers fail to load
     */
    displayServerLoadError() {
        const dropdown = document.getElementById('mt5-server-select');
        if (!dropdown) return;
        
        dropdown.innerHTML = `
            <option value="" disabled selected>⚠️ Unable to load servers</option>
            <option value="" disabled>Please refresh the page</option>
        `;
        dropdown.disabled = true;
    },
    
    /**
     * Populate server dropdown with available servers
     */
    populateServerDropdown() {
        const dropdown = document.getElementById('mt5-server-select');
        if (!dropdown) return;
        
        dropdown.innerHTML = '<option value="">Select MT5 Server...</option>';
        
        // Group by type
        const demoServers = this.mt5Servers.filter(s => s.type === 'Demo');
        const liveServers = this.mt5Servers.filter(s => s.type === 'Live');
        
        if (demoServers.length > 0) {
            const demoGroup = document.createElement('optgroup');
            demoGroup.label = 'Demo Accounts';
            demoServers.forEach(server => {
                const option = document.createElement('option');
                option.value = server.name;
                option.textContent = server.name;
                demoGroup.appendChild(option);
            });
            dropdown.appendChild(demoGroup);
        }
        
        if (liveServers.length > 0) {
            const liveGroup = document.createElement('optgroup');
            liveGroup.label = 'Live Accounts';
            liveServers.forEach(server => {
                const option = document.createElement('option');
                option.value = server.name;
                option.textContent = server.name;
                liveGroup.appendChild(option);
            });
            dropdown.appendChild(liveGroup);
        }
    },
    
    /**
     * Setup form event listeners
     */
    setupEventListeners() {
        const connectBtn = document.getElementById('mt5-connect-btn');
        const disconnectBtn = document.getElementById('mt5-disconnect-btn');
        const form = document.getElementById('mt5-connection-form');
        
        if (connectBtn) {
            connectBtn.addEventListener('click', () => this.handleConnect());
        }
        
        if (disconnectBtn) {
            disconnectBtn.addEventListener('click', () => this.handleDisconnect());
        }
        
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleConnect();
            });
        }
    },
    
    /**
     * Handle connect button click
     */
    async handleConnect() {
        const login = document.getElementById('mt5-login-input')?.value.trim();
        const password = document.getElementById('mt5-password-input')?.value.trim();
        const server = document.getElementById('mt5-server-select')?.value.trim();
        
        if (!login || !password || !server) {
            this.showError('Please fill in all fields (Login ID, Password, Server)');
            return;
        }
        
        await this.connect(login, password, server);
    },
    
    /**
     * Connect to MT5 account
     */
    async connect(login, password, server) {
        try {
            this.isConnecting = true;
            this.updateUI('connecting');
            
            const token = localStorage.getItem('access_token');
            if (!token) {
                throw new Error('Not authenticated');
            }
            
            console.log(`🔌 Storing MT5 credentials for user...`);

            // FIRST: Store credentials (encrypted in DB per user)
            const storeResponse = await fetch('http://localhost:5000/api/mt5/credentials/store', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    mt5_login: login,
                    mt5_password: password,
                    mt5_server: server
                })
            });

            const storeData = await storeResponse.json();

            if (!storeData.success) {
                throw new Error(storeData.error || 'Failed to store credentials');
            }

            console.log('✅ Credentials stored securely');

            // SECOND: Connect using stored credentials (isolated per user)
            const response = await fetch('http://localhost:5000/api/mt5/connect', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})  // No body needed - uses stored credentials
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('✅ MT5 Connected successfully');
                this.showSuccess(`Connected to MT5 Account ${data.account.login}`);
                
                // Clear form
                document.getElementById('mt5-login-input').value = '';
                document.getElementById('mt5-password-input').value = '';
                document.getElementById('mt5-server-select').value = '';
                
                // Update UI
                this.updateUI('connected');
                
                // Show account info
                this.displayAccountInfo(data.account);
                
                // Check connection status after a delay
                setTimeout(() => this.checkConnectionStatus(), 1000);
            } else {
                console.error('❌ Connection failed:', data);
                this.showError(`Connection failed: ${data.error}\n${data.details || ''}`);
                this.updateUI('disconnected');
            }
        } catch (error) {
            console.error('Connection error:', error);
            this.showError(`Connection error: ${error.message}`);
            this.updateUI('disconnected');
        } finally {
            this.isConnecting = false;
        }
    },
    
    /**
     * Handle disconnect button click
     */
    async handleDisconnect() {
        if (!confirm('Are you sure you want to disconnect your MT5 account?\nYour stored credentials will be deleted.')) {
            return;
        }
        
        await this.disconnect();
    },
    
    /**
     * Disconnect from MT5 account
     */
    async disconnect() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                throw new Error('Not authenticated');
            }
            
            console.log('🔌 Disconnecting from MT5...');
            
            const response = await fetch('http://localhost:5000/api/mt5/disconnect', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('✅ Disconnected from MT5');
                this.showSuccess('Disconnected from MT5 account');
                this.updateUI('disconnected');
                this.clearAccountInfo();
            } else {
                console.error('Disconnection failed:', data);
                this.showError(`Disconnection failed: ${data.error}`);
            }
        } catch (error) {
            console.error('Disconnection error:', error);
            this.showError(`Disconnection error: ${error.message}`);
        }
    },
    
    /**
     * Check current connection status
     */
    async checkConnectionStatus() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;
            
            const response = await fetch('http://localhost:5000/api/mt5/connection-status', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                if (data.connected) {
                    console.log('✅ Connected to MT5');
                    this.updateUI('connected');
                } else {
                    console.log('⚠️ Not connected to MT5');
                    this.updateUI('disconnected');
                }
            }
        } catch (error) {
            console.warn('Failed to check connection status:', error);
        }
    },
    
    /**
     * Start periodic connection status check
     */
    startConnectionStatusCheck() {
        if (this.connectionCheckInterval) {
            clearInterval(this.connectionCheckInterval);
        }
        
        // Check every 30 seconds
        this.connectionCheckInterval = setInterval(() => {
            this.checkConnectionStatus();
        }, 30000);
    },
    
    /**
     * Stop connection status check
     */
    stopConnectionStatusCheck() {
        if (this.connectionCheckInterval) {
            clearInterval(this.connectionCheckInterval);
            this.connectionCheckInterval = null;
        }
    },
    
    /**
     * Update UI based on connection state
     */
    updateUI(state) {
        const form = document.getElementById('mt5-connection-form');
        const status = document.getElementById('mt5-connection-status');
        const connectBtn = document.getElementById('mt5-connect-btn');
        const disconnectBtn = document.getElementById('mt5-disconnect-btn');
        const inputs = document.querySelectorAll('.mt5-form-input');
        
        if (!form || !status) return;
        
        if (state === 'connecting') {
            status.className = 'mt5-status connecting';
            status.innerHTML = '<span class="spinner"></span> 🟡 Connecting...';
            connectBtn.disabled = true;
            inputs.forEach(input => input.disabled = true);
            disconnectBtn.classList.add('hidden');
        } else if (state === 'connected') {
            status.className = 'mt5-status connected';
            status.innerHTML = '<span class="indicator green"></span> 🟢 Connected';
            connectBtn.disabled = true;
            inputs.forEach(input => input.disabled = true);
            form.classList.add('hidden');
            disconnectBtn.classList.remove('hidden');
        } else {
            status.className = 'mt5-status disconnected';
            status.innerHTML = '<span class="indicator red"></span> 🔴 Not Connected';
            connectBtn.disabled = false;
            inputs.forEach(input => input.disabled = false);
            form.classList.remove('hidden');
            disconnectBtn.classList.add('hidden');
        }
    },
    
    /**
     * Display account information
     */
    displayAccountInfo(account) {
        const container = document.getElementById('mt5-account-info');
        if (!container) return;
        
        container.innerHTML = `
            <div class="mt5-info-grid">
                <div class="mt5-info-card">
                    <span class="label">Account #</span>
                    <span class="value">${account.login}</span>
                </div>
                <div class="mt5-info-card">
                    <span class="label">Balance</span>
                    <span class="value">${account.balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${account.currency}</span>
                </div>
                <div class="mt5-info-card">
                    <span class="label">Equity</span>
                    <span class="value">${account.equity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${account.currency}</span>
                </div>
                <div class="mt5-info-card">
                    <span class="label">Margin Level</span>
                    <span class="value">${account.margin_level === 0 ? 'N/A (No positions)' : account.margin_level.toFixed(2) + '%'}</span>
                </div>
                <div class="mt5-info-card">
                    <span class="label">Leverage</span>
                    <span class="value">1:${account.leverage}</span>
                </div>
                <div class="mt5-info-card">
                    <span class="label">Account Type</span>
                    <span class="value">${account.trade_mode === 'demo' ? '📋 Demo' : '💰 Live'}</span>
                </div>
            </div>
        `;
    },
    
    /**
     * Clear account information
     */
    clearAccountInfo() {
        const container = document.getElementById('mt5-account-info');
        if (container) {
            container.innerHTML = '';
        }
    },
    
    /**
     * Show success message
     */
    showSuccess(message) {
        this.showNotification(message, 'success');
    },
    
    /**
     * Show error message
     */
    showError(message) {
        this.showNotification(message, 'error');
    },
    
    /**
     * Show notification
     */
    showNotification(message, type) {
        const container = document.getElementById('mt5-notifications');
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span>${type === 'success' ? '✅' : '❌'} ${message}</span>
                <button onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
};

/**
 * Initialize when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        if (typeof AuthSystem !== 'undefined' && AuthSystem.isAuthenticated()) {
            MT5ConnectionManager.init();
        }
    }, 500);
});

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', function() {
    MT5ConnectionManager.stopConnectionStatusCheck();
});
