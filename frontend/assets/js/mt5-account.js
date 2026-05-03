/**
 * MT5 Account Data Manager
 * Handles fetching and displaying live MetaTrader 5 account information
 */

const MT5AccountManager = {
    refreshInterval: null,
    autoRefreshEnabled: true,
    refreshRate: 5000, // 5 seconds
    
    /**
     * Initialize MT5 account manager
     */
    init() {
        console.log('🔄 Initializing MT5 Account Manager');
        
        // Load account data on init
        this.loadAccountData();
        
        // Start auto-refresh
        this.startAutoRefresh();
    },
    
    /**
     * Load MT5 account data from API
     */
    async loadAccountData() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                console.warn('⚠️ No auth token - skipping MT5 account load');
                this.displayDisconnected('Please login first');
                return;
            }
            
            console.log('📡 Fetching MT5 account data (isolated)...');
            
            // Use isolated endpoint
            const response = await fetch(APIConfig.buildUrl('/api/mt5/account'), {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            console.log(`Response status: ${response.status}, OK: ${response.ok}`);
            
            // Parse JSON regardless of status
            let data = {};
            try {
                data = await response.json();
                console.log('Parsed response data:', data);
            } catch (parseError) {
                console.error('Failed to parse JSON response:', parseError);
                data = { message: 'Invalid response format' };
            }
            
            // Handle error responses
            if (!response.ok) {
                // Handle specific error codes
                if (response.status === 400) {
                    // 400 means MT5 not connected
                    const msg = data.message || 'MT5 account not connected. Please connect your account.';
                    console.warn('⚠️ MT5 not connected:', msg);
                    this.displayDisconnected(msg);
                } else if (response.status === 401) {
                    // 401 means not authenticated
                    console.warn('⚠️ Not authenticated');
                    this.displayDisconnected('Please login to your account');
                } else if (response.status === 403) {
                    // 403 means forbidden
                    console.warn('⚠️ Access denied');
                    this.displayDisconnected('Access denied');
                } else {
                    // Generic error
                    const msg = data.message || `API error: ${response.status}`;
                    console.warn('⚠️ API error:', msg);
                    this.displayDisconnected(msg);
                }
                return;
            }
            
            // Handle successful response
            if (data.success && data.account) {
                console.log('✅ MT5 account data received:', data.account);
                this.displayAccountInfo(data.account);
            } else {
                const msg = data.message || 'MT5 account not connected';
                console.warn('⚠️ MT5 not connected:', msg);
                this.displayDisconnected(msg);
            }
            
            // Note: health endpoint is not present in the backend yet
            
        } catch (error) {
            console.error('❌ Unexpected error loading MT5 account data:', error);
            this.displayDisconnected('Failed to load account data. Please try again.');
        }
    },
    
    /**
     * Display account information in the UI
     */
    displayAccountInfo(accountData) {
        // Update connection status
        const statusIndicator = document.getElementById('mt5-status-indicator');
        const statusText = document.getElementById('mt5-status-text');
        
        if (accountData.connected) {
            statusIndicator.className = 'w-3 h-3 rounded-full bg-green-500 animate-pulse';
            statusText.textContent = `🟢 Connected - Account ${accountData.login}`;
            statusText.className = 'font-semibold text-green-400';
        } else {
            statusIndicator.className = 'w-3 h-3 rounded-full bg-red-500';
            statusText.textContent = '🔴 ' + (accountData.message || 'Disconnected');
            statusText.className = 'font-semibold text-red-400';
            return; // Don't update other fields if disconnected
        }
        
        // Update balance
        const balance = accountData.balance !== undefined ? accountData.balance : null;
        if (balance !== null) {
            document.getElementById('mt5-balance').textContent = 
                `${balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            document.getElementById('mt5-balance-currency').textContent = accountData.currency || 'USD';
        }
        
        // Update equity and P/L
        const equity = accountData.equity !== undefined ? accountData.equity : null;
        const profitLoss = accountData.profit_loss !== undefined ? accountData.profit_loss : 0;
        if (equity !== null) {
            document.getElementById('mt5-equity').textContent = 
                `${equity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            
            const profitLossText = profitLoss >= 0 ? 
                `📈 +${profitLoss.toFixed(2)}` : 
                `📉 ${profitLoss.toFixed(2)}`;
            document.getElementById('mt5-equity-change').textContent = profitLossText;
        }
        
        // Update margin
        const margin = accountData.margin || 0;
        const freMargin = accountData.free_margin || 0;
        const totalMargin = margin + freMargin;
        
        document.getElementById('mt5-margin').textContent = 
            `${margin.toFixed(2)} / ${freMargin.toFixed(2)}`;
        
        // Update margin bar
        if (totalMargin > 0) {
            const marginPercentage = (margin / totalMargin) * 100;
            const marginBar = document.getElementById('mt5-margin-bar');
            marginBar.style.width = `${marginPercentage}%`;
        }
        
        // Update margin level
        const marginLevel = accountData.margin_level || 0;
        const marginLevelEl = document.getElementById('mt5-margin-level');
        const marginLevelStatus = document.getElementById('mt5-margin-level-status');
        
        // Handle case when margin_level is 0 (no open positions)
        if (marginLevel === 0) {
            marginLevelEl.textContent = 'N/A';
            marginLevelEl.className = 'text-2xl font-bold text-blue-400';
            marginLevelStatus.textContent = '📊 No open positions';
            marginLevelStatus.className = 'text-xs text-blue-400';
        } else {
            marginLevelEl.textContent = `${marginLevel.toFixed(2)}%`;
            marginLevelEl.className = 'text-2xl font-bold';
            
            if (marginLevel < 100) {
                marginLevelEl.classList.add('text-red-400');
                marginLevelStatus.textContent = '🚨 CRITICAL - Margin call imminent!';
                marginLevelStatus.className = 'text-xs text-red-400';
            } else if (marginLevel < 300) {
                marginLevelEl.classList.add('text-orange-400');
                marginLevelStatus.textContent = '⚠️ WARNING - Low margin level';
                marginLevelStatus.className = 'text-xs text-orange-400';
            } else if (marginLevel < 1000) {
                marginLevelEl.classList.add('text-yellow-400');
                marginLevelStatus.textContent = '⏱️ Caution - Monitor margin';
                marginLevelStatus.className = 'text-xs text-yellow-400';
            } else {
                marginLevelEl.classList.add('text-green-400');
                marginLevelStatus.textContent = '✅ Good';
                marginLevelStatus.className = 'text-xs text-green-400';
            }
        }
        
        // Update leverage
        document.getElementById('mt5-leverage').textContent = `1:${accountData.leverage || '--'}`;
        
        // Update account type
        const accountType = accountData.trade_mode === 'demo' ? '📋 DEMO' : '💰 LIVE';
        document.getElementById('mt5-account-type').textContent = accountType;
        document.getElementById('mt5-account-type').className = 
            accountData.trade_mode === 'demo' ? 'text-xl font-bold text-blue-400' : 'text-xl font-bold text-red-400';
        
        // Update account login
        document.getElementById('mt5-account-login').textContent = accountData.login || '--';
        
        // Update server
        document.getElementById('mt5-server').textContent = accountData.server || '--';
        
        // Update last update time
        const lastUpdate = new Date(accountData.timestamp);
        document.getElementById('mt5-last-update').textContent = 
            lastUpdate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    },
    
    /**
     * Display disconnected status
     */
    displayDisconnected(message) {
        const statusIndicator = document.getElementById('mt5-status-indicator');
        const statusText = document.getElementById('mt5-status-text');
        
        statusIndicator.className = 'w-3 h-3 rounded-full bg-red-500';
        statusText.textContent = '🔴 ' + (message || 'Disconnected');
        statusText.className = 'font-semibold text-red-400';
        
        // Clear account details
        const placeholders = [
            'mt5-balance', 'mt5-equity', 'mt5-margin', 'mt5-margin-level',
            'mt5-leverage', 'mt5-account-type', 'mt5-account-login', 'mt5-server'
        ];
        
        placeholders.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '--';
        });
        
        document.getElementById('mt5-warnings-container').innerHTML = `
            <div class="text-sm text-red-400">
                <i class="fas fa-plug"></i> MT5 terminal not connected
            </div>
        `;
    },
    
    /**
     * Display error message
     */
    displayError(message) {
        const statusText = document.getElementById('mt5-status-text');
        statusText.textContent = '⚠️ Error: ' + message;
        statusText.className = 'font-semibold text-red-400';
    },
    
    /**
     * Start auto-refresh of account data
     */
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            if (this.autoRefreshEnabled && localStorage.getItem('access_token')) {
                this.loadAccountData();
            }
        }, this.refreshRate);
        
        console.log(`🔄 MT5 auto-refresh started (${this.refreshRate}ms interval)`);
    },
    
    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        console.log('⏸️ MT5 auto-refresh stopped');
    },
    
    /**
     * Manually refresh account data
     */
    async manualRefresh() {
        console.log('🔄 Manual MT5 account refresh');
        await this.loadAccountData();
    }
};

/**
 * Load MT5 account data (called from HTML button)
 */
async function loadMT5Account() {
    await MT5AccountManager.manualRefresh();
}

/**
 * Initialize MT5 account manager when dashboard loads
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize after a short delay to ensure auth is ready
    setTimeout(() => {
        if (typeof AuthSystem !== 'undefined' && AuthSystem.isAuthenticated()) {
            MT5AccountManager.init();
        }
    }, 500);
});
