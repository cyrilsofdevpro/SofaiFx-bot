/**
 * Settings & Preferences Manager
 * Handles user preferences for monitored pairs and auto-analysis settings
 */

class SettingsManager {
    constructor() {
        this.preferences = {
            monitored_pairs: [],
            auto_analysis_enabled: false,
            auto_analysis_interval: 3600,
            min_confidence_threshold: 0.7,
            alert_on_high_confidence: false,
            alert_high_confidence_threshold: 0.8
        };
        this.isSaving = false;
    }

    /**
     * Load preferences from API
     */
    async loadPreferences() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            const response = await fetch(APIConfig.buildUrl('/api/preferences'), {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                this.preferences = await response.json();
                this.renderSettings();
            }
        } catch (error) {
            console.error('Error loading preferences:', error);
        }
    }

    /**
     * Save preferences to API
     */
    async savePreferences() {
        this.isSaving = true;
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            // Get current values from form
            const monitored_pairs = Array.from(document.querySelectorAll('.pair-checkbox:checked'))
                .map(cb => cb.value);
            
            const auto_analysis_enabled = document.getElementById('auto-analysis-toggle')?.checked || false;
            const auto_analysis_interval = parseInt(document.getElementById('analysis-interval')?.value || 3600);
            const min_confidence_threshold = parseFloat(document.getElementById('confidence-threshold')?.value || 0.7);
            const alert_on_high_confidence = document.getElementById('alert-toggle')?.checked || false;
            const alert_high_confidence_threshold = parseFloat(document.getElementById('alert-threshold')?.value || 0.8);

            const response = await fetch(APIConfig.buildUrl('/api/preferences'), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    monitored_pairs,
                    auto_analysis_enabled,
                    auto_analysis_interval,
                    min_confidence_threshold,
                    alert_on_high_confidence,
                    alert_high_confidence_threshold
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.preferences = data.preferences;
                this.showSuccess('Settings saved successfully!');
            } else {
                this.showError('Failed to save settings');
            }
        } catch (error) {
            console.error('Error saving preferences:', error);
            this.showError('Error saving settings');
        } finally {
            this.isSaving = false;
        }
    }

    /**
     * Render settings panel
     */
    renderSettings() {
        const container = document.getElementById('settings-panel');
        if (!container) return;

        const pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'EURGBP', 'EURJPY', 'NZDUSD'];

        container.innerHTML = `
            <div class="space-y-6">
                <!-- Monitored Pairs Section -->
                <div class="bg-slate-700/50 rounded-lg p-5 border border-slate-600">
                    <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <i class="fas fa-bookmark text-blue-400"></i> Monitored Pairs
                    </h3>
                    <p class="text-sm text-gray-400 mb-4">Select which pairs to monitor for analysis</p>
                    
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                        ${pairs.map(pair => `
                            <label class="flex items-center gap-3 p-3 bg-slate-600/50 rounded-lg hover:bg-slate-600 cursor-pointer transition">
                                <input type="checkbox" 
                                       class="pair-checkbox" 
                                       value="${pair}"
                                       ${this.preferences.monitored_pairs?.includes(pair) ? 'checked' : ''}
                                       onchange="settingsManager.updatePairSelection()">
                                <span class="text-white font-semibold">${pair}</span>
                            </label>
                        `).join('')}
                    </div>
                </div>

                <!-- Auto-Analysis Section -->
                <div class="bg-slate-700/50 rounded-lg p-5 border border-slate-600">
                    <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <i class="fas fa-robot text-purple-400"></i> Auto-Analysis
                    </h3>
                    
                    <div class="space-y-4">
                        <!-- Toggle -->
                        <div class="flex items-center justify-between">
                            <label class="text-white font-semibold">Enable Auto-Analysis</label>
                            <div class="toggle-switch">
                                <input type="checkbox" 
                                       id="auto-analysis-toggle"
                                       ${this.preferences.auto_analysis_enabled ? 'checked' : ''}
                                       onchange="settingsManager.toggleAutoAnalysis(this.checked)">
                                <span class="toggle-slider"></span>
                            </div>
                        </div>

                        <!-- Interval -->
                        <div>
                            <label class="block text-sm text-gray-300 mb-2">
                                Analysis Interval
                            </label>
                            <div class="flex items-center gap-3">
                                <select id="analysis-interval" 
                                        class="flex-1 px-3 py-2 bg-slate-600 border border-slate-500 rounded text-white focus:outline-none focus:border-blue-500"
                                        value="${this.preferences.auto_analysis_interval || 3600}">
                                    <option value="900">Every 15 minutes</option>
                                    <option value="1800">Every 30 minutes</option>
                                    <option value="3600">Every 1 hour</option>
                                    <option value="7200">Every 2 hours</option>
                                    <option value="14400">Every 4 hours</option>
                                    <option value="86400">Every 24 hours</option>
                                </select>
                                <button onclick="settingsManager.testInterval()" class="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded transition text-sm">
                                    <i class="fas fa-test"></i> Test
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Confidence Thresholds Section -->
                <div class="bg-slate-700/50 rounded-lg p-5 border border-slate-600">
                    <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <i class="fas fa-chart-bar text-green-400"></i> Confidence Thresholds
                    </h3>
                    
                    <div class="space-y-4">
                        <!-- Min Confidence -->
                        <div>
                            <label class="block text-sm text-gray-300 mb-2">
                                Minimum Confidence: <span class="text-green-400 font-bold" id="confidence-value">${(this.preferences.min_confidence_threshold || 0.7) * 100}%</span>
                            </label>
                            <input type="range" 
                                   id="confidence-threshold"
                                   min="0.5" max="0.99" step="0.05"
                                   value="${this.preferences.min_confidence_threshold || 0.7}"
                                   onchange="settingsManager.updateConfidenceDisplay()"
                                   class="w-full">
                            <div class="flex justify-between text-xs text-gray-500 mt-1">
                                <span>50%</span>
                                <span>99%</span>
                            </div>
                        </div>

                        <!-- High Confidence Alert -->
                        <div class="border-t border-slate-600 pt-4">
                            <div class="flex items-center justify-between mb-3">
                                <label class="text-white font-semibold">High Confidence Alerts</label>
                                <div class="toggle-switch">
                                    <input type="checkbox" 
                                           id="alert-toggle"
                                           ${this.preferences.alert_on_high_confidence ? 'checked' : ''}>
                                    <span class="toggle-slider"></span>
                                </div>
                            </div>

                            <div>
                                <label class="block text-sm text-gray-300 mb-2">
                                    Alert when confidence exceeds: <span class="text-yellow-400 font-bold" id="alert-value">${(this.preferences.alert_high_confidence_threshold || 0.8) * 100}%</span>
                                </label>
                                <input type="range" 
                                       id="alert-threshold"
                                       min="0.5" max="0.99" step="0.05"
                                       value="${this.preferences.alert_high_confidence_threshold || 0.8}"
                                       onchange="settingsManager.updateAlertDisplay()"
                                       class="w-full">
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Save Button -->
                <div class="flex gap-3">
                    <button onclick="settingsManager.savePreferences()" 
                            class="flex-1 px-4 py-3 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-400 hover:to-green-500 text-white font-bold rounded-lg transition transform hover:scale-105"
                            ${this.isSaving ? 'disabled' : ''}>
                        <i class="fas fa-save"></i> Save Settings
                    </button>
                    <button onclick="location.reload()" 
                            class="px-4 py-3 bg-slate-600 hover:bg-slate-500 text-white font-bold rounded-lg transition">
                        <i class="fas fa-redo"></i> Reset
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Update pair selection display
     */
    updatePairSelection() {
        const selected = Array.from(document.querySelectorAll('.pair-checkbox:checked'))
            .map(cb => cb.value);
        document.getElementById('pair-count').textContent = selected.length;
    }

    /**
     * Toggle auto-analysis
     */
    toggleAutoAnalysis(enabled) {
        const intervalControl = document.getElementById('analysis-interval').parentElement;
        intervalControl.style.opacity = enabled ? '1' : '0.5';
        intervalControl.style.pointerEvents = enabled ? 'auto' : 'none';
    }

    /**
     * Update confidence threshold display
     */
    updateConfidenceDisplay() {
        const value = document.getElementById('confidence-threshold').value;
        document.getElementById('confidence-value').textContent = Math.round(value * 100) + '%';
    }

    /**
     * Update alert threshold display
     */
    updateAlertDisplay() {
        const value = document.getElementById('alert-threshold').value;
        document.getElementById('alert-value').textContent = Math.round(value * 100) + '%';
    }

    /**
     * Test interval
     */
    async testInterval() {
        alert('Interval test would run in background - feature in development');
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        const notification = document.createElement('div');
        notification.className = 'fixed bottom-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-fadeIn';
        notification.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    /**
     * Show error message
     */
    showError(message) {
        const notification = document.createElement('div');
        notification.className = 'fixed bottom-4 right-4 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-fadeIn';
        notification.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }
}

// Global instance
const settingsManager = new SettingsManager();

// Load preferences on page load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        settingsManager.loadPreferences();
    }, 1000);
});
