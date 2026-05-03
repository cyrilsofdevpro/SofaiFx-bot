/**
 * Pair Recommendations UI Manager
 * Displays recommended currency pairs based on signal analysis
 */

class RecommendationsManager {
    constructor() {
        this.recommendations = [];
        this.isLoading = false;
    }

    /**
     * Fetch recommendations from API
     */
    async fetchRecommendations(hours = 24) {
        const token = localStorage.getItem('access_token');
        if (!token) {
            console.debug('User not authenticated, features will load after login');
            return;
        }
        
        this.isLoading = true;
        try {

            const response = await fetch(
                APIConfig.buildUrl(`/api/recommendations?hours=${hours}`),
                {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            const data = await response.json();
            this.recommendations = data.recommendations || [];
            this.renderRecommendations();
        } catch (error) {
            console.error('Error fetching recommendations:', error);
            this.showError('Failed to load recommendations');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Render recommendations as cards
     */
    renderRecommendations() {
        const container = document.getElementById('recommendations-container');
        if (!container) return;

        if (this.recommendations.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <i class="fas fa-inbox text-gray-400 text-4xl mb-3"></i>
                    <p class="text-gray-400">No recommendations available yet.</p>
                    <p class="text-sm text-gray-500 mt-2">Analyze some pairs to get recommendations</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.recommendations.map(rec => this.createRecommendationCard(rec)).join('');
    }

    /**
     * Create a single recommendation card
     */
    createRecommendationCard(rec) {
        const trendColor = this.getTrendColor(rec.trend);
        const trendIcon = this.getTrendIcon(rec.trend);
        const stats = rec.stats;

        return `
            <div class="bg-gradient-to-br from-slate-700 to-slate-800 border border-slate-600 rounded-lg p-5 hover:border-${trendColor}-500 transition transform hover:scale-105 cursor-pointer" 
                 onclick="this.classList.toggle('ring-2'); this.classList.toggle('ring-${trendColor}-500');">
                <!-- Header -->
                <div class="flex items-start justify-between mb-4">
                    <div class="flex items-center gap-3">
                        <span class="text-4xl">${rec.emoji}</span>
                        <div>
                            <h3 class="text-lg font-bold text-white">${rec.symbol}</h3>
                            <p class="text-xs text-gray-400">${rec.description}</p>
                        </div>
                    </div>
                    <span class="px-2 py-1 bg-${trendColor}-900 text-${trendColor}-200 text-xs font-semibold rounded">
                        ${rec.trend.replace(/_/g, ' ').toUpperCase()}
                    </span>
                </div>

                <!-- Stats Grid -->
                <div class="grid grid-cols-4 gap-2 mb-4">
                    <div class="bg-slate-600/50 rounded p-2 text-center">
                        <p class="text-xs text-gray-400">Total</p>
                        <p class="text-lg font-bold text-white">${stats.total_signals}</p>
                    </div>
                    <div class="bg-green-900/30 rounded p-2 text-center">
                        <p class="text-xs text-green-400">BUY</p>
                        <p class="text-lg font-bold text-green-400">${stats.buy_signals}</p>
                    </div>
                    <div class="bg-red-900/30 rounded p-2 text-center">
                        <p class="text-xs text-red-400">SELL</p>
                        <p class="text-lg font-bold text-red-400">${stats.sell_signals}</p>
                    </div>
                    <div class="bg-yellow-900/30 rounded p-2 text-center">
                        <p class="text-xs text-yellow-400">HOLD</p>
                        <p class="text-lg font-bold text-yellow-400">${stats.hold_signals}</p>
                    </div>
                </div>

                <!-- Confidence Bar -->
                <div class="mb-3">
                    <div class="flex justify-between items-center mb-2">
                        <p class="text-xs text-gray-400">Avg Confidence</p>
                        <p class="text-sm font-bold text-${trendColor}-400">${stats.avg_confidence}</p>
                    </div>
                    <div class="w-full bg-slate-600 rounded-full h-2 overflow-hidden">
                        <div class="bg-gradient-to-r from-${trendColor}-500 to-${trendColor}-400 h-full rounded-full transition-all"
                             style="width: ${stats.avg_confidence.replace('%', '')}%"></div>
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="flex gap-2 pt-3 border-t border-slate-600">
                    <button onclick="event.stopPropagation(); analyzeSymbol('${rec.symbol}')" 
                            class="flex-1 px-2 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded transition">
                        <i class="fas fa-chart-line"></i> Analyze
                    </button>
                    <button onclick="event.stopPropagation(); addToMonitored('${rec.symbol}')" 
                            class="flex-1 px-2 py-1.5 bg-slate-600 hover:bg-slate-500 text-white text-xs font-semibold rounded transition">
                        <i class="fas fa-plus"></i> Monitor
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Get color class for trend type
     */
    getTrendColor(trend) {
        const colors = {
            'trending_up': 'green',
            'trending_down': 'red',
            'consolidating': 'yellow',
            'low_volatility': 'blue'
        };
        return colors[trend] || 'gray';
    }

    /**
     * Get icon for trend type
     */
    getTrendIcon(trend) {
        const icons = {
            'trending_up': '📈',
            'trending_down': '📉',
            'consolidating': '➡️',
            'low_volatility': '😴'
        };
        return icons[trend] || '📊';
    }

    /**
     * Show error message
     */
    showError(message) {
        const container = document.getElementById('recommendations-container');
        if (container) {
            container.innerHTML = `
                <div class="col-span-full">
                    <div class="bg-red-900/30 border border-red-500 rounded-lg p-4 text-center">
                        <i class="fas fa-exclamation-circle text-red-400 text-2xl mb-2"></i>
                        <p class="text-red-400 font-semibold">${message}</p>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Refresh recommendations
     */
    refresh() {
        this.fetchRecommendations();
    }
}

// Global instance
const recommendationsManager = new RecommendationsManager();

// Auto-load recommendations when user logs in or on page load if already authenticated
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        // Load immediately if already authenticated
        if (localStorage.getItem('access_token')) {
            recommendationsManager.fetchRecommendations();
        }
        // Refresh every 5 minutes
        setInterval(() => recommendationsManager.fetchRecommendations(), 5 * 60 * 1000);
    }, 1000);
});

// Listen for login event and load recommendations
window.addEventListener('userLoggedIn', () => {
    console.log('🔄 User logged in, loading recommendations...');
    recommendationsManager.fetchRecommendations();
});
