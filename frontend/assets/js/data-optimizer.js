/**
 * Data Optimizer Module
 * Implements caching, deduplication, and efficient data fetching
 */

class DataOptimizer {
    constructor() {
        this.cache = new Map();
        this.cacheTimestamps = new Map();
        this.cacheTTL = {
            signals: 15000,      // 15 seconds
            stats: 30000,        // 30 seconds
            chart: 60000,        // 60 seconds
            config: 3600000,     // 1 hour
            health: 30000        // 30 seconds
        };
        this.lowDataMode = this.loadLowDataMode();
        this.pendingRequests = new Map();
    }

    /**
     * Load Low Data Mode preference from localStorage
     */
    loadLowDataMode() {
        const saved = localStorage.getItem('lowDataMode');
        return saved ? JSON.parse(saved) : false;
    }

    /**
     * Save Low Data Mode preference
     */
    saveLowDataMode(enabled) {
        this.lowDataMode = enabled;
        localStorage.setItem('lowDataMode', JSON.stringify(enabled));
    }

    /**
     * Get polling interval based on data type and mode
     */
    getPollingInterval(dataType) {
        if (this.lowDataMode) {
            return {
                signals: 60000,     // 60 seconds in low data mode
                stats: 60000,       // 60 seconds
                chart: 120000,      // 2 minutes
                health: 60000       // 60 seconds
            }[dataType] || 60000;
        }

        return {
            signals: 15000,   // 15 seconds (reduced from 30s)
            stats: 20000,     // 20 seconds (reduced from 30s per component)
            chart: 60000,     // 60 seconds
            health: 60000     // 60 seconds (reduced from 10s)
        }[dataType] || 30000;
    }

    /**
     * Check if cache is still valid
     */
    isCacheValid(key) {
        const timestamp = this.cacheTimestamps.get(key);
        if (!timestamp) return false;

        const ttl = this.cacheTTL[key] || 30000;
        return Date.now() - timestamp < ttl;
    }

    /**
     * Get cached data or fetch if expired
     */
    async getCachedOrFetch(key, fetchFn, ttl = null) {
        // Return cached data if valid
        if (this.isCacheValid(key) && this.cache.has(key)) {
            console.log(`📦 Using cached data for: ${key}`);
            return this.cache.get(key);
        }

        // Return pending request if already in flight
        if (this.pendingRequests.has(key)) {
            console.log(`⏳ Waiting for pending request: ${key}`);
            return this.pendingRequests.get(key);
        }

        // Fetch new data
        const promise = fetchFn()
            .then(data => {
                this.cache.set(key, data);
                this.cacheTimestamps.set(key, Date.now());
                if (ttl) this.cacheTTL[key] = ttl;
                this.pendingRequests.delete(key);
                console.log(`✅ Fetched and cached: ${key}`);
                return data;
            })
            .catch(err => {
                this.pendingRequests.delete(key);
                console.error(`❌ Failed to fetch ${key}:`, err);
                // Return stale cache if available on error
                if (this.cache.has(key)) {
                    console.log(`⚠️ Returning stale cache for: ${key}`);
                    return this.cache.get(key);
                }
                throw err;
            });

        this.pendingRequests.set(key, promise);
        return promise;
    }

    /**
     * Clear cache for a specific key or all
     */
    clearCache(key = null) {
        if (key) {
            this.cache.delete(key);
            this.cacheTimestamps.delete(key);
            console.log(`🗑️ Cleared cache for: ${key}`);
        } else {
            this.cache.clear();
            this.cacheTimestamps.clear();
            console.log('🗑️ Cleared all cache');
        }
    }

    /**
     * Force refresh cache immediately
     */
    invalidateCache(key) {
        this.cacheTimestamps.delete(key);
        console.log(`🔄 Invalidated cache for: ${key}`);
    }

    /**
     * Get cache stats for debugging
     */
    getCacheStats() {
        const stats = {
            totalItems: this.cache.size,
            items: []
        };

        for (const [key, value] of this.cache) {
            const timestamp = this.cacheTimestamps.get(key);
            const age = Date.now() - timestamp;
            const ttl = this.cacheTTL[key] || 30000;
            stats.items.push({
                key,
                size: JSON.stringify(value).length,
                ageMs: age,
                ttlMs: ttl,
                expired: age > ttl
            });
        }

        return stats;
    }
}

// Global instance
window.dataOptimizer = new DataOptimizer();
