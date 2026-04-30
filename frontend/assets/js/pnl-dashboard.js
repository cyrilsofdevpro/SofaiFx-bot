/**
 * P&L Dashboard - Performance tracking and analytics
 * Phase 5: User System - Dashboard with P&L tracking
 */

let pnlChart = null;
let monthlyChart = null;

// Initialize P&L Dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated before loading P&L
    if (typeof AuthSystem !== 'undefined' && AuthSystem.isAuthenticated()) {
        loadPnLDashboard();
    }
});

// Load P&L Dashboard data
async function loadPnLDashboard() {
    try {
        const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
        if (!token) {
            console.log('No auth token - P&L dashboard hidden');
            return;
        }
        
        // Load summary
        await loadPnLSummary(token);
        
        // Load recent trades
        await loadRecentTrades(token);
        
        // Load by symbol
        await loadPnLBySymbol(token);
        
        // Load monthly
        await loadMonthlyPnL(token);
        
    } catch (error) {
        console.error('P&L Dashboard error:', error);
    }
}

// Load P&L Summary
async function loadPnLSummary(token) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/pnl/summary`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) return;
        
        const data = await response.json();
        const pnl = data.data;
        
        // Update summary cards
        const totalEl = document.getElementById('pnl-total');
        const totalPercentEl = document.getElementById('pnl-total-percent');
        const winRateEl = document.getElementById('pnl-win-rate');
        const tradesCountEl = document.getElementById('pnl-trades-count');
        const profitFactorEl = document.getElementById('pnl-profit-factor');
        const avgWinEl = document.getElementById('pnl-avg-win');
        const openPositionsEl = document.getElementById('pnl-open-positions');
        const winningTradesEl = document.getElementById('pnl-winning-trades');
        
        if (totalEl) {
            const pnlValue = pnl.total_pnl || 0;
            totalEl.textContent = `$${pnlValue.toFixed(2)}`;
            totalEl.className = `text-2xl font-bold ${pnlValue >= 0 ? 'text-green-400' : 'text-red-400'}`;
        }
        
        if (totalPercentEl) {
            totalPercentEl.textContent = `${(pnl.total_pnl_percent || 0).toFixed(2)}%`;
        }
        
        if (winRateEl) {
            winRateEl.textContent = `${(pnl.win_rate_percent || 0).toFixed(1)}%`;
        }
        
        if (tradesCountEl) {
            tradesCountEl.textContent = `${pnl.total_trades || 0} trades`;
        }
        
        if (profitFactorEl) {
            profitFactorEl.textContent = (pnl.profit_factor || 0).toFixed(2);
        }
        
        if (avgWinEl) {
            avgWinEl.textContent = `Avg Win: $${(pnl.avg_win || 0).toFixed(2)}`;
        }
        
        // Update stats section
        updateElement('stat-total', pnl.total_trades || 0);
        updateElement('stat-winning', pnl.winning_trades || 0);
        updateElement('stat-losing', pnl.losing_trades || 0);
        updateElement('stat-avg-win', `$${(pnl.avg_win || 0).toFixed(2)}`);
        updateElement('stat-avg-loss', `$${(pnl.avg_loss || 0).toFixed(2)}`);
        updateElement('stat-largest-win', `$${(pnl.largest_win || 0).toFixed(2)}`);
        updateElement('stat-largest-loss', `$${(pnl.largest_loss || 0).toFixed(2)}`);
        
        // Load open positions
        await loadOpenPositionsPnL(token);
        
    } catch (error) {
        console.error('P&L Summary error:', error);
    }
}

// Load Open Positions
async function loadOpenPositionsPnL(token) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/trades/open`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) return;
        
        const data = await response.json();
        const trades = data.data || [];
        
        const openEl = document.getElementById('pnl-open-positions');
        const winningEl = document.getElementById('pnl-winning-trades');
        
        if (openEl) {
            openEl.textContent = trades.length;
        }
        
        if (winningEl) {
            const winning = trades.filter(t => t.pnl && t.pnl > 0).length;
            winningEl.textContent = `${winning} winning`;
        }
        
    } catch (error) {
        console.error('Open positions error:', error);
    }
}

// Load Recent Trades
async function loadRecentTrades(token) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/trades/recent?limit=20`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) return;
        
        const data = await response.json();
        const trades = data.data || [];
        
        const container = document.getElementById('pnl-recent-trades');
        if (!container) return;
        
        if (trades.length === 0) {
            container.innerHTML = '<p class="text-gray-400 text-center py-4">No trades yet</p>';
            return;
        }
        
        container.innerHTML = trades.map(trade => `
            <div class="flex items-center justify-between bg-slate-700 rounded-lg p-3">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full flex items-center justify-center ${trade.trade_type === 'BUY' ? 'bg-green-600' : 'bg-red-600'}">
                        <i class="fas fa-${trade.trade_type === 'BUY' ? 'arrow-up' : 'arrow-down'} text-white"></i>
                    </div>
                    <div>
                        <div class="font-semibold text-white">${trade.symbol}</div>
                        <div class="text-sm text-gray-400">${formatDate(trade.entry_time)}</div>
                    </div>
                </div>
                <div class="text-right">
                    <div class="font-semibold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}">
                        ${trade.pnl >= 0 ? '+' : ''}$${(trade.pnl || 0).toFixed(2)}
                    </div>
                    <div class="text-sm text-gray-400">${trade.status}</div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Recent trades error:', error);
    }
}

// Load P&L by Symbol
async function loadPnLBySymbol(token) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/pnl/by-symbol`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) return;
        
        const data = await response.json();
        const symbols = data.data || {};
        
        const container = document.getElementById('pnl-symbols-grid');
        if (!container) return;
        
        const symbolEntries = Object.entries(symbols);
        
        if (symbolEntries.length === 0) {
            container.innerHTML = '<p class="text-gray-400 text-center py-4 col-span-3">No symbol data available</p>';
            return;
        }
        
        container.innerHTML = symbolEntries.map(([symbol, stats]) => `
            <div class="bg-slate-700 rounded-lg p-4">
                <div class="font-semibold text-white mb-2">${symbol}</div>
                <div class="grid grid-cols-2 gap-2 text-sm">
                    <div class="text-gray-400">Trades:</div>
                    <div class="text-white">${stats.total_trades}</div>
                    <div class="text-gray-400">Win Rate:</div>
                    <div class="text-white">${stats.win_rate}%</div>
                    <div class="text-gray-400">P&L:</div>
                    <div class="${stats.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}">$${stats.total_pnl.toFixed(2)}</div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('P&L by symbol error:', error);
    }
}

// Load Monthly P&L
async function loadMonthlyPnL(token) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/pnl/monthly?months=12`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) return;
        
        const data = await response.json();
        const monthly = data.data || [];
        
        if (monthly.length === 0) return;
        
        // Create chart
        const ctx = document.getElementById('monthly-chart');
        if (!ctx) return;
        
        if (monthlyChart) {
            monthlyChart.destroy();
        }
        
        monthlyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthly.map(m => m.month),
                datasets: [{
                    label: 'P&L',
                    data: monthly.map(m => m.total_pnl),
                    backgroundColor: monthly.map(m => m.total_pnl >= 0 ? 'rgba(34, 197, 94, 0.7)' : 'rgba(239, 68, 68, 0.7)'),
                    borderColor: monthly.map(m => m.total_pnl >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#9ca3af' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#9ca3af' }
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Monthly P&L error:', error);
    }
}

// Show P&L Tab
function showPnLTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.pnl-tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`pnl-tab-${tabName}`);
    if (selectedTab) {
        selectedTab.classList.remove('hidden');
    }
    
    // Update tab buttons
    document.querySelectorAll('[onclick^="showPnLTab"]').forEach(btn => {
        btn.classList.remove('text-green-400', 'border-b-2', 'border-green-500');
        btn.classList.add('text-gray-400');
    });
    
    // Highlight active tab
    const activeBtn = document.querySelector(`[onclick="showPnLTab('${tabName}')"]`);
    if (activeBtn) {
        activeBtn.classList.add('text-green-400', 'border-b-2', 'border-green-500');
        activeBtn.classList.remove('text-gray-400');
    }
}

// Helper: Update element text
function updateElement(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value;
    }
}

// Helper: Format date
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
        return dateStr;
    }
}

// Period filter handler
document.addEventListener('DOMContentLoaded', function() {
    const periodSelect = document.getElementById('pnl-period-select');
    if (periodSelect) {
        periodSelect.addEventListener('change', async function() {
            const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
            if (!token) return;
            
            const days = this.value;
            try {
                const response = await fetch(`${API_BASE_URL}/api/dashboard/pnl/by-period?days=${days}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (!response.ok) return;
                
                const data = await response.json();
                const pnl = data.data;
                
                // Update cards
                const totalEl = document.getElementById('pnl-total');
                if (totalEl) {
                    const pnlValue = pnl.total_pnl || 0;
                    totalEl.textContent = `$${pnlValue.toFixed(2)}`;
                    totalEl.className = `text-2xl font-bold ${pnlValue >= 0 ? 'text-green-400' : 'text-red-400'}`;
                }
                
                updateElement('pnl-win-rate', `${(pnl.win_rate_percent || 0).toFixed(1)}%`);
                updateElement('pnl-trades-count', `${pnl.total_trades || 0} trades`);
                
            } catch (error) {
                console.error('Period filter error:', error);
            }
        });
    }
});

// Export for global use
window.loadPnLDashboard = loadPnLDashboard;
window.showPnLTab = showPnLTab;