/**
 * Chart Optimizer Module
 * Optimizes Chart.js to only update new data instead of re-rendering entire chart
 */

class ChartOptimizer {
    constructor() {
        this.charts = new Map();
        this.lastDataHash = new Map();
        this.updateQueues = new Map();
    }

    /**
     * Register a chart for optimization
     */
    registerChart(chartId, chart) {
        this.charts.set(chartId, chart);
        this.updateQueues.set(chartId, []);
        console.log(`📊 Registered chart: ${chartId}`);
    }

    /**
     * Calculate hash of data for change detection
     */
    hashData(data) {
        return JSON.stringify(data);
    }

    /**
     * Check if data has changed
     */
    hasDataChanged(chartId, data) {
        const newHash = this.hashData(data);
        const oldHash = this.lastDataHash.get(chartId);
        const changed = newHash !== oldHash;
        if (changed) {
            this.lastDataHash.set(chartId, newHash);
        }
        return changed;
    }

    /**
     * Update chart incrementally instead of full re-render
     */
    updateChart(chartId, newData, datasetIndex = 0) {
        const chart = this.charts.get(chartId);
        if (!chart) {
            console.warn(`⚠️ Chart not registered: ${chartId}`);
            return;
        }

        // Check if data actually changed
        if (!this.hasDataChanged(chartId, newData)) {
            console.log(`✓ No change detected for chart: ${chartId} - skipping update`);
            return;
        }

        try {
            if (Array.isArray(newData)) {
                // For multiple datasets
                chart.data.datasets[datasetIndex].data = newData;
            } else {
                // For single dataset
                chart.data.datasets[0].data = newData;
            }

            // Use minimal update instead of full refresh
            chart.update('none');  // 'none' = no animation, instant update
            console.log(`✅ Updated chart: ${chartId}`);
        } catch (err) {
            console.error(`❌ Error updating chart ${chartId}:`, err);
        }
    }

    /**
     * Update specific data points instead of entire dataset
     */
    updateDataPoints(chartId, newPoints, datasetIndex = 0) {
        const chart = this.charts.get(chartId);
        if (!chart) return;

        const data = chart.data.datasets[datasetIndex].data;
        
        // Only update changed points
        for (const point of newPoints) {
            if (point.index < data.length) {
                data[point.index] = point.value;
            } else {
                data.push(point.value);
            }
        }

        chart.update('none');
        console.log(`✅ Updated ${newPoints.length} data points in chart: ${chartId}`);
    }

    /**
     * Batch updates to reduce repaints
     */
    queueUpdate(chartId, updateFn) {
        if (!this.updateQueues.has(chartId)) {
            this.updateQueues.set(chartId, []);
        }

        this.updateQueues.get(chartId).push(updateFn);
        
        // Process queue in next tick to batch updates
        if (this.updateQueues.get(chartId).length === 1) {
            requestAnimationFrame(() => {
                this.flushQueue(chartId);
            });
        }
    }

    /**
     * Process all queued updates at once
     */
    flushQueue(chartId) {
        const queue = this.updateQueues.get(chartId) || [];
        if (queue.length === 0) return;

        console.log(`⚡ Flushing ${queue.length} queued updates for chart: ${chartId}`);

        // Execute all updates
        for (const updateFn of queue) {
            try {
                updateFn();
            } catch (err) {
                console.error('Error executing queued update:', err);
            }
        }

        // Clear queue
        this.updateQueues.set(chartId, []);
    }

    /**
     * Get chart statistics
     */
    getStats(chartId) {
        const chart = this.charts.get(chartId);
        if (!chart) return null;

        return {
            chartId,
            datasets: chart.data.datasets.length,
            dataPoints: chart.data.datasets[0]?.data?.length || 0,
            lastHash: this.lastDataHash.get(chartId)
        };
    }
}

window.chartOptimizer = new ChartOptimizer();
