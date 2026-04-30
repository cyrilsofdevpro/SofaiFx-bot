/**
 * Network Monitor Module
 * Debugs and monitors API calls and data usage
 */

class NetworkMonitor {
    constructor() {
        this.requests = [];
        this.stats = {
            totalRequests: 0,
            totalDataSize: 0,
            duplicateRequests: 0,
            largeRequests: 0,
            requestsByEndpoint: {}
        };
        // DISABLED by default to prevent fetch interception issues during auth
        this.isEnabled = false;
        this.setupDone = false;
        this.originalFetch = window.fetch;
        // Don't auto-setup - wait for explicit enablement
    }

    /**
     * Setup fetch interceptor to track all requests
     */
    setupInterceptor() {
        window.fetch = async (...args) => {
            const startTime = performance.now();
            const [resource, config] = args;

            try {
                const response = await this.originalFetch.apply(window, args);
                const endTime = performance.now();
                const duration = endTime - startTime;

                // Clone response to measure size
                const clonedResponse = response.clone();
                const data = await clonedResponse.json().catch(() => ({}));
                const dataSize = JSON.stringify(data).length;

                this.recordRequest(resource, response.status, duration, dataSize, data);
                
                return response;
            } catch (err) {
                console.error('Fetch error:', err);
                throw err;
            }
        };
    }

    /**
     * Record a network request
     */
    recordRequest(url, status, duration, dataSize, responseData) {
        const endpoint = this.parseEndpoint(url);
        const isDuplicate = this.isDuplicateRequest(url);
        const isLarge = dataSize > 50000; // 50KB threshold

        const request = {
            timestamp: new Date(),
            url,
            endpoint,
            status,
            duration: duration.toFixed(2),
            dataSize,
            isDuplicate,
            isLarge,
            signalCount: responseData?.signals?.length || responseData?.total || 0
        };

        this.requests.push(request);
        this.updateStats(endpoint, dataSize, isDuplicate, isLarge);

        if (this.isEnabled) {
            this.logRequest(request);
        }

        // Keep only last 100 requests
        if (this.requests.length > 100) {
            this.requests.shift();
        }
    }

    /**
     * Parse endpoint from full URL
     */
    parseEndpoint(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.pathname + urlObj.search;
        } catch {
            return url;
        }
    }

    /**
     * Check for duplicate requests within last 5 seconds
     */
    isDuplicateRequest(url) {
        const now = Date.now();
        const recentRequests = this.requests.filter(r => 
            now - r.timestamp < 5000 && r.url === url
        );
        return recentRequests.length > 0;
    }

    /**
     * Update statistics
     */
    updateStats(endpoint, dataSize, isDuplicate, isLarge) {
        this.stats.totalRequests++;
        this.stats.totalDataSize += dataSize;
        if (isDuplicate) this.stats.duplicateRequests++;
        if (isLarge) this.stats.largeRequests++;

        if (!this.stats.requestsByEndpoint[endpoint]) {
            this.stats.requestsByEndpoint[endpoint] = { count: 0, totalSize: 0 };
        }
        this.stats.requestsByEndpoint[endpoint].count++;
        this.stats.requestsByEndpoint[endpoint].totalSize += dataSize;
    }

    /**
     * Log request with formatting
     */
    logRequest(request) {
        const warnings = [];
        if (request.isDuplicate) warnings.push('⚠️ DUPLICATE');
        if (request.isLarge) warnings.push('⚠️ LARGE');
        if (request.duration > 1000) warnings.push('⚠️ SLOW');

        const warningStr = warnings.length > 0 ? ` [${warnings.join(' ')}]` : '';
        console.log(
            `📡 ${request.endpoint} - Status: ${request.status}, ` +
            `Time: ${request.duration}ms, Size: ${(request.dataSize / 1024).toFixed(1)}KB${warningStr}`
        );
    }

    /**
     * Enable/disable monitoring
     */
    setEnabled(enabled) {
        if (enabled && !this.setupDone) {
            // First time enabling - setup interceptor
            this.setupInterceptor();
            this.setupDone = true;
            console.log('🔍 Network monitor interceptor initialized');
        }
        this.isEnabled = enabled;
        localStorage.setItem('networkMonitorEnabled', enabled ? 'true' : 'false');
        console.log(`🔍 Network monitoring ${enabled ? 'enabled' : 'disabled'}`);
    }

    /**
     * Get all requests
     */
    getRequests() {
        return this.requests;
    }

    /**
     * Get summary statistics
     */
    getStats() {
        const avgSize = this.stats.totalRequests > 0 
            ? (this.stats.totalDataSize / this.stats.totalRequests / 1024).toFixed(2) 
            : 0;

        return {
            ...this.stats,
            avgDataSizeKB: avgSize,
            duplicatePercent: ((this.stats.duplicateRequests / this.stats.totalRequests) * 100).toFixed(1),
            largePercent: ((this.stats.largeRequests / this.stats.totalRequests) * 100).toFixed(1),
            totalDataSizeMB: (this.stats.totalDataSize / 1024 / 1024).toFixed(2)
        };
    }

    /**
     * Print detailed report
     */
    printReport() {
        console.group('📊 Network Monitor Report');
        console.log('Total Requests:', this.stats.totalRequests);
        console.log('Total Data:', (this.stats.totalDataSize / 1024).toFixed(2), 'KB');
        console.log('Duplicate Requests:', this.stats.duplicateRequests);
        console.log('Large Requests (>50KB):', this.stats.largeRequests);
        
        console.group('Requests by Endpoint:');
        for (const [endpoint, data] of Object.entries(this.stats.requestsByEndpoint)) {
            console.log(
                `${endpoint}: ${data.count} requests, ${(data.totalSize / 1024).toFixed(1)}KB`
            );
        }
        console.groupEnd();
        
        console.group('Recent Requests:');
        this.requests.slice(-10).forEach(r => {
            console.log(`${r.endpoint} (${r.duration}ms, ${(r.dataSize / 1024).toFixed(1)}KB)`);
        });
        console.groupEnd();
        
        console.groupEnd();
    }

    /**
     * Clear statistics
     */
    clear() {
        this.requests = [];
        this.stats = {
            totalRequests: 0,
            totalDataSize: 0,
            duplicateRequests: 0,
            largeRequests: 0,
            requestsByEndpoint: {}
        };
        console.log('🗑️ Network monitor cleared');
    }
}

window.networkMonitor = new NetworkMonitor();

// Helper function to toggle monitoring
window.toggleNetworkMonitor = function(enable) {
    if (enable === undefined) {
        enable = !window.networkMonitor.isEnabled;
    }
    window.networkMonitor.setEnabled(enable);
    if (enable) {
        console.log('🔍 Network Monitor: Type `networkMonitor.printReport()` to see stats');
    }
};
