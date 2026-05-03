// ============================================
// SofAi FX Admin Dashboard JavaScript
// ============================================

let API_BASE = window.location.origin;
let currentTab = 'overview';
let charts = {};

// ===== HELPER FUNCTION =====
function getAuthToken() {
    // Check sessionStorage first, then localStorage (for browser compatibility)
    return sessionStorage.getItem('access_token') || localStorage.getItem('access_token');
}

// ===== MOBILE SIDEBAR TOGGLE =====
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    
    if (sidebar && overlay) {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
    }
}

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    if (typeof APIConfig !== 'undefined' && APIConfig.baseUrl) {
        API_BASE = APIConfig.baseUrl;
        console.log('[ADMIN] Using API_BASE from APIConfig:', API_BASE);
    } else {
        API_BASE = window.location.origin;
        console.warn('[ADMIN] APIConfig is not defined; using window.location.origin as API base URL:', API_BASE);
    }

    checkAdminAuth();
    loadAdminInfo();
    refreshData();
    
    // Auto-refresh every 30 seconds
    setInterval(refreshData, 30000);
});

// ===== AUTHENTICATION CHECK =====
async function checkAdminAuth() {
    // Check both sessionStorage (primary) and localStorage (fallback for browser compatibility)
    let token = sessionStorage.getItem('access_token');
    let storageType = 'sessionStorage';
    
    if (!token) {
        token = localStorage.getItem('access_token');
        storageType = 'localStorage';
    }
    
    console.log('[ADMIN] Token from', storageType + ':', token ? 'YES (found)' : 'NO (missing)');
    
    if (!token) {
        console.log('[ADMIN] No token found - redirecting to login');
        window.location.href = 'index.html';
        return;
    }
    
    try {
        console.log('[ADMIN] Checking admin access with token...');
        const response = await fetch(`${API_BASE}/admin/current-admin`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        console.log('[ADMIN] Response status:', response.status);
        console.log('[ADMIN] Response ok:', response.ok);
        
        const responseData = await response.json();
        console.log('[ADMIN] Response data:', responseData);
        
        if (response.status === 403) {
            console.error('[ADMIN] Access denied (403) - User not admin');
            alert('You do not have admin access');
            window.location.href = 'index.html';
            return;
        }
        
        if (!response.ok) {
            console.error('[ADMIN] Auth check failed:', response.status);
            throw new Error('Auth check failed');
        }
        
        console.log('[ADMIN] Auth check passed - Admin access granted!');
    } catch (error) {
        console.error('[ADMIN] Auth check error:', error);
        alert('Error: ' + error.message);
        window.location.href = 'index.html';
    }
}

// ===== LOAD ADMIN INFO =====
async function loadAdminInfo() {
    // Check both sessionStorage and localStorage
    let userStr = sessionStorage.getItem('auth_user');
    if (!userStr) {
        userStr = localStorage.getItem('auth_user');
    }
    
    if (userStr) {
        const user = JSON.parse(userStr);
        document.getElementById('admin-name').textContent = user.name;
        document.getElementById('admin-email').textContent = user.email;
    }
}

// ===== TAB SWITCHING =====
function switchTab(tabName) {
    currentTab = tabName;
    
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    // Show selected tab
    const tabEl = document.getElementById(`${tabName}-tab`);
    if (tabEl) {
        tabEl.classList.remove('hidden');
    }
    
    // Update sidebar navigation
    document.querySelectorAll('.sidebar-nav-item').forEach(btn => {
        btn.classList.remove('active', 'bg-green-600');
    });
    if (event && event.target) {
        event.target.closest('.sidebar-nav-item').classList.add('active', 'bg-green-600');
    }
    
    // Close mobile sidebar after selection
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('open');
    
    // Update page title
    const titles = {
        'overview': 'Overview',
        'users': 'User Management',
        'signals': 'Signals Analytics',
        'bot': 'Bot Control Panel',
        'plans': 'Subscription Plans',
        'features': 'Feature Toggles',
        'leaderboard': 'Top Traders Leaderboard',
        'security': 'Security & Logs',
        'notifications': 'Notifications & Broadcast',
        'system': 'System Monitoring',
        'settings': 'Settings & Configuration'
    };
    document.getElementById('page-title').textContent = titles[tabName] || 'Dashboard';
    
    // Load tab-specific data
    if (tabName === 'users') loadUsers();
    if (tabName === 'signals') loadSignalAnalytics();
    if (tabName === 'bot') loadBotStatus();
    if (tabName === 'plans') loadPlans();
    if (tabName === 'features') loadFeatures();
    if (tabName === 'leaderboard') loadLeaderboard();
    if (tabName === 'security') loadFailedLogins();
    if (tabName === 'system') loadSystemStatus();
}

// ===== REFRESH DATA =====
async function refreshData() {
    const token = getAuthToken();
    
    try {
        // Load overview stats
        const statsRes = await fetch(`${API_BASE}/admin/stats/overview`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (statsRes.ok) {
            const data = await statsRes.json();
            updateOverviewStats(data.overview);
            updateSystemStatus(data.system_status);
        }
        
        // Update timestamp
        const now = new Date();
        document.getElementById('last-update').textContent = now.toLocaleTimeString();
        
    } catch (error) {
        console.error('Refresh error:', error);
    }
}

// ===== UPDATE OVERVIEW STATS =====
function updateOverviewStats(stats) {
    document.getElementById('total-users').textContent = stats.total_users;
    document.getElementById('active-users').textContent = stats.active_users_24h;
    document.getElementById('signals-today').textContent = stats.signals_today;
    document.getElementById('avg-confidence').textContent = stats.avg_confidence_today + '%';
    
    // Update signal distribution chart
    updateSignalDistributionChart(
        stats.buy_signals_today,
        stats.sell_signals_today
    );
}

// ===== CHART: SIGNAL DISTRIBUTION =====
function updateSignalDistributionChart(buys, sells) {
    const ctx = document.getElementById('signalDistributionChart')?.getContext('2d');
    if (!ctx) return;
    
    // Destroy existing chart
    if (charts.distribution) charts.distribution.destroy();
    
    charts.distribution = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Buy Signals', 'Sell Signals'],
            datasets: [{
                data: [buys, sells],
                backgroundColor: ['#10b981', '#ef4444'],
                borderColor: '#1e293b',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: { color: '#d1d5db' }
                }
            }
        }
    });
}

// ===== LOAD USERS =====
async function loadUsers() {
    const token = getAuthToken();
    const tbody = document.getElementById('users-table-body');
    
    try {
        const response = await fetch(`${API_BASE}/admin/users?per_page=50`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Failed to fetch users');
        
        const data = await response.json();
        
        if (!data.users || data.users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="py-8 text-center text-gray-400">No users found</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.users.map(user => `
            <tr class="border-b border-slate-700 table-row-hover">
                <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                        <div>
                            <p class="font-semibold text-white">${user.name}</p>
                            ${user.is_admin ? '<span class="badge badge-admin text-xs">ADMIN</span>' : ''}
                        </div>
                    </div>
                </td>
                <td class="px-4 py-3 text-sm text-gray-300">${user.email}</td>
                <td class="px-4 py-3">
                    <span class="badge ${user.plan === 'premium' ? 'bg-blue-900 text-blue-200' : user.plan === 'enterprise' ? 'bg-purple-900 text-purple-200' : 'bg-gray-800 text-gray-300'}">
                        ${user.plan.toUpperCase()}
                    </span>
                </td>
                <td class="px-4 py-3">
                    <span class="badge ${user.is_active ? 'badge-active' : 'badge-inactive'}">
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td class="px-4 py-3 text-sm text-gray-300">${user.signal_count}</td>
                <td class="px-4 py-3 space-y-1">
                    <button onclick="toggleUserActive(${user.id}, ${user.is_active})" class="block text-xs px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded text-yellow-400 font-semibold">
                        ${user.is_active ? 'Disable' : 'Enable'}
                    </button>
                    <button onclick="toggleUserAdmin(${user.id}, ${user.is_admin})" class="block text-xs px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded text-purple-400 font-semibold">
                        ${user.is_admin ? 'Revoke Admin' : 'Make Admin'}
                    </button>
                    <button onclick="showUserDetails(${user.id})" class="block text-xs px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded text-blue-400 font-semibold">
                        View Signals
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading users:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="py-8 text-center text-red-400">Error loading users</td></tr>';
    }
}

// ===== USER ACTIONS =====
async function toggleUserActive(userId, currentStatus) {
    const token = getAuthToken();
    
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}/toggle-active`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            showNotification(`User ${currentStatus ? 'disabled' : 'enabled'} successfully`);
            loadUsers();
        }
    } catch (error) {
        console.error('Error toggling user:', error);
        showNotification('Error updating user', 'error');
    }
}

async function toggleUserAdmin(userId, currentStatus) {
    const token = getAuthToken();
    
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}/toggle-admin`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            showNotification(`User ${currentStatus ? 'admin revoked' : 'made admin'} successfully`);
            loadUsers();
        }
    } catch (error) {
        console.error('Error toggling admin:', error);
        showNotification('Error updating user', 'error');
    }
}

// ===== LOAD SIGNAL ANALYTICS =====
async function loadSignalAnalytics() {
    const token = getAuthToken();
    
    try {
        const response = await fetch(`${API_BASE}/admin/signals/analytics`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Failed to fetch analytics');
        
        const data = await response.json();
        
        // Update summary
        document.getElementById('total-signals').textContent = data.summary.total_signals;
        document.getElementById('buy-sell-ratio').textContent = data.summary.buy_sell_ratio.toFixed(2);
        
        // Update timeline chart
        updateSignalTimelineChart(data.timeline_30d);
        
        // Update top pairs
        updateTopPairsList(data.top_pairs);
    } catch (error) {
        console.error('Error loading signal analytics:', error);
    }
}

// ===== CHART: SIGNAL TIMELINE =====
function updateSignalTimelineChart(timeline) {
    const ctx = document.getElementById('signalTimelineChart')?.getContext('2d');
    if (!ctx) return;
    
    if (charts.timeline) charts.timeline.destroy();
    
    charts.timeline = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeline.map(d => d.date),
            datasets: [{
                label: 'Signals',
                data: timeline.map(d => d.signals),
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#d1d5db' } }
            },
            scales: {
                y: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: '#374151' }
                },
                x: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: '#374151' }
                }
            }
        }
    });
}

// ===== UPDATE TOP PAIRS =====
function updateTopPairsList(pairs) {
    const list = document.getElementById('top-pairs-list');
    
    if (!pairs || pairs.length === 0) {
        list.innerHTML = '<p class="text-gray-400 text-center py-4">No data yet</p>';
        return;
    }
    
    list.innerHTML = pairs.map(pair => `
        <div class="flex justify-between items-center p-3 bg-slate-700 rounded hover:bg-slate-600 transition">
            <div>
                <p class="font-semibold text-white">${pair.symbol}</p>
                <p class="text-xs text-gray-400">${pair.signal_count} signals</p>
            </div>
            <div class="text-right">
                <p class="font-semibold text-green-400">${pair.avg_confidence}%</p>
                <p class="text-xs text-gray-400">Avg confidence</p>
            </div>
        </div>
    `).join('');
}

// ===== LOAD SYSTEM STATUS =====
async function loadSystemStatus() {
    const token = getAuthToken();
    
    try {
        const response = await fetch(`${API_BASE}/admin/system/status`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Failed to fetch system status');
        
        const data = await response.json();
        
        // Update database info
        document.getElementById('db-size').textContent = data.database.size_mb + ' MB';
        document.getElementById('db-user-count').textContent = data.database.users;
        document.getElementById('db-signal-count').textContent = data.database.signals;
        
        // Update logs
        updateLogsList(data.logs);
    } catch (error) {
        console.error('Error loading system status:', error);
    }
}

// ===== UPDATE LOGS LIST =====
function updateLogsList(logs) {
    const list = document.getElementById('logs-list');
    
    if (!logs || logs.length === 0) {
        list.innerHTML = '<p class="text-gray-400 text-center py-4">No recent logs</p>';
        return;
    }
    
    list.innerHTML = logs.map(log => `
        <div class="p-3 bg-slate-700 rounded text-sm">
            <p class="font-semibold text-white">${log.file}</p>
            <p class="text-xs text-gray-400">Modified: ${new Date(log.modified).toLocaleString()}</p>
        </div>
    `).join('');
}

// ===== SEND TEST NOTIFICATION =====
async function sendTestNotification() {
    const token = getAuthToken();
    const channel = document.getElementById('test-channel').value;
    
    try {
        const response = await fetch(`${API_BASE}/admin/notifications/test`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ channel })
        });
        
        if (response.ok) {
            showNotification('✅ Test notification sent!');
        } else {
            showNotification('❌ Failed to send test notification', 'error');
        }
    } catch (error) {
        console.error('Error sending test notification:', error);
        showNotification('Error sending notification', 'error');
    }
}

// ===== SEND BROADCAST =====
async function sendBroadcast() {
    const token = getAuthToken();
    const title = document.getElementById('broadcast-title').value;
    const message = document.getElementById('broadcast-message').value;
    
    if (!title || !message) {
        showNotification('Please fill in all fields', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/notifications/broadcast`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, message })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`✅ Broadcast sent to ${data.sent}/${data.total_users} users`);
            document.getElementById('broadcast-title').value = '';
            document.getElementById('broadcast-message').value = '';
        } else {
            showNotification('❌ Failed to send broadcast', 'error');
        }
    } catch (error) {
        console.error('Error sending broadcast:', error);
        showNotification('Error sending broadcast', 'error');
    }
}

// ===== UTILITY FUNCTIONS =====
function showNotification(message, type = 'success') {
    const toast = document.getElementById('notification-toast');
    const msgEl = document.getElementById('notification-message');
    
    msgEl.textContent = message;
    
    if (type === 'error') {
        toast.classList.remove('bg-green-600');
        toast.classList.add('bg-red-600');
    } else {
        toast.classList.remove('bg-red-600');
        toast.classList.add('bg-green-600');
    }
    
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

function logout() {
    sessionStorage.clear();
    localStorage.clear();
    window.location.href = 'index.html';
}

async function showUserDetails(userId) {
    const token = getAuthToken();
    
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}/signals`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();
        alert(`User: ${data.user.name}\nSignals: ${data.signal_count}\nLast 5 signals:\n${data.signals.slice(0, 5).map(s => `${s.symbol} ${s.signal}`).join('\n')}`);
    } catch (error) {
        console.error('Error loading user details:', error);
    }
}

// ===== BOT CONTROL FUNCTIONS =====
async function loadBotStatus() {
    const token = getAuthToken();
    
    try {
        const response = await fetch(`${API_BASE}/admin/bot/status`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            const bot = data.bot;
            
            document.getElementById('bot-enabled').textContent = bot.enabled ? 'ON' : 'OFF';
            document.getElementById('bot-enabled').className = bot.enabled ? 'text-2xl font-bold text-green-400 mt-2' : 'text-2xl font-bold text-red-400 mt-2';
            document.getElementById('bot-risk').textContent = bot.risk_level.toUpperCase();
            document.getElementById('trades-today').textContent = bot.trades_today;
            
            document.getElementById('bot-toggle').checked = bot.enabled;
        }
    } catch (error) {
        console.error('Error loading bot status:', error);
    }
}

async function toggleBot() {
    const token = getAuthToken();
    const enabled = document.getElementById('bot-toggle').checked;
    
    try {
        const response = await fetch(`${API_BASE}/admin/bot/toggle`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled })
        });
        
        if (response.ok) {
            showNotification(`Bot ${enabled ? 'enabled' : 'disabled'} successfully`);
            loadBotStatus();
        }
    } catch (error) {
        console.error('Error toggling bot:', error);
        showNotification('Error toggling bot', 'error');
    }
}

async function updateRiskLevel() {
    const token = getAuthToken();
    const risk_level = document.getElementById('risk-level').value;
    
    try {
        const response = await fetch(`${API_BASE}/admin/bot/risk-level`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ risk_level })
        });
        
        if (response.ok) {
            showNotification('Risk level updated successfully');
            loadBotStatus();
        }
    } catch (error) {
        console.error('Error updating risk level:', error);
        showNotification('Error updating risk level', 'error');
    }
}

// ===== PLANS FUNCTIONS =====
async function loadPlans() {
    const token = getAuthToken();
    
    try {
        const response = await fetch(`${API_BASE}/admin/plans`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            const grid = document.getElementById('plans-grid');
            
            grid.innerHTML = Object.entries(data.plans).map(([key, plan]) => `
                <div class="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 rounded-lg p-6 hover:border-green-500 transition">
                    <h4 class="text-xl font-bold text-white mb-2">${plan.name}</h4>
                    <p class="text-2xl font-bold text-green-400 mb-4">$${plan.price}<span class="text-sm text-gray-400">/mo</span></p>
                    
                    <div class="mb-4 pb-4 border-b border-slate-700">
                        <p class="text-sm font-semibold text-gray-300 mb-2">Users: <span class="text-green-400">${plan.users}</span></p>
                        <p class="text-sm font-semibold text-gray-300">Token Limit: <span class="text-green-400">${plan.token_limit === -1 ? 'Unlimited' : plan.token_limit}</span></p>
                    </div>
                    
                    <ul class="space-y-2 text-sm text-gray-300">
                        ${plan.features.map(f => `<li class="flex items-center gap-2"><i class="fas fa-check text-green-500"></i> ${f}</li>`).join('')}
                    </ul>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading plans:', error);
    }
}

// ===== FEATURES FUNCTIONS =====
async function loadFeatures() {
    const token = getAuthToken();
    
    try {
        const response = await fetch(`${API_BASE}/admin/features`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            const list = document.getElementById('features-list');
            
            list.innerHTML = Object.entries(data.features).map(([key, feature]) => `
                <div class="flex items-center justify-between p-4 bg-slate-700 rounded-lg hover:bg-slate-600 transition">
                    <div>
                        <p class="font-semibold text-white">${feature.name}</p>
                        <p class="text-sm text-gray-400">${feature.description}</p>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" ${feature.enabled ? 'checked' : ''} onchange="toggleFeature('${key}', this.checked)" class="sr-only peer">
                        <div class="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                    </label>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading features:', error);
    }
}

async function toggleFeature(featureId, enabled) {
    const token = getAuthToken();
    
    try {
        const response = await fetch(`${API_BASE}/admin/features/${featureId}/toggle`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled })
        });
        
        if (response.ok) {
            showNotification(`Feature ${enabled ? 'enabled' : 'disabled'} successfully`);
        }
    } catch (error) {
        console.error('Error toggling feature:', error);
        showNotification('Error toggling feature', 'error');
    }
}

// ===== LEADERBOARD FUNCTIONS =====
async function loadLeaderboard() {
    const token = getAuthToken();
    
    try {
        const response = await fetch(`${API_BASE}/admin/leaderboard/users?limit=20`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            const tbody = document.getElementById('leaderboard-body');
            
            tbody.innerHTML = data.leaderboard.map(user => `
                <tr class="border-b border-slate-700 table-row-hover">
                    <td class="px-4 py-3">
                        <span class="text-lg font-bold text-yellow-500">#${user.rank}</span>
                    </td>
                    <td class="px-4 py-3">
                        <div>
                            <p class="font-semibold text-white">${user.name}</p>
                            <p class="text-xs text-gray-400">${user.email}</p>
                        </div>
                    </td>
                    <td class="px-4 py-3 text-lg font-bold text-green-400">${user.signal_count}</td>
                    <td class="px-4 py-3">
                        <span class="badge ${user.plan === 'premium' ? 'bg-blue-900 text-blue-200' : user.plan === 'enterprise' ? 'bg-purple-900 text-purple-200' : 'bg-gray-800 text-gray-300'}">
                            ${user.plan.toUpperCase()}
                        </span>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading leaderboard:', error);
    }
}

// ===== SECURITY FUNCTIONS =====
async function loadFailedLogins() {
    const token = getAuthToken();
    
    try {
        const response = await fetch(`${API_BASE}/admin/security/failed-logins`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            const container = document.getElementById('failed-logins');
            
            if (!data.failed_attempts || data.failed_attempts.length === 0) {
                container.innerHTML = '<p class="text-gray-400 text-center py-4">No failed login attempts</p>';
                return;
            }
            
            container.innerHTML = data.failed_attempts.map(attempt => `
                <div class="p-3 bg-slate-700 rounded">
                    <p class="font-semibold text-white text-sm">${attempt.email}</p>
                    <p class="text-xs text-red-400 mt-1">Attempts: ${attempt.attempts} | IP: ${attempt.ip}</p>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading failed logins:', error);
    }
}

async function saveUserNotes() {
    const token = getAuthToken();
    const user_id = parseInt(document.getElementById('note-user-id').value);
    const notes = document.getElementById('user-notes').value;
    
    if (!user_id) {
        showNotification('Please enter a user ID', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/users/${user_id}/notes`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ notes })
        });
        
        if (response.ok) {
            showNotification('Notes saved successfully');
        }
    } catch (error) {
        console.error('Error saving notes:', error);
        showNotification('Error saving notes', 'error');
    }
}

// ===== EXPORT FUNCTIONS =====
async function exportUsersCSV() {
    const token = getAuthToken();
    
    try {
        const response = await fetch(`${API_BASE}/admin/export/users-csv`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'sofai-users.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showNotification('Users CSV exported successfully');
        }
    } catch (error) {
        console.error('Error exporting users:', error);
        showNotification('Error exporting users', 'error');
    }
}

async function exportSignalsCSV() {
    showNotification('Signals export coming soon', 'info');
}

function updateSystemStatus(status) {
    // Can enhance this to show more detailed status information
}
