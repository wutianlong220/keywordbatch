// Batch Processor JavaScript for Keyword Processing Tool

document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let inputFolderPath = '';
    let outputFolderPath = '';
    let isProcessing = false;
    let isPaused = false;
    let processingInterval = null;
    let currentJobId = null;
    
    // DOM elements
    const inputFolderPathEl = document.getElementById('inputFolderPath');
    const outputFolderPathEl = document.getElementById('outputFolderPath');
    const startBtn = document.getElementById('startProcessingBtn');
    const pauseBtn = document.getElementById('pauseProcessingBtn');
    const stopBtn = document.getElementById('stopProcessingBtn');
    const clearLogBtn = document.getElementById('clearLogBtn');
    const exportLogBtn = document.getElementById('exportLogBtn');
    const newTaskBtn = document.getElementById('newTaskBtn');
    const logContainer = document.getElementById('logContainer');
    const currentStatusEl = document.getElementById('currentStatus');
    const overallProgressBar = document.getElementById('overallProgressBar');
    const totalFilesEl = document.getElementById('totalFiles');
    const completedFilesEl = document.getElementById('completedFiles');
    const failedFilesEl = document.getElementById('failedFiles');
    const currentFileEl = document.getElementById('currentFile');
    const summaryPanel = document.getElementById('summaryPanel');
    const summaryContent = document.getElementById('summaryContent');
    
    // Folder selection handlers
    window.selectInputFolder = function() {
        document.getElementById('inputFolderInput').click();
    };
    
    window.selectOutputFolder = function() {
        document.getElementById('outputFolderInput').click();
    };
    
    // File input change handlers
    document.getElementById('inputFolderInput').addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            // Get the folder path from the first file
            const firstFile = e.target.files[0];
            const path = firstFile.webkitRelativePath.split('/')[0];
            inputFolderPath = path;
            inputFolderPathEl.innerHTML = `<i class="fas fa-folder text-primary"></i> ${path}`;
            updateStartButton();
            addLog(`输入文件夹已选择: ${path}`, 'success');
        }
    });
    
    document.getElementById('outputFolderInput').addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            // Get the folder path from the first file
            const firstFile = e.target.files[0];
            const path = firstFile.webkitRelativePath.split('/')[0];
            outputFolderPath = path;
            outputFolderPathEl.innerHTML = `<i class="fas fa-folder text-success"></i> ${path}`;
            updateStartButton();
            addLog(`输出文件夹已选择: ${path}`, 'success');
        }
    });
    
    // Update start button state
    function updateStartButton() {
        startBtn.disabled = !inputFolderPath || !outputFolderPath || isProcessing;
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
    
    // Update progress
    function updateProgress(total, completed, failed, currentFile) {
        totalFilesEl.textContent = total;
        completedFilesEl.textContent = completed;
        failedFilesEl.textContent = failed;
        currentFileEl.textContent = currentFile || '-';
        
        const progress = total > 0 ? Math.round((completed / total) * 100) : 0;
        overallProgressBar.style.width = progress + '%';
        overallProgressBar.textContent = progress + '%';
        overallProgressBar.setAttribute('aria-valuenow', progress);
    }
    
    // Start processing
    startBtn.addEventListener('click', async function() {
        if (!inputFolderPath || !outputFolderPath) {
            addLog('请先选择输入和输出文件夹', 'warning');
            return;
        }
        
        if (isProcessing) {
            addLog('正在处理中，请稍候...', 'info');
            return;
        }
        
        try {
            // Reset UI state
            isProcessing = true;
            isPaused = false;
            updateStartButton();
            pauseBtn.disabled = false;
            stopBtn.disabled = false;
            currentStatusEl.textContent = '扫描文件';
            currentStatusEl.className = 'badge bg-warning';
            summaryPanel.style.display = 'none';
            
            addLog('开始批量处理任务...', 'info');
            addLog(`输入文件夹: ${inputFolderPath}`, 'info');
            addLog(`输出文件夹: ${outputFolderPath}`, 'info');
            
            // Start processing
            const response = await fetch('/api/batch-process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    input_folder: inputFolderPath,
                    output_folder: outputFolderPath
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                currentJobId = result.job_id;
                addLog(`处理任务已启动，任务ID: ${result.job_id}`, 'success');
                
                // Start polling for status updates
                startStatusPolling();
            } else {
                addLog(`启动失败: ${result.error}`, 'error');
                resetProcessingState();
            }
            
        } catch (error) {
            addLog(`网络错误: ${error.message}`, 'error');
            resetProcessingState();
        }
    });
    
    // Pause/Resume processing
    pauseBtn.addEventListener('click', async function() {
        if (!currentJobId) return;
        
        try {
            const action = isPaused ? 'resume' : 'pause';
            const response = await fetch(`/api/job-control/${currentJobId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action: action })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                isPaused = !isPaused;
                pauseBtn.innerHTML = isPaused ? '<i class="fas fa-play"></i> 继续处理' : '<i class="fas fa-pause"></i> 暂停处理';
                pauseBtn.className = isPaused ? 'btn btn-success btn-lg px-5 ms-3' : 'btn btn-warning btn-lg px-5 ms-3';
                addLog(isPaused ? '处理已暂停' : '处理已继续', 'warning');
            } else {
                addLog(`操作失败: ${result.error}`, 'error');
            }
            
        } catch (error) {
            addLog(`网络错误: ${error.message}`, 'error');
        }
    });
    
    // Stop processing
    stopBtn.addEventListener('click', async function() {
        if (!currentJobId) return;
        
        if (confirm('确定要停止处理任务吗？')) {
            try {
                const response = await fetch(`/api/job-control/${currentJobId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ action: 'stop' })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    addLog('处理任务已停止', 'warning');
                    resetProcessingState();
                } else {
                    addLog(`停止失败: ${result.error}`, 'error');
                }
                
            } catch (error) {
                addLog(`网络错误: ${error.message}`, 'error');
            }
        }
    });
    
    // Status polling
    function startStatusPolling() {
        if (processingInterval) {
            clearInterval(processingInterval);
        }
        
        // Poll every 2 seconds
        processingInterval = setInterval(async () => {
            if (!currentJobId) return;
            
            try {
                const response = await fetch(`/api/job-status/${currentJobId}`);
                const status = await response.json();
                
                if (response.ok) {
                    updateJobStatus(status);
                    
                    // Stop polling if job is completed or failed
                    if (status.status === 'completed' || status.status === 'failed') {
                        clearInterval(processingInterval);
                        showSummary(status);
                        resetProcessingState();
                    }
                } else {
                    addLog(`获取状态失败: ${status.error}`, 'error');
                }
                
            } catch (error) {
                addLog(`状态查询错误: ${error.message}`, 'error');
            }
        }, 2000);
    }
    
    // Update job status display
    function updateJobStatus(status) {
        // Update status badge
        currentStatusEl.textContent = getStatusText(status.status);
        currentStatusEl.className = `badge ${getStatusBadge(status.status)}`;
        
        // Update progress
        updateProgress(
            status.total_files || 0,
            status.completed_files || 0,
            status.failed_files || 0,
            status.current_file || ''
        );
        
        // Update current processing info
        if (status.current_batch && status.total_batches) {
            currentFileEl.textContent = `${status.current_file} (批次 ${status.current_batch}/${status.total_batches})`;
        }
    }
    
    // Get status text
    function getStatusText(status) {
        switch (status) {
            case 'scanning': return '扫描文件';
            case 'processing': return '正在处理';
            case 'paused': return '已暂停';
            case 'completed': return '已完成';
            case 'failed': return '处理失败';
            default: return '未知状态';
        }
    }
    
    // Get status badge class
    function getStatusBadge(status) {
        switch (status) {
            case 'scanning': return 'bg-info';
            case 'processing': return 'bg-warning';
            case 'paused': return 'bg-secondary';
            case 'completed': return 'bg-success';
            case 'failed': return 'bg-danger';
            default: return 'bg-primary';
        }
    }
    
    // Show processing summary
    function showSummary(status) {
        summaryPanel.style.display = 'block';
        summaryContent.innerHTML = `
            <div class="row">
                <div class="col-md-3">
                    <div class="text-center">
                        <div class="stat-value">${status.total_files || 0}</div>
                        <div class="stat-label">总文件数</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <div class="stat-value text-success">${status.completed_files || 0}</div>
                        <div class="stat-label">成功处理</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <div class="stat-value text-danger">${status.failed_files || 0}</div>
                        <div class="stat-label">处理失败</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <div class="stat-value text-primary">${status.processing_time || '0分钟'}</div>
                        <div class="stat-label">处理时间</div>
                    </div>
                </div>
            </div>
            ${status.failed_files > 0 ? `
                <div class="mt-3">
                    <h6>失败文件列表:</h6>
                    <ul class="mb-0">
                        ${(status.failed_file_list || []).map(file => `<li>${file}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        `;
    }
    
    // Reset processing state
    function resetProcessingState() {
        isProcessing = false;
        isPaused = false;
        currentJobId = null;
        updateStartButton();
        pauseBtn.disabled = true;
        stopBtn.disabled = true;
        pauseBtn.innerHTML = '<i class="fas fa-pause"></i> 暂停处理';
        pauseBtn.className = 'btn btn-warning btn-lg px-5 ms-3';
        
        if (processingInterval) {
            clearInterval(processingInterval);
            processingInterval = null;
        }
    }
    
    // Clear log
    clearLogBtn.addEventListener('click', function() {
        logContainer.innerHTML = '';
        addLog('日志已清除', 'info');
    });
    
    // Export log
    exportLogBtn.addEventListener('click', function() {
        const logText = logContainer.innerText;
        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `processing_log_${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        addLog('日志已导出', 'success');
    });
    
    // New task
    newTaskBtn.addEventListener('click', function() {
        if (confirm('确定要开始新任务吗？当前进度将会丢失。')) {
            location.reload();
        }
    });
    
    // Initialize
    addLog('批量处理工具已启动', 'info');
    addLog('请选择输入和输出文件夹，然后点击开始处理', 'info');
});