/**
 * Auto-Analysis Scheduler Manager
 * Controls background pair analysis jobs
 */

class SchedulerManager {
    constructor() {
        this.isRunning = false;
        this.currentJob = null;
        this.refreshInterval = null;
    }

    /**
     * Start auto-analysis
     */
    async startAutoAnalysis() {
        try {
            const token = getAuthToken();
            if (!token) return;

            // Get monitored pairs from settings
            const pairs = Array.from(document.querySelectorAll('.pair-checkbox:checked'))
                .map(cb => cb.value);
            
            if (pairs.length === 0) {
                this.showError('Please select at least one pair to monitor');
                return;
            }

            const interval = parseInt(document.getElementById('analysis-interval')?.value || 3600);

            const response = await fetch(APIConfig.buildUrl('/api/auto-analysis/start'), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    pairs: pairs,
                    interval_seconds: interval
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.isRunning = true;
                this.updateSchedulerUI();
                this.showSuccess(`Auto-analysis started for ${pairs.length} pairs`);
                this.startStatusRefresh();
            } else {
                this.showError('Failed to start auto-analysis');
            }
        } catch (error) {
            console.error('Error starting auto-analysis:', error);
            this.showError('Error starting auto-analysis');
        }
    }

    /**
     * Stop auto-analysis
     */
    async stopAutoAnalysis() {
        try {
            const token = getAuthToken();
            if (!token) return;

            const response = await fetch(APIConfig.buildUrl('/api/auto-analysis/stop'), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                this.isRunning = false;
                this.stopStatusRefresh();
                this.updateSchedulerUI();
                this.showSuccess('Auto-analysis stopped');
            } else {
                this.showError('Failed to stop auto-analysis');
            }
        } catch (error) {
            console.error('Error stopping auto-analysis:', error);
            this.showError('Error stopping auto-analysis');
        }
    }

    /**
     * Pause auto-analysis
     */
    async pauseAutoAnalysis() {
        try {
            // Note: This would require implementing pause in backend
            this.showInfo('Pause feature coming soon');
        } catch (error) {
            console.error('Error pausing auto-analysis:', error);
        }
    }

    /**
     * Resume auto-analysis
     */
    async resumeAutoAnalysis() {
        try {
            // Note: This would require implementing resume in backend
            this.showInfo('Resume feature coming soon');
        } catch (error) {
            console.error('Error resuming auto-analysis:', error);
        }
    }

    /**
     * Get current job status
     */
    async getJobStatus() {
        try {
            const token = getAuthToken();
            if (!token) return;

            const response = await fetch(APIConfig.buildUrl('/api/auto-analysis/status'), {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderJobStatus(data);
                this.isRunning = data.active;
                return data;
            }
        } catch (error) {
            console.error('Error getting job status:', error);
        }
        return null;
    }

    /**
     * Render scheduler controls
     */
    renderSchedulerControls() {
        const container = document.getElementById('scheduler-controls');
        if (!container) return;

        container.innerHTML = `
            <div class="space-y-4">
                <!-- Status Indicator -->
                <div class="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div id="status-indicator" class="w-4 h-4 rounded-full ${this.isRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'} transition"></div>
                            <div>
                                <p class="text-sm text-gray-400">Auto-Analysis Status</p>
                                <p class="text-lg font-bold text-white" id="status-text">
                                    ${this.isRunning ? 'Running' : 'Stopped'}
                                </p>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="text-xs text-gray-400">Uptime</p>
                            <p class="text-sm font-semibold text-green-400" id="uptime">--:--:--</p>
                        </div>
                    </div>
                </div>

                <!-- Job Details -->
                <div id="job-details-container"></div>

                <!-- Control Buttons -->
                <div class="flex gap-3">
                    <button onclick="schedulerManager.startAutoAnalysis()" 
                            class="flex-1 px-4 py-3 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-400 hover:to-green-500 text-white font-bold rounded-lg transition transform hover:scale-105 ${this.isRunning ? 'opacity-50 cursor-not-allowed' : ''}">
                        <i class="fas fa-play"></i> Start
                    </button>
                    <button onclick="schedulerManager.stopAutoAnalysis()" 
                            class="flex-1 px-4 py-3 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-400 hover:to-red-500 text-white font-bold rounded-lg transition transform hover:scale-105 ${!this.isRunning ? 'opacity-50 cursor-not-allowed' : ''}">
                        <i class="fas fa-stop"></i> Stop
                    </button>
                    <button onclick="schedulerManager.pauseAutoAnalysis()" 
                            class="flex-1 px-4 py-3 bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-400 hover:to-yellow-500 text-white font-bold rounded-lg transition transform hover:scale-105 ${!this.isRunning ? 'opacity-50 cursor-not-allowed' : ''}">
                        <i class="fas fa-pause"></i> Pause
                    </button>
                    <button onclick="schedulerManager.getJobStatus()" 
                            class="px-4 py-3 bg-slate-600 hover:bg-slate-500 text-white font-bold rounded-lg transition">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                </div>

                <!-- Quick Info -->
                <div class="grid grid-cols-2 gap-3 text-sm">
                    <div class="bg-slate-600/30 rounded p-3">
                        <p class="text-gray-400">Pairs Monitored</p>
                        <p class="text-xl font-bold text-blue-400" id="pair-count">0</p>
                    </div>
                    <div class="bg-slate-600/30 rounded p-3">
                        <p class="text-gray-400">Next Run</p>
                        <p class="text-sm font-semibold text-green-400" id="next-run">--</p>
                    </div>
                    <div class="bg-slate-600/30 rounded p-3">
                        <p class="text-gray-400">Interval</p>
                        <p class="text-sm font-semibold text-yellow-400" id="interval-display">--</p>
                    </div>
                    <div class="bg-slate-600/30 rounded p-3">
                        <p class="text-gray-400">Last Run</p>
                        <p class="text-sm font-semibold text-purple-400" id="last-run">Never</p>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render job status details
     */
    renderJobStatus(data) {
        const container = document.getElementById('job-details-container');
        if (!container) return;

        if (!data.jobs || data.jobs.length === 0) {
            container.innerHTML = '';
            return;
        }

        const job = data.jobs[0];
        const interval = job.interval_seconds;
        const intervalText = this.formatInterval(interval);

        container.innerHTML = `
            <div class="bg-slate-600/30 rounded-lg p-4 border border-slate-600">
                <h4 class="text-sm font-bold text-white mb-3 flex items-center gap-2">
                    <i class="fas fa-info-circle text-blue-400"></i> Job Details
                </h4>
                <div class="space-y-2 text-sm">
                    <div class="flex justify-between">
                        <span class="text-gray-400">Pairs:</span>
                        <span class="text-white font-semibold">${job.pairs.join(', ')}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Interval:</span>
                        <span class="text-green-400 font-semibold">${intervalText}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Next Run:</span>
                        <span class="text-yellow-400 font-semibold">${job.next_run ? new Date(job.next_run).toLocaleTimeString() : 'Pending'}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Status:</span>
                        <span class="text-blue-400 font-semibold">${job.enabled ? '✓ Enabled' : '✗ Disabled'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Format interval to human-readable text
     */
    formatInterval(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
        if (seconds < 86400) return `${Math.round(seconds / 3600)}h`;
        return `${Math.round(seconds / 86400)}d`;
    }

    /**
     * Start periodic status refresh
     */
    startStatusRefresh() {
        this.refreshInterval = setInterval(() => {
            this.getJobStatus();
        }, 5000);
    }

    /**
     * Stop status refresh
     */
    stopStatusRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Update scheduler UI based on current state
     */
    updateSchedulerUI() {
        const startBtn = document.querySelector('button[onclick*="startAutoAnalysis"]');
        const stopBtn = document.querySelector('button[onclick*="stopAutoAnalysis"]');
        const pauseBtn = document.querySelector('button[onclick*="pauseAutoAnalysis"]');

        if (startBtn) startBtn.classList.toggle('opacity-50', this.isRunning);
        if (stopBtn) stopBtn.classList.toggle('opacity-50', !this.isRunning);
        if (pauseBtn) pauseBtn.classList.toggle('opacity-50', !this.isRunning);
    }

    /**
     * Show success notification
     */
    showSuccess(message) {
        const notification = document.createElement('div');
        notification.className = 'fixed bottom-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-fadeIn z-50';
        notification.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    /**
     * Show error notification
     */
    showError(message) {
        const notification = document.createElement('div');
        notification.className = 'fixed bottom-4 right-4 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-fadeIn z-50';
        notification.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    /**
     * Show info notification
     */
    showInfo(message) {
        const notification = document.createElement('div');
        notification.className = 'fixed bottom-4 right-4 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-fadeIn z-50';
        notification.innerHTML = `<i class="fas fa-info-circle"></i> ${message}`;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }
}

// Global instance
const schedulerManager = new SchedulerManager();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        schedulerManager.renderSchedulerControls();
        schedulerManager.getJobStatus();
    }, 1000);
});
