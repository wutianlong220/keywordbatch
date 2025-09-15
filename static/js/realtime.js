/**
 * Real-time Progress Monitor
 * Handles real-time progress updates and notifications
 */

class ProgressMonitor {
    constructor() {
        this.activeJobs = new Map();
        this.updateInterval = null;
        this.notificationCallbacks = new Map();
    }

    /**
     * Start monitoring a job
     * @param {string} jobId - Job ID to monitor
     * @param {Object} callbacks - Callback functions for updates
     */
    startMonitoring(jobId, callbacks = {}) {
        if (this.activeJobs.has(jobId)) {
            return; // Already monitoring
        }

        this.activeJobs.set(jobId, {
            lastUpdate: null,
            callbacks: callbacks,
            completed: false
        });

        if (!this.updateInterval) {
            this.startUpdateLoop();
        }

        console.log(`Started monitoring job: ${jobId}`);
    }

    /**
     * Stop monitoring a job
     * @param {string} jobId - Job ID to stop monitoring
     */
    stopMonitoring(jobId) {
        this.activeJobs.delete(jobId);

        if (this.activeJobs.size === 0 && this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }

        console.log(`Stopped monitoring job: ${jobId}`);
    }

    /**
     * Start the update loop
     */
    startUpdateLoop() {
        this.updateInterval = setInterval(() => {
            this.updateAllJobs();
        }, 1000); // Update every second
    }

    /**
     * Update all active jobs
     */
    async updateAllJobs() {
        for (const [jobId, jobData] of this.activeJobs) {
            if (jobData.completed) continue;

            try {
                const response = await fetch(`/api/stream-progress/${jobId}?last_update=${jobData.lastUpdate || ''}`);

                if (!response.ok) {
                    if (response.status === 404) {
                        this.handleJobNotFound(jobId);
                    }
                    continue;
                }

                const status = await response.json();

                // Check if we have new data
                if (jobData.lastUpdate !== status.progress.last_updated) {
                    jobData.lastUpdate = status.progress.last_updated;

                    // Call update callbacks
                    if (jobData.callbacks.onProgress) {
                        jobData.callbacks.onProgress(status);
                    }

                    // Check for completion
                    if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
                        jobData.completed = true;
                        if (jobData.callbacks.onComplete) {
                            jobData.callbacks.onComplete(status);
                        }

                        // Send notification
                        this.showJobCompletionNotification(jobId, status);
                    }
                }
            } catch (error) {
                console.error(`Error updating job ${jobId}:`, error);
            }
        }
    }

    /**
     * Handle job not found
     * @param {string} jobId - Job ID that was not found
     */
    handleJobNotFound(jobId) {
        const jobData = this.activeJobs.get(jobId);
        if (jobData && jobData.callbacks.onError) {
            jobData.callbacks.onError({ message: 'Job not found' });
        }
        this.stopMonitoring(jobId);
    }

    /**
     * Show job completion notification
     * @param {string} jobId - Completed job ID
     * @param {Object} status - Job status
     */
    showJobCompletionNotification(jobId, status) {
        const title = status.status === 'completed' ? '处理完成' : '处理结束';
        const message = status.status === 'completed'
            ? `任务 ${jobId} 已成功完成处理 ${status.progress.processed_keywords} 个关键词`
            : `任务 ${jobId} 已结束，状态：${status.status}`;

        this.showNotification(title, message, status.status === 'completed' ? 'success' : 'warning');
    }

    /**
     * Show system notification
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {string} type - Notification type
     */
    showNotification(title, message, type = 'info') {
        // Browser notification if permitted
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: '/static/images/icon.png'
            });
        }

        // In-app notification
        this.showInAppNotification(title, message, type);
    }

    /**
     * Show in-app notification
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {string} type - Notification type
     */
    showInAppNotification(title, message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} alert-dismissible fade show notification-toast`;
        notification.innerHTML = `
            <strong>${title}</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add to notification container
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }

        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Request notification permission
     */
    requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
}

/**
 * LogManager for real-time log display
 */
class LogManager {
    constructor() {
        this.logContainer = null;
        this.autoScroll = true;
        this.maxLogs = 100;
        this.filters = {
            level: null,
            category: null,
            jobId: null
        };
    }

    /**
     * Initialize log manager
     * @param {string} containerId - ID of log container
     */
    init(containerId) {
        this.logContainer = document.getElementById(containerId);
        if (this.logContainer) {
            this.startLogUpdates();
        }
    }

    /**
     * Start log updates
     */
    startLogUpdates() {
        setInterval(() => {
            this.updateLogs();
        }, 2000); // Update every 2 seconds
    }

    /**
     * Update logs display
     */
    async updateLogs() {
        if (!this.logContainer) return;

        try {
            const params = new URLSearchParams();
            if (this.filters.level) params.append('level', this.filters.level);
            if (this.filters.category) params.append('category', this.filters.category);
            if (this.filters.jobId) params.append('jobId', this.filters.jobId);
            params.append('limit', this.maxLogs);

            const response = await fetch(`/api/logs?${params}`);
            if (!response.ok) return;

            const data = await response.json();
            this.displayLogs(data.logs);
        } catch (error) {
            console.error('Error updating logs:', error);
        }
    }

    /**
     * Display logs in container
     * @param {Array} logs - Log entries to display
     */
    displayLogs(logs) {
        const currentLogs = this.logContainer.innerHTML;
        const newLogsHtml = logs.map(log => this.createLogEntryHtml(log)).join('');

        if (currentLogs !== newLogsHtml) {
            this.logContainer.innerHTML = newLogsHtml;
            if (this.autoScroll) {
                this.logContainer.scrollTop = this.logContainer.scrollHeight;
            }
        }
    }

    /**
     * Create HTML for a log entry
     * @param {Object} log - Log entry
     * @returns {string} HTML string
     */
    createLogEntryHtml(log) {
        const levelClass = {
            'debug': 'text-muted',
            'info': 'text-info',
            'warning': 'text-warning',
            'error': 'text-danger',
            'success': 'text-success'
        }[log.level] || 'text-secondary';

        const levelIcon = {
            'debug': '🔧',
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅'
        }[log.level] || '📝';

        const time = new Date(log.timestamp).toLocaleTimeString();

        return `
            <div class="log-entry ${levelClass}">
                <span class="log-time">[${time}]</span>
                <span class="log-level">${levelIcon}</span>
                <span class="log-category">[${log.category}]</span>
                <span class="log-message">${this.escapeHtml(log.message)}</span>
                ${log.job_id ? `<span class="log-job-id">(${log.job_id})</span>` : ''}
            </div>
        `;
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Set log filters
     * @param {Object} filters - Filter criteria
     */
    setFilters(filters) {
        this.filters = { ...this.filters, ...filters };
        this.updateLogs();
    }

    /**
     * Clear logs
     */
    clearLogs() {
        if (this.logContainer) {
            this.logContainer.innerHTML = '';
        }
    }
}

/**
 * Keyboard shortcuts
 */
class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.init();
    }

    /**
     * Initialize keyboard shortcuts
     */
    init() {
        document.addEventListener('keydown', (e) => {
            // Don't trigger shortcuts when typing in input fields
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            const key = e.key.toLowerCase();
            const modifiers = [];
            if (e.ctrlKey) modifiers.push('ctrl');
            if (e.altKey) modifiers.push('alt');
            if (e.shiftKey) modifiers.push('shift');

            const shortcut = [...modifiers, key].join('+');

            if (this.shortcuts.has(shortcut)) {
                e.preventDefault();
                this.shortcuts.get(shortcut)();
            }
        });
    }

    /**
     * Register a keyboard shortcut
     * @param {string} shortcut - Shortcut combination
     * @param {Function} callback - Function to call
     */
    register(shortcut, callback) {
        this.shortcuts.set(shortcut.toLowerCase(), callback);
    }
}

// Global instances
const progressMonitor = new ProgressMonitor();
const logManager = new LogManager();
const keyboardShortcuts = new KeyboardShortcuts();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Request notification permission
    progressMonitor.requestNotificationPermission();

    // Initialize log manager if container exists
    const logContainer = document.getElementById('log-container');
    if (logContainer) {
        logManager.init('log-container');
    }

    // Register default shortcuts
    keyboardShortcuts.register('ctrl+s', () => {
        // Save or start processing
        const startButton = document.getElementById('startProcessing');
        if (startButton && !startButton.disabled) {
            startButton.click();
        }
    });

    keyboardShortcuts.register('escape', () => {
        // Close modals or cancel operations
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
        });
    });
});

// Export for use in other modules
window.ProgressMonitor = ProgressMonitor;
window.LogManager = LogManager;
window.KeyboardShortcuts = KeyboardShortcuts;
window.progressMonitor = progressMonitor;
window.logManager = logManager;
window.keyboardShortcuts = keyboardShortcuts;