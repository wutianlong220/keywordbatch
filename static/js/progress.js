// Progress page specific JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Get URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const jobId = urlParams.get('job_id') || 'sample-job-id';
    
    // DOM elements
    const statusIndicator = document.getElementById('statusIndicator');
    const jobStatus = document.getElementById('jobStatus');
    const jobDescription = document.getElementById('jobDescription');
    const timeRemaining = document.getElementById('timeRemaining');
    const processingSpeed = document.getElementById('processingSpeed');
    const mainProgressBar = document.getElementById('mainProgressBar');
    const processedCount = document.getElementById('processedCount');
    const totalCount = document.getElementById('totalCount');
    const successCount = document.getElementById('successCount');
    const errorCount = document.getElementById('errorCount');
    const logContainer = document.getElementById('logContainer');
    const resultSection = document.getElementById('resultSection');
    
    // Buttons
    const pauseBtn = document.getElementById('pauseBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const clearLogBtn = document.getElementById('clearLogBtn');
    const downloadLogBtn = document.getElementById('downloadLogBtn');
    const downloadExcelBtn = document.getElementById('downloadExcelBtn');
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');
    const newTaskBtn = document.getElementById('newTaskBtn');
    const viewReportBtn = document.getElementById('viewReportBtn');
    
    // State variables
    let isPolling = true;
    let isPaused = false;
    let pollingInterval;
    
    // Initialize
    startPolling();
    
    // Polling function
    function startPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        
        // Initial poll
        pollStatus();
        
        // Set up regular polling
        pollingInterval = setInterval(() => {
            if (!isPaused && isPolling) {
                pollStatus();
            }
        }, 2000);
    }
    
    // Poll status from server
    async function pollStatus() {
        try {
            const response = await fetch(`/api/status/${jobId}`);
            const data = await response.json();
            
            if (response.ok) {
                updateUI(data);
            } else {
                addLog('获取状态失败: ' + (data.error || '未知错误'), 'error');
            }
        } catch (error) {
            addLog('网络错误: ' + error.message, 'error');
        }
    }
    
    // Update UI with status data
    function updateUI(data) {
        // Update status indicator
        statusIndicator.className = `status-indicator ${data.status}`;
        
        // Update status text
        switch (data.status) {
            case 'running':
                jobStatus.textContent = '正在处理...';
                jobDescription.textContent = '正在处理关键词数据';
                break;
            case 'completed':
                jobStatus.textContent = '处理完成';
                jobDescription.textContent = '所有关键词已处理完成';
                showResults();
                break;
            case 'failed':
                jobStatus.textContent = '处理失败';
                jobDescription.textContent = '处理过程中出现错误';
                break;
            case 'paused':
                jobStatus.textContent = '已暂停';
                jobDescription.textContent = '处理任务已暂停';
                break;
        }
        
        // Update progress
        const progress = data.progress || 0;
        mainProgressBar.style.width = progress + '%';
        mainProgressBar.textContent = progress + '%';
        mainProgressBar.setAttribute('aria-valuenow', progress);
        
        // Update statistics
        processedCount.textContent = data.processed || 0;
        totalCount.textContent = data.total || 0;
        successCount.textContent = data.success || 0;
        errorCount.textContent = data.error || 0;
        
        // Update time remaining and processing speed
        if (data.status === 'running' && data.processed && data.total) {
            const remaining = data.total - data.processed;
            const avgTime = remaining * (data.avgProcessTime || 0.1);
            timeRemaining.textContent = `预计剩余时间: ${formatTime(avgTime)}`;
            processingSpeed.textContent = `处理速度: ${data.processingSpeed || 0} 关键词/秒`;
        }
        
        // Add sample logs for demo
        if (data.status === 'running' && Math.random() < 0.3) {
            addLog(`正在处理关键词 #${data.processed || 0}`, 'info');
        }
    }
    
    // Show results section
    function showResults() {
        resultSection.style.display = 'block';
        isPolling = false;
        
        // Update button states
        pauseBtn.disabled = true;
        pauseBtn.innerHTML = '<i class="fas fa-pause"></i> 暂停处理';
        
        addLog('处理完成！结果已生成。', 'success');
    }
    
    // Add log entry
    function addLog(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.innerHTML = `
            <span class="log-timestamp">[${timestamp}]</span> ${message}
        `;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
    
    // Format time
    function formatTime(seconds) {
        if (seconds < 60) {
            return `${Math.round(seconds)}秒`;
        } else if (seconds < 3600) {
            return `${Math.round(seconds / 60)}分钟`;
        } else {
            return `${Math.round(seconds / 3600)}小时`;
        }
    }
    
    // Button event listeners
    pauseBtn.addEventListener('click', function() {
        isPaused = !isPaused;
        if (isPaused) {
            this.innerHTML = '<i class="fas fa-play"></i> 继续处理';
            this.classList.remove('btn-danger');
            this.classList.add('btn-success');
            addLog('处理已暂停', 'warning');
        } else {
            this.innerHTML = '<i class="fas fa-pause"></i> 暂停处理';
            this.classList.remove('btn-success');
            this.classList.add('btn-danger');
            addLog('处理已继续', 'info');
        }
    });
    
    cancelBtn.addEventListener('click', function() {
        if (confirm('确定要取消处理任务吗？')) {
            isPolling = false;
            addLog('处理任务已取消', 'warning');
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        }
    });
    
    refreshBtn.addEventListener('click', function() {
        addLog('手动刷新状态', 'info');
        pollStatus();
    });
    
    clearLogBtn.addEventListener('click', function() {
        logContainer.innerHTML = '';
        addLog('日志已清除', 'info');
    });
    
    downloadLogBtn.addEventListener('click', function() {
        const logText = logContainer.innerText;
        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `processing_log_${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        addLog('日志已下载', 'success');
    });
    
    downloadExcelBtn.addEventListener('click', function() {
        addLog('正在生成Excel文件...', 'info');
        // Simulate download
        setTimeout(() => {
            addLog('Excel文件已下载', 'success');
        }, 1000);
    });
    
    downloadCsvBtn.addEventListener('click', function() {
        addLog('正在生成CSV文件...', 'info');
        // Simulate download
        setTimeout(() => {
            addLog('CSV文件已下载', 'success');
        }, 1000);
    });
    
    newTaskBtn.addEventListener('click', function() {
        window.location.href = '/';
    });
    
    viewReportBtn.addEventListener('click', function() {
        addLog('报告查看功能开发中...', 'info');
    });
    
    // Add some initial logs for demo
    addLog('系统启动，等待处理任务...', 'info');
    addLog(`任务ID: ${jobId}`, 'info');
    addLog('正在连接处理服务器...', 'info');
    
    // Simulate initial progress
    setTimeout(() => {
        addLog('开始处理关键词数据', 'success');
        addLog('初始化处理引擎...', 'info');
    }, 1000);
});