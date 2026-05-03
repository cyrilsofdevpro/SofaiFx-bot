// Configuration
const API_BASE_URL = APIConfig.baseUrl;
let allSignals = [];
let signalsChart = null;
let confidenceChart = null;

// Global state for shared data
const sharedState = {
    signals: [],
    stats: null,
    lastUpdate: 0,
    isUpdating: false
};

// Polling interval IDs for cleanup
const pollingIntervals = {
    signals: null,
    status: null,
    chart: null
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadConfig();
    
    console.log('📊 Dashboard DOMContentLoaded fired');
    console.log('🔐 AuthSystem defined:', typeof AuthSystem !== 'undefined');
    
    // CRITICAL: Wait for auth system to be ready before loading user data
    // This prevents race conditions where data loads before user validation completes
    (async () => {
        if (typeof AuthSystem !== 'undefined') {
            console.log('⏳ Waiting for auth system to be ready...');
            await AuthSystem.waitForReady();
            console.log('✅ Auth system ready - proceeding with data load');
        }
        
        if (typeof AuthSystem !== 'undefined' && AuthSystem.isAuthenticated()) {
            console.log('✅ User authenticated - loading signals');
            loadSignals();
            loadSignalBreakdown();  // Load buy/sell signal counts
            // Reduce polling from 30s to 15s using lightweight endpoint + cache
            const signalInterval = dataOptimizer.getPollingInterval('signals');
            pollingIntervals.signals = setInterval(loadSignals, signalInterval);
            console.log(`📡 Signal polling set to ${signalInterval}ms`);
        } else {
            console.log('⚠️ User not authenticated - skipping signal load');
            document.getElementById('bot-status').textContent = 'Offline';
            document.getElementById('last-update').textContent = 'N/A';
        }
    })();
    
    // Use minimal health endpoint, reduce from 10s to 60s
    updateServerStatus();
    const healthInterval = dataOptimizer.getPollingInterval('health');
    pollingIntervals.status = setInterval(updateServerStatus, healthInterval);
    console.log(`❤️ Health check set to ${healthInterval}ms`);
    
    // Poll for signal breakdown every 30 seconds
    pollingIntervals.breakdown = setInterval(loadSignalBreakdown, 30000);
    console.log('📊 Signal breakdown polling set to 30000ms');
    
    // Poll for open positions every 30 seconds
    pollingIntervals.positions = setInterval(loadOpenPositions, 30000);
    console.log('📊 Position polling set to 30000ms');
    
    initCharts();
    
    // Delay trading chart initialization to ensure LightweightCharts library is loaded
    setTimeout(() => {
        lazyLoader.register('trading-chart', initTradingChart, '#trading-chart');
    }, 500);
    
    // Allow Enter key in symbol input
    document.getElementById('symbol-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') analyzeSymbol();
    });
    
    // Check if user is admin and show admin button
    checkAdminStatus();
    
    // Check trading bot status
    checkBotStatus();
    
    // Add Low Data Mode toggle button
    addLowDataModeUI();
    
    // Network monitoring is DISABLED by default (can be enabled manually)
    // To enable: toggleNetworkMonitor(true) in console
});


// Analyze specific symbol
async function analyzeSymbol() {
    const symbol = document.getElementById('symbol-input').value.toUpperCase().trim();
    
    if (!symbol) {
        alert('Please enter a symbol (e.g., EURUSD)');
        return;
    }
    
    if (symbol.length !== 6) {
        alert('Symbol must be 6 characters (e.g., EURUSD)');
        return;
    }
    
    await analyze(symbol);
    document.getElementById('symbol-input').value = '';
}

// Analyze all configured pairs
async function analyzeAll() {
    await analyze(null, true);
}

// Main analysis function
async function analyze(symbol = null, analyzeAll = false) {
    let btn = null;
    let originalText = '';
    
    try {
        // Show loading state
        btn = event?.target || document.querySelector('button');
        originalText = btn ? btn.innerHTML : '';
        if (btn) {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
            btn.disabled = true;
        }
        
        const endpoint = analyzeAll ? '/api/analyze-all' : '/api/analyze';
        const payload = analyzeAll ? { pairs: [] } : { symbol, notify: true };
        
        console.log('🔄 Analyzing:', endpoint, payload);
        console.log('📦 Token available:', !!sessionStorage.getItem('access_token'));
        console.log('📦 Token value:', sessionStorage.getItem('access_token')?.substring(0, 30) + '...');
        
        // Get token and build headers
        const token = sessionStorage.getItem('access_token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
            console.log('✓ Authorization header set:', headers['Authorization'].substring(0, 40) + '...');
        }
        
        // Make request with explicit Authorization header
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(payload)
        });
        
        console.log('📨 Response status:', response.status);
        console.log('📨 Response headers:', Array.from(response.headers.entries()));
        
        const data = await response.json();
        
        // Log response data
        console.log('📊 Response data:', data);
        
        // Handle authorization error
        if (response.status === 401) {
            console.error('🔐 Authorization failed - clearing auth');
            if (typeof AuthSystem !== 'undefined') {
                AuthSystem.clearAuth();
                const authModal = document.getElementById('auth-modal');
                if (authModal) authModal.classList.remove('hidden');
            }
            showNotification('⚠️ Session expired. Please log in again.', 'warning');
            return;
        }
        
        // Handle API rate limit error
        if (response.status === 429 || data.error === 'API_RATE_LIMIT') {
            showRateLimitWarning(data.message || 'API rate limit reached');
            return;
        }
        
        // Handle token limit reached (for free users)
        if (response.status === 403 || data.error === 'TOKEN_LIMIT_REACHED') {
            showNotification(`🚫 ${data.message || 'Daily token limit reached! Upgrade to Premium for unlimited tokens.'}`, 'error');
            // Refresh token usage display
            if (typeof AuthSystem !== 'undefined' && AuthSystem.updateTokenUsage) {
                AuthSystem.updateTokenUsage();
            }
            return;
        }
        
        if (response.ok) {
            if (analyzeAll) {
                showNotification(`✅ Analyzed ${data.analyzed} pairs`, 'success');
            } else {
                if (data.signal) {
                    showNotification(`✅ Signal for ${symbol}: ${data.signal.signal}`, 'success');
                    allSignals.unshift(data.signal);
                    
                    // Show risk management data if available
                    if (data.risk_management) {
                        displayRiskManagement(symbol, data.signal, data.risk_management);
                    }
                } else {
                    showNotification(`⚠️ No clear signal for ${symbol}`, 'warning');
                }
            }
            
            loadSignals();
            
            // Refresh token usage display after analysis
            if (typeof AuthSystem !== 'undefined' && AuthSystem.updateTokenUsage) {
                AuthSystem.updateTokenUsage();
            }
        } else {
            showNotification(`❌ Error: ${data.error}`, 'error');
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        showNotification(`❌ Connection error: ${error.message}`, 'error');
    } finally {
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }
}

// Load all signals (optimized with lightweight endpoint and caching)
async function loadSignals() {
    if (sharedState.isUpdating) {
        console.log('⏳ Signal update already in progress, skipping...');
        return;
    }

    sharedState.isUpdating = true;

    try {
        console.log('📥 Loading signals...');
        
        // Use cache with lightweight endpoint
        const signals = await dataOptimizer.getCachedOrFetch('signals', async () => {
            const token = sessionStorage.getItem('access_token');
            const limit = 20;  // Fetch only latest 20 instead of 50
            
            const headers = { 'Content-Type': 'application/json' };
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            // Use lightweight endpoint that returns minimal fields
            const endpoint = `/api/signals/latest?limit=${limit}`;
            console.log(`📡 Fetching from ${endpoint}`);
            
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'GET',
                headers: headers
            });
            
            console.log('📨 Signals response status:', response.status);
            
            if (!response.ok) {
                if (response.status === 401) {
                    console.error('⚠️ 401 Unauthorized - token invalid or missing');
                    
                    if (typeof AuthSystem !== 'undefined') {
                        console.log('🔐 Clearing invalid token and showing login...');
                        AuthSystem.clearAuth();
                        const authModal = document.getElementById('auth-modal');
                        if (authModal) authModal.classList.remove('hidden');
                        showNotification('⚠️ Session expired. Please log in again.', 'warning');
                    }
                    document.getElementById('bot-status').textContent = 'Offline';
                    return [];
                }
                throw new Error(`API error: ${response.status}`);
            }
            
            return await response.json();
        });

        if (signals && signals.signals && Array.isArray(signals.signals)) {
            allSignals = signals.signals;
            sharedState.signals = signals.signals;
            console.log('✓ Loaded', signals.signals.length, 'signals');
            
            updateSignalsDisplay();
            updateStatsFromCache();
            updateChartsOptimized();
            
            document.getElementById('bot-status').textContent = 'Active';
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
            
            // Also load open positions
            loadOpenPositions();
        }
        
    } catch (error) {
        console.error('Load signals error:', error);
        document.getElementById('bot-status').textContent = 'Error';
    } finally {
        sharedState.isUpdating = false;
    }
}

// Load signal breakdown (buy/sell counts per user)
async function loadSignalBreakdown() {
    try {
        const token = sessionStorage.getItem('access_token');
        if (!token) {
            console.log('⚠️ No token for signal breakdown');
            return;
        }

        const response = await fetch(`${API_BASE_URL}/api/stats/signals-breakdown`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            console.warn('⚠️ Signal breakdown fetch failed:', response.status);
            return;
        }

        const data = await response.json();
        console.log('📊 Signal breakdown:', data);

        // Update signal cards
        if (data.signals) {
            document.getElementById('total-signals').textContent = data.signals.total || 0;
            document.getElementById('buy-signals').textContent = data.signals.buy || 0;
            document.getElementById('sell-signals').textContent = data.signals.sell || 0;
            
            console.log(`✅ Signals Updated: Total=${data.signals.total} Buy=${data.signals.buy} Sell=${data.signals.sell}`);
        }
    } catch (error) {
        console.error('❌ Error loading signal breakdown:', error);
    }
}

// Load open positions and update display
async function loadOpenPositions() {
    const token = sessionStorage.getItem('access_token');
    if (!token) return;
    
    try {
        // Fetch execution status (includes open positions)
        const response = await fetch(`${API_BASE_URL}/api/execution/status`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.execution_status) {
                const status = data.execution_status;
                
                // Update today's P&L
                const pnlEl = document.getElementById('today-pnl');
                if (status.today_pnl !== undefined) {
                    pnlEl.textContent = `$${status.today_pnl.toFixed(2)}`;
                    pnlEl.className = status.today_pnl >= 0 ? 'text-xl font-bold text-green-400' : 'text-xl font-bold text-red-400';
                }
                
                // Update total trades
                document.getElementById('total-trades').textContent = status.today_trades_closed || 0;
                
                // Update open positions display
                const positionsContainer = document.getElementById('positions-container');
                if (status.open_trades > 0 && status.open_trade_symbols) {
                    let html = '<div class="space-y-2">';
                    status.open_trade_symbols.forEach(symbol => {
                        html += `
                            <div class="bg-slate-700 rounded-lg p-3 flex justify-between items-center">
                                <span class="font-semibold">${symbol}</span>
                                <span class="text-yellow-400">Open</span>
                            </div>
                        `;
                    });
                    html += '</div>';
                    positionsContainer.innerHTML = html;
                } else {
                    positionsContainer.innerHTML = '<div class="text-gray-400 text-sm">No open positions</div>';
                }
            }
        }
    } catch (error) {
        console.error('Error loading positions:', error);
    }
}

// Clear all signals
async function clearSignals() {
    // Confirm before clearing
    if (!confirm('⚠️ Are you sure you want to clear ALL signals? This cannot be undone!')) {
        return;
    }
    
    try {
        console.log('🗑️ Clearing all signals...');
        
        const token = sessionStorage.getItem('access_token');
        if (!token) {
            showNotification('❌ Please log in first', 'error');
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/api/signals/clear`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`✅ Cleared ${data.deleted} signals`, 'success');
            allSignals = [];
            updateSignalsDisplay();
            updateStats();
            updateCharts();
            console.log('✅ Signals cleared successfully');
        } else if (response.status === 401) {
            AuthSystem.clearAuth();
            const authModal = document.getElementById('auth-modal');
            if (authModal) authModal.classList.remove('hidden');
            showNotification('⚠️ Session expired. Please log in again.', 'warning');
        } else {
            showNotification(`❌ Error: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Clear signals error:', error);
        showNotification(`❌ Error: ${error.message}`, 'error');
    }
}

// Load configuration
async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/config`);
        const config = await response.json();
        
        const pairsList = config.currency_pairs.join(', ');
        document.getElementById('monitored-pairs').textContent = pairsList;
        
    } catch (error) {
        console.error('Load config error:', error);
        document.getElementById('monitored-pairs').textContent = 'Error loading config';
    }
}

// Update server status (optimized with minimal health endpoint)
async function updateServerStatus() {
    try {
        // Use minimal health endpoint with caching
        const health = await dataOptimizer.getCachedOrFetch('health', async () => {
            // Use minimal endpoint that requires no auth
            const response = await fetch(`${API_BASE_URL}/api/health/minimal`);
            if (!response.ok) throw new Error(`Status: ${response.status}`);
            return await response.json();
        }, 60000);  // Cache for 60 seconds

        if (health && health.status === 'ok') {
            const statusEl = document.getElementById('server-status');
            if (statusEl) {
                statusEl.innerHTML = '<span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span><span>Online</span>';
            }
        }
    } catch (error) {
        console.log('Server status unavailable');
        const statusEl = document.getElementById('server-status');
        if (statusEl) {
            statusEl.innerHTML = '<span class="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span><span>Offline</span>';
        }
    }
}

// Update signals display
function updateSignalsDisplay() {
    const container = document.getElementById('signals-container');
    const tableBody = document.getElementById('signals-table-body');
    
    if (allSignals.length === 0) {
        container.innerHTML = '<div class="text-center text-gray-400 py-8"><p>No signals yet.</p></div>';
        tableBody.innerHTML = '<tr><td colspan="6" class="px-4 py-8 text-center text-gray-400">No signals yet</td></tr>';
        return;
    }
    
    // Update feed
    container.innerHTML = allSignals.slice(0, 10).map(signal => {
        const tradeAllowed = signal.filter_results?.is_trade_allowed ?? true;
        const aiConfidence = signal.ai_prediction?.confidence ?? 0;
        const signalQuality = signal.signal_quality?.agreeing_indicators ?? 0;
        
        return `
        <div class="bg-slate-700 border border-slate-600 rounded-lg p-4 hover:border-blue-400 transition">
            <div class="flex justify-between items-start mb-2">
                <div>
                    <h3 class="font-semibold text-lg">${signal.symbol}</h3>
                    <p class="text-xs text-gray-400">${new Date(signal.timestamp).toLocaleString()}</p>
                </div>
                <div class="flex gap-2">
                    <span class="px-3 py-1 rounded-full text-sm font-bold ${
                        signal.signal === 'BUY' ? 'bg-green-900 text-green-300' :
                        signal.signal === 'SELL' ? 'bg-red-900 text-red-300' :
                        'bg-yellow-900 text-yellow-300'
                    }">
                        ${signal.signal}
                    </span>
                    <span class="px-3 py-1 rounded-full text-sm font-bold ${
                        tradeAllowed ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
                    }">
                        ${tradeAllowed ? '✓ Allow' : '✗ Block'}
                    </span>
                </div>
            </div>
            <p class="text-sm text-gray-300 mb-3">${signal.reason}</p>
            
            <div class="grid grid-cols-2 gap-3 mb-3 text-xs">
                <div class="bg-slate-600 rounded p-2">
                    <p class="text-gray-400">Confidence</p>
                    <p class="text-green-300 font-bold">${(signal.confidence * 100).toFixed(0)}%</p>
                </div>
                <div class="bg-slate-600 rounded p-2">
                    <p class="text-gray-400">AI Confidence</p>
                    <p class="text-blue-300 font-bold">${(aiConfidence * 100).toFixed(0)}%</p>
                </div>
                <div class="bg-slate-600 rounded p-2">
                    <p class="text-gray-400">Price</p>
                    <p class="text-yellow-300 font-bold">${signal.price ? signal.price.toFixed(4) : 'N/A'}</p>
                </div>
                <div class="bg-slate-600 rounded p-2">
                    <p class="text-gray-400">Indicator Agreement</p>
                    <p class="text-purple-300 font-bold">${signalQuality}/3</p>
                </div>
            </div>
            
            ${tradeAllowed ? '' : '<div class="text-xs bg-red-900 bg-opacity-50 text-red-300 px-2 py-1 rounded border border-red-700">⚠️ Trade filtered by smart filter</div>'}
        </div>
    `}).join('');
    
    // Update table
    tableBody.innerHTML = allSignals.map(signal => {
        const tradeAllowed = signal.filter_results?.is_trade_allowed ?? true;
        const aiConfidence = signal.ai_prediction?.confidence ?? 0;
        const signalQuality = signal.signal_quality?.agreeing_indicators ?? 0;
        
        return `
        <tr class="border-b border-slate-700 hover:bg-slate-700 transition">
            <td class="px-4 py-2 font-semibold">${signal.symbol}</td>
            <td class="px-4 py-2">
                <span class="px-2 py-1 rounded text-xs font-bold ${
                    signal.signal === 'BUY' ? 'bg-green-900 text-green-300' :
                    signal.signal === 'SELL' ? 'bg-red-900 text-red-300' :
                    'bg-yellow-900 text-yellow-300'
                }">
                    ${signal.signal}
                </span>
            </td>
            <td class="px-4 py-2">${signal.price ? signal.price.toFixed(4) : 'N/A'}</td>
            <td class="px-4 py-2">
                <div class="w-full bg-slate-600 rounded-full h-2">
                    <div class="bg-gradient-to-r from-blue-400 to-green-400 h-2 rounded-full" 
                         style="width: ${signal.confidence * 100}%"></div>
                </div>
                <span class="text-xs text-gray-400">${(signal.confidence * 100).toFixed(0)}%</span>
            </td>
            <td class="px-4 py-2">
                <div class="w-full bg-slate-600 rounded-full h-2">
                    <div class="bg-gradient-to-r from-purple-400 to-blue-400 h-2 rounded-full" 
                         style="width: ${aiConfidence * 100}%"></div>
                </div>
                <span class="text-xs text-gray-400">${(aiConfidence * 100).toFixed(0)}%</span>
            </td>
            <td class="px-4 py-2 text-xs">
                <span class="px-2 py-1 rounded font-bold ${
                    tradeAllowed ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
                }">
                    ${tradeAllowed ? '✓ Allow' : '✗ Block'}
                </span>
            </td>
            <td class="px-4 py-2 text-xs text-gray-400">${signalQuality}/3</td>
            <td class="px-4 py-2 text-xs text-gray-300 max-w-xs truncate">${signal.reason}</td>
            <td class="px-4 py-2 text-xs text-gray-400">${new Date(signal.timestamp).toLocaleTimeString()}</td>
        </tr>
    `}).join('');
}

// Update statistics (optimized with lightweight endpoint)
async function updateStatsFromCache() {
    try {
        const stats = await dataOptimizer.getCachedOrFetch('stats', async () => {
            const token = sessionStorage.getItem('access_token');
            const headers = { 'Content-Type': 'application/json' };
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            // Use lightweight stats endpoint
            const response = await fetch(`${API_BASE_URL}/api/stats/summary`, {
                method: 'GET',
                headers: headers
            });

            if (!response.ok) throw new Error(`API error: ${response.status}`);
            return await response.json();
        });

        // Update UI from cached stats
        if (stats) {
            document.getElementById('total-signals').textContent = stats.total || 0;
            document.getElementById('buy-signals').textContent = stats.buys || 0;
            document.getElementById('sell-signals').textContent = stats.sells || 0;
            document.getElementById('avg-confidence').textContent = 
                `${(stats.avg_confidence * 100).toFixed(0)}%`;
            console.log('✅ Stats updated from lightweight endpoint');
        }
    } catch (error) {
        console.error('Update stats error:', error);
        // Fallback: calculate from loaded signals
        updateStatsFromSignals();
    }
}

// Fallback: Update statistics from already-loaded signals
function updateStatsFromSignals() {
    const total = allSignals.length;
    const buys = allSignals.filter(s => s.signal === 'BUY').length;
    const sells = allSignals.filter(s => s.signal === 'SELL').length;
    const avgConfidence = allSignals.length > 0 
        ? (allSignals.reduce((sum, s) => sum + s.confidence, 0) / allSignals.length * 100).toFixed(0)
        : 0;
    
    document.getElementById('total-signals').textContent = total;
    document.getElementById('buy-signals').textContent = buys;
    document.getElementById('sell-signals').textContent = sells;
    document.getElementById('avg-confidence').textContent = `${avgConfidence}%`;
}

// Deprecated: Old updateStats function - now uses updateStatsFromCache
// Left for backwards compatibility
function updateStats() {
    updateStatsFromSignals();
}

// Initialize charts (with optimizer registration)
function initCharts() {
    // Signals Distribution Chart
    const signalsCtx = document.getElementById('signalsChart').getContext('2d');
    signalsChart = new Chart(signalsCtx, {
        type: 'doughnut',
        data: {
            labels: ['Buy', 'Sell', 'Hold'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(234, 179, 8, 0.8)'
                ],
                borderColor: [
                    'rgba(34, 197, 94, 1)',
                    'rgba(239, 68, 68, 1)',
                    'rgba(234, 179, 8, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#e5e7eb' } }
            }
        }
    });
    
    // Register chart with optimizer
    chartOptimizer.registerChart('signalsChart', signalsChart);
    
    // Confidence Distribution Chart
    const confidenceCtx = document.getElementById('confidenceChart').getContext('2d');
    confidenceChart = new Chart(confidenceCtx, {
        type: 'bar',
        data: {
            labels: ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'],
            datasets: [{
                label: 'Number of Signals',
                data: [0, 0, 0, 0, 0],
                backgroundColor: [
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(251, 146, 60, 0.8)',
                    'rgba(234, 179, 8, 0.8)',
                    'rgba(132, 204, 22, 0.8)',
                    'rgba(34, 197, 94, 0.8)'
                ],
                borderColor: '#1e293b',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'x',
            responsive: true,
            plugins: {
                legend: { labels: { color: '#e5e7eb' } }
            },
            scales: {
                y: { ticks: { color: '#e5e7eb' }, grid: { color: '#334155' } },
                x: { ticks: { color: '#e5e7eb' }, grid: { color: '#334155' } }
            }
        }
    });
    
    // Register chart with optimizer
    chartOptimizer.registerChart('confidenceChart', confidenceChart);
    
    console.log('✅ Charts initialized and registered with optimizer');
}

// Update charts (optimized - only updates changed data)
function updateChartsOptimized() {
    if (!signalsChart || !confidenceChart) return;
    
    const buys = allSignals.filter(s => s.signal === 'BUY').length;
    const sells = allSignals.filter(s => s.signal === 'SELL').length;
    const holds = allSignals.filter(s => s.signal === 'HOLD').length;
    
    const newSignalData = [buys, sells, holds];
    
    // Use chart optimizer to detect changes and update only if needed
    chartOptimizer.updateChart('signalsChart', newSignalData, 0);
    
    // Confidence distribution
    const confidenceBins = [0, 0, 0, 0, 0];
    allSignals.forEach(signal => {
        const conf = signal.confidence * 100;
        if (conf <= 20) confidenceBins[0]++;
        else if (conf <= 40) confidenceBins[1]++;
        else if (conf <= 60) confidenceBins[2]++;
        else if (conf <= 80) confidenceBins[3]++;
        else confidenceBins[4]++;
    });
    
    // Only update if data changed
    chartOptimizer.updateChart('confidenceChart', confidenceBins, 0);
}

// Deprecated: Old updateCharts function
// Left for backwards compatibility - now uses updateChartsOptimized
function updateCharts() {
    updateChartsOptimized();
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white ${
        type === 'success' ? 'bg-green-600' :
        type === 'error' ? 'bg-red-600' :
        type === 'warning' ? 'bg-yellow-600' :
        'bg-blue-600'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Display risk management data in a modal
function displayRiskManagement(symbol, signal, risk) {
    const signalColor = signal.signal === 'BUY' ? 'green' : signal.signal === 'SELL' ? 'red' : 'yellow';
    const signalTextColor = signal.signal === 'BUY' ? 'text-green-300' : signal.signal === 'SELL' ? 'text-red-300' : 'text-yellow-300';
    
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-slate-800 border border-slate-700 rounded-lg max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
            <div class="bg-gradient-to-r from-slate-700 to-slate-900 px-6 py-4 border-b border-slate-700 flex justify-between items-center">
                <h2 class="text-2xl font-bold flex items-center gap-2">
                    <span class="text-2xl">📊</span> ${symbol} Trading Analysis
                </h2>
                <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-white text-2xl">×</button>
            </div>
            
            <div class="p-6 space-y-6">
                <!-- Signal Summary -->
                <div class="bg-slate-700 rounded-lg p-4 border border-slate-600">
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="font-semibold text-lg">Signal</h3>
                        <span class="px-4 py-2 rounded-full text-lg font-bold bg-${signalColor}-900 ${signalTextColor}">
                            ${signal.signal}
                        </span>
                    </div>
                    <p class="text-gray-300 text-sm">${signal.reason}</p>
                    <p class="text-gray-400 text-xs mt-2">Confidence: <strong>${(signal.confidence * 100).toFixed(1)}%</strong></p>
                </div>
                
                <!-- Entry & Exit Points -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="bg-slate-700 rounded-lg p-4 border border-slate-600">
                        <p class="text-gray-400 text-sm mb-1">Entry Price</p>
                        <p class="text-2xl font-bold text-blue-400">${risk.entry_price.toFixed(5)}</p>
                    </div>
                    <div class="bg-slate-700 rounded-lg p-4 border border-red-600 border-opacity-50">
                        <p class="text-gray-400 text-sm mb-1">Stop Loss</p>
                        <p class="text-2xl font-bold text-red-400">${risk.stop_loss.toFixed(5)}</p>
                        <p class="text-xs text-red-400 mt-1">${risk.sl_pips.toFixed(1)} pips</p>
                    </div>
                    <div class="bg-slate-700 rounded-lg p-4 border border-green-600 border-opacity-50">
                        <p class="text-gray-400 text-sm mb-1">Take Profit</p>
                        <p class="text-2xl font-bold text-green-400">${risk.take_profit.toFixed(5)}</p>
                        <p class="text-xs text-green-400 mt-1">${risk.tp_pips.toFixed(1)} pips</p>
                    </div>
                </div>
                
                <!-- Position Sizing -->
                <div class="bg-slate-700 rounded-lg p-4 border border-slate-600">
                    <h3 class="font-semibold mb-3 flex items-center gap-2">
                        <i class="fas fa-calculator text-purple-400"></i> Position Sizing (${risk.risk_per_trade_percent}% Risk)
                    </h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                        <div>
                            <p class="text-gray-400">Lots</p>
                            <p class="text-lg font-bold text-purple-300">${risk.position_size.lots}</p>
                        </div>
                        <div>
                            <p class="text-gray-400">Units</p>
                            <p class="text-lg font-bold text-purple-300">${risk.position_size.units.toLocaleString()}</p>
                        </div>
                        <div>
                            <p class="text-gray-400">Risk Amount</p>
                            <p class="text-lg font-bold text-red-400">$${risk.position_size.risk_amount.toFixed(2)}</p>
                        </div>
                        <div>
                            <p class="text-gray-400">Risk Pips</p>
                            <p class="text-lg font-bold text-yellow-400">${risk.position_size.risk_pips.toFixed(1)}</p>
                        </div>
                    </div>
                </div>
                
                <!-- Risk Metrics -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-slate-700 rounded-lg p-4 border border-slate-600">
                        <p class="text-gray-400 text-sm mb-2">Risk/Reward Ratio</p>
                        <p class="text-3xl font-bold text-green-400">${risk.risk_reward_ratio}:1</p>
                        <p class="text-xs text-gray-500 mt-1">For every $1 risked, potential $${(risk.risk_reward_ratio).toFixed(2)} profit</p>
                    </div>
                    <div class="bg-slate-700 rounded-lg p-4 border border-slate-600">
                        <p class="text-gray-400 text-sm mb-2">Account Balance</p>
                        <p class="text-3xl font-bold text-blue-400">$${risk.account_balance.toLocaleString()}</p>
                        <p class="text-xs text-gray-500 mt-1">Risk per trade: $${risk.position_size.risk_amount.toFixed(2)}</p>
                    </div>
                </div>
                
                <!-- ATR Info -->
                <div class="bg-slate-700 rounded-lg p-4 border border-slate-600">
                    <p class="text-gray-400 text-sm mb-2">Volatility (ATR-14)</p>
                    <p class="text-2xl font-bold text-orange-400">${risk.atr.toFixed(6)}</p>
                    <p class="text-xs text-gray-500 mt-1">Current market volatility used for SL/TP calculations</p>
                </div>
            </div>
            
            <div class="bg-slate-700 px-6 py-4 border-t border-slate-600 flex gap-3">
                <button onclick="this.closest('.fixed').remove()" class="flex-1 px-4 py-2 bg-slate-600 hover:bg-slate-500 rounded-lg transition">
                    Close
                </button>
                <button onclick="copyToClipboard('${symbol}|${risk.entry_price.toFixed(5)}|${risk.stop_loss.toFixed(5)}|${risk.take_profit.toFixed(5)}')" class="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition">
                    Copy Details
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

// Copy risk details to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('✅ Trading details copied to clipboard!', 'success');
    });
}

// Show API rate limit warning
function showRateLimitWarning(message) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-gradient-to-br from-red-900 to-red-800 border-2 border-red-500 rounded-lg max-w-md w-full mx-4 shadow-2xl">
            <div class="px-6 py-4 border-b border-red-600">
                <h2 class="text-2xl font-bold flex items-center gap-2 text-red-200">
                    <i class="fas fa-exclamation-triangle"></i> API LIMIT REACHED
                </h2>
            </div>
            
            <div class="p-6 space-y-4">
                <div class="bg-red-800 border-l-4 border-red-400 p-4 rounded">
                    <p class="text-red-100 font-semibold mb-2">⚠️ Daily Request Limit Exceeded</p>
                    <p class="text-red-200 text-sm">
                        The free tier of Alpha Vantage API allows only <strong>25 requests per day</strong>. 
                        Your limit has been reached.
                    </p>
                </div>
                
                <div class="bg-red-700 p-4 rounded">
                    <p class="text-red-100 font-semibold mb-3">💡 What You Can Do:</p>
                    <ul class="text-red-200 text-sm space-y-2">
                        <li class="flex items-start gap-2">
                            <i class="fas fa-check text-red-300 mt-1"></i>
                            <span><strong>Use Cached Data:</strong> Analysis with cached data (from earlier today) is still available</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <i class="fas fa-check text-red-300 mt-1"></i>
                            <span><strong>Wait:</strong> The limit resets daily at 00:00 UTC</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <i class="fas fa-check text-red-300 mt-1"></i>
                            <span><strong>Upgrade:</strong> Get a <strong>Premium API Key</strong> with unlimited requests</span>
                        </li>
                    </ul>
                </div>
                
                <div class="bg-red-700 bg-opacity-50 p-4 rounded border border-red-500 border-opacity-50">
                    <p class="text-red-100 text-sm">
                        <strong>Error Details:</strong><br>
                        ${message}
                    </p>
                </div>
            </div>
            
            <div class="bg-red-800 px-6 py-4 border-t border-red-600 flex gap-3">
                <button onclick="this.closest('.fixed').remove()" class="flex-1 px-4 py-2 bg-red-700 hover:bg-red-600 text-red-100 rounded-lg transition font-semibold">
                    <i class="fas fa-times"></i> Close
                </button>
                <button onclick="location.href='https://www.alphavantage.co/premium/' ; this.closest('.fixed').remove()" class="flex-1 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg transition font-semibold">
                    <i class="fas fa-external-link-alt"></i> Get Premium Key
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

// ==================== TRADING CHART FUNCTIONS ====================

let tradingChart = null;
let currentPair = 'EURUSD';
let currentTimeframe = '60';
let chartData = {};

// Initialize Trading Chart on page load (lazy loaded)
function initTradingChart() {
    const container = document.getElementById('trading-chart');
    if (!container) {
        console.error('trading-chart container not found!');
        return;
    }
    
    // Check if LightweightCharts is loaded
    if (typeof LightweightCharts === 'undefined') {
        console.error('LightweightCharts library not loaded!');
        return;
    }
    
    console.log(`🚀 Lazy-loading trading chart: ${container.clientWidth}x${container.clientHeight}px`);
    
    try {
        // Create chart
        tradingChart = LightweightCharts.createChart(container, {
            layout: {
                textColor: '#d1d5db',
                background: { color: '#0f172a' }
            },
            width: container.clientWidth,
            height: container.clientHeight,
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                tickMarkFormatter: (time) => {
                    const date = new Date(time * 1000);
                    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                }
            },
            rightPriceScale: {
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1
                }
            }
        });
        
        console.log('Chart created successfully');
        
        // Verify chart object has the required methods
        if (typeof tradingChart.addCandlestickSeries !== 'function') {
            console.error('tradingChart.addCandlestickSeries is not available!', tradingChart);
            return;
        }
        
        // Create candlestick series
        window.candleStickSeries = tradingChart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderUpColor: '#10b981',
            borderDownColor: '#ef4444',
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444'
        });
        
        console.log('Candlestick series created');
        
        // Load initial data
        updateChartData();
        
        // Fit content
        tradingChart.timeScale().fitContent();
        console.log('Chart initialized and fitted');
        
        // Setup optimized polling for chart (reduced from 60s to adaptive interval based on data mode)
        const chartInterval = dataOptimizer.getPollingInterval('chart');
        pollingIntervals.chart = setInterval(updateChartData, chartInterval);
        console.log(`📊 Chart polling set to ${chartInterval}ms`);
        
    } catch (error) {
        console.error('Error initializing chart:', error);
    }
}

// Change currency pair
function changePair(pair) {
    currentPair = pair;
    
    // Update active tab
    document.querySelectorAll('.pair-tab').forEach(tab => {
        tab.classList.remove('active-tab');
    });
    document.querySelector(`[data-pair="${pair}"]`).classList.add('active-tab');
    
    // Update chart
    updateChartData();
}

// Change timeframe
function changeTimeframe(timeframe) {
    currentTimeframe = timeframe;
    updateChartData();
}

// Fetch and update chart data (optimized with caching and lazy loading)
async function updateChartData() {
    try {
        console.log(`Fetching chart data for ${currentPair} (${currentTimeframe}min)...`);
        
        // Use cache with lightweight endpoint
        const cacheKey = `chart-${currentPair}-${currentTimeframe}`;
        const data = await dataOptimizer.getCachedOrFetch(cacheKey, async () => {
            const response = await fetch(
                `${API_BASE_URL}/api/chart-data?symbol=${currentPair}&timeframe=${currentTimeframe}`,
                {
                    headers: { 'Content-Type': 'application/json' }
                }
            );
            
            if (response.ok) {
                return await response.json();
            } else {
                console.warn(`API returned status ${response.status}, using mock data`);
                return generateMockChartData(currentPair, currentTimeframe);
            }
        }, 60000);  // Cache chart data for 60 seconds
        
        // Update candlestick chart with optimized update
        if (data.ohlc && data.ohlc.length > 0) {
            console.log(`Processing ${data.ohlc.length} OHLC bars...`);
            
            const chartBars = data.ohlc.map(bar => ({
                time: Math.floor(bar.time / 1000),
                open: bar.open,
                high: bar.high,
                low: bar.low,
                close: bar.close
            }));
            
            if (window.candleStickSeries) {
                window.candleStickSeries.setData(chartBars);
                tradingChart.timeScale().fitContent();
                console.log('Chart updated successfully');
            }
            
            // Update chart info
            const latest = data.ohlc[data.ohlc.length - 1];
            const previous = data.ohlc[data.ohlc.length - 2];
            const change = ((latest.close - previous.close) / previous.close * 100).toFixed(2);
            
            document.getElementById('chart-current-price').textContent = latest.close.toFixed(5);
            document.getElementById('chart-change').textContent = `${change > 0 ? '+' : ''}${change}%`;
            document.getElementById('chart-high').textContent = Math.max(...data.ohlc.map(b => b.high)).toFixed(5);
            document.getElementById('chart-low').textContent = Math.min(...data.ohlc.map(b => b.low)).toFixed(5);
            
            console.log(`Chart info: Price=${latest.close.toFixed(5)}, Change=${change}%`);
        }
        
    } catch (error) {
        console.error('Chart data error:', error);
        const data = generateMockChartData(currentPair, currentTimeframe);
        if (data.ohlc && data.ohlc.length > 0) {
            const chartBars = data.ohlc.map(bar => ({
                time: Math.floor(bar.time / 1000),
                open: bar.open,
                high: bar.high,
                low: bar.low,
                close: bar.close
            }));
            
            if (window.candleStickSeries) {
                window.candleStickSeries.setData(chartBars);
                tradingChart.timeScale().fitContent();
            }
        }
    }
}

// Generate mock chart data for demo/fallback
function generateMockChartData(pair, timeframe) {
    const basePrice = {
        'EURUSD': 1.1680,
        'GBPUSD': 1.3463,
        'USDJPY': 104.50,
        'AUDUSD': 0.7210,
        'USDCAD': 1.2550
    }[pair] || 1.1680;
    
    const bars = [];
    let price = basePrice;
    const now = Date.now();
    const interval = parseInt(timeframe) * 60 * 1000;
    
    for (let i = 50; i >= 0; i--) {
        const time = now - (i * interval);
        const volatility = 0.0005;
        const open = price;
        const close = price + (Math.random() - 0.5) * volatility;
        const high = Math.max(open, close) + Math.random() * volatility;
        const low = Math.min(open, close) - Math.random() * volatility;
        
        bars.push({
            time: time,
            open: parseFloat(open.toFixed(5)),
            high: parseFloat(high.toFixed(5)),
            low: parseFloat(low.toFixed(5)),
            close: parseFloat(close.toFixed(5))
        });
        
        price = close;
    }
    
    return { ohlc: bars };
}

// Handle window resize
window.addEventListener('resize', () => {
    if (tradingChart) {
        const container = document.getElementById('trading-chart');
        if (container) {
            tradingChart.applyOptions({
                width: container.clientWidth,
                height: container.clientHeight
            });
        }
    }
});

// Add Low Data Mode UI toggle
function addLowDataModeUI() {
    const existingBtn = document.getElementById('low-data-mode-btn');
    if (existingBtn) return;  // Already exists

    const btn = document.createElement('button');
    btn.id = 'low-data-mode-btn';
    btn.className = 'px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-200 transition text-sm font-medium';
    btn.innerHTML = `<i class="fas fa-wifi-slash"></i> Low Data Mode: ${dataOptimizer.lowDataMode ? 'ON' : 'OFF'}`;
    
    btn.addEventListener('click', () => {
        const newState = !dataOptimizer.lowDataMode;
        dataOptimizer.saveLowDataMode(newState);
        btn.innerHTML = `<i class="fas fa-wifi-slash"></i> Low Data Mode: ${newState ? 'ON' : 'OFF'}`;
        
        if (newState) {
            btn.classList.add('bg-orange-600', 'hover:bg-orange-500');
            btn.classList.remove('bg-gray-700', 'hover:bg-gray-600');
            showNotification('📡 Low Data Mode enabled - reducing polling frequency', 'info');
            console.log('🔇 Low Data Mode: ON - Polling intervals increased');
        } else {
            btn.classList.remove('bg-orange-600', 'hover:bg-orange-500');
            btn.classList.add('bg-gray-700', 'hover:bg-gray-600');
            showNotification('📡 Low Data Mode disabled - normal polling resumed', 'info');
            console.log('🔊 Low Data Mode: OFF - Polling intervals normalized');
        }
        
        // Restart polling with new intervals
        restartPolling();
    });

    // Add button to dashboard header or create a toolbar
    const header = document.querySelector('header') || document.querySelector('.dashboard-header');
    if (header) {
        header.appendChild(btn);
    } else {
        // Fallback: add to body after delay
        setTimeout(() => {
            const container = document.querySelector('[role="main"]') || document.body;
            container.insertBefore(btn, container.firstChild);
        }, 100);
    }

    console.log('✅ Low Data Mode UI added');
}

// Restart polling with new intervals
function restartPolling() {
    // Clear existing intervals
    if (pollingIntervals.signals) clearInterval(pollingIntervals.signals);
    if (pollingIntervals.status) clearInterval(pollingIntervals.status);
    if (pollingIntervals.chart) clearInterval(pollingIntervals.chart);

    // Clear cache to force immediate fresh data
    dataOptimizer.clearCache('signals');
    dataOptimizer.clearCache('stats');
    dataOptimizer.clearCache('health');

    // Restart polling with new intervals
    const signalInterval = dataOptimizer.getPollingInterval('signals');
    const healthInterval = dataOptimizer.getPollingInterval('health');
    const chartInterval = dataOptimizer.getPollingInterval('chart');

    pollingIntervals.signals = setInterval(loadSignals, signalInterval);
    pollingIntervals.status = setInterval(updateServerStatus, healthInterval);
    if (tradingChart) {
        pollingIntervals.chart = setInterval(updateChartData, chartInterval);
    }

    console.log(`🔄 Polling restarted with new intervals: signals=${signalInterval}ms, health=${healthInterval}ms, chart=${chartInterval}ms`);
}

// Cleanup polling intervals on page unload
window.addEventListener('beforeunload', () => {
    if (pollingIntervals.signals) clearInterval(pollingIntervals.signals);
    if (pollingIntervals.status) clearInterval(pollingIntervals.status);
    if (pollingIntervals.chart) clearInterval(pollingIntervals.chart);
    console.log('🛑 Polling intervals cleaned up');
});

// ===== ADMIN FUNCTIONS =====
/**
 * Check if current user is admin and show admin button
 */
function checkAdminStatus() {
    const adminBtn = document.getElementById('admin-btn');
    if (!adminBtn) return;
    
    // Check if user is admin
    if (typeof AuthSystem !== 'undefined' && AuthSystem.user && AuthSystem.user.is_admin) {
        adminBtn.classList.remove('hidden');
        if (typeof updateMobileAdminBtn !== 'undefined') {
            updateMobileAdminBtn(true);
        }
        console.log('✅ Admin user detected');
    } else {
        if (typeof updateMobileAdminBtn !== 'undefined') {
            updateMobileAdminBtn(false);
        }
    }
}

/**
 * Navigate to admin dashboard
 */
function goToAdmin() {
    window.location.href = 'admin.html';
}

// ===== TRADING BOT CONTROL =====
/**
 * Toggle trading bot on/off
 */
async function toggleTradingBot() {
    const btn = document.getElementById('trading-bot-btn');
    const statusEl = document.getElementById('bot-status');
    const token = sessionStorage.getItem('access_token');
    
    if (!token) {
        alert('Please log in first');
        return;
    }
    
    try {
        // First check current status
        const statusResp = await fetch(`${API_BASE_URL}/api/execution/running`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const statusData = await statusResp.json();
        const isRunning = statusData.running;
        
        let response;
        if (isRunning) {
            // Stop the bot
            response = await fetch(`${API_BASE_URL}/api/execution/stop`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
        } else {
            // Start the bot
            response = await fetch(`${API_BASE_URL}/api/execution/start`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });
        }
        
        const data = await response.json();
        
        if (response.ok) {
            // Update button appearance
            if (data.running) {
                btn.classList.remove('bg-red-600', 'hover:bg-red-500');
                btn.classList.add('bg-green-600', 'hover:bg-green-500');
                btn.innerHTML = '<i class="fas fa-stop"></i> Stop Trading Bot';
                statusEl.textContent = 'Active';
                statusEl.classList.add('text-green-400');
            } else {
                btn.classList.remove('bg-green-600', 'hover:bg-green-500');
                btn.classList.add('bg-red-600', 'hover:bg-red-500');
                btn.innerHTML = '<i class="fas fa-play"></i> Start Trading Bot';
                statusEl.textContent = 'Idle';
                statusEl.classList.remove('text-green-400');
            }
        } else {
            alert(data.error || 'Failed to toggle trading bot');
        }
    } catch (error) {
        console.error('Error toggling trading bot:', error);
        alert('Error connecting to server');
    }
}

/**
 * Check and update trading bot status on page load
 */
async function checkBotStatus() {
    const btn = document.getElementById('trading-bot-btn');
    const statusEl = document.getElementById('bot-status');
    const token = sessionStorage.getItem('access_token');
    
    if (!token || !btn) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/execution/running`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.running) {
            btn.classList.remove('bg-red-600', 'hover:bg-red-500');
            btn.classList.add('bg-green-600', 'hover:bg-green-500');
            btn.innerHTML = '<i class="fas fa-stop"></i> Stop Trading Bot';
            statusEl.textContent = 'Active';
            statusEl.classList.add('text-green-400');
        }
    } catch (error) {
        console.error('Error checking bot status:', error);
    }
}
