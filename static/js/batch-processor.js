// Batch Processor JavaScript for Keyword Processing Tool

document.addEventListener('DOMContentLoaded', function() {
    // Check browser compatibility for File System Access API
    checkBrowserCompatibility();

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
    
    // Path selection handlers
    window.selectInputPath = function() {
        selectFolderPath('input');
    };

    window.selectOutputPath = function() {
        selectFolderPath('output');
    };

    // Show folder path selection dialog
    async function selectFolderPath(type) {
        try {
            if ('showDirectoryPicker' in window) {
                // Use File System Access API
                const dirHandle = await window.showDirectoryPicker();

                // Try to get full path using various methods
                let fullPath = await getFullPathFromHandle(dirHandle, type);

                if (fullPath) {
                    if (type === 'input') {
                        inputFolderPath = fullPath;
                        inputFolderPathEl.textContent = fullPath;
                    } else {
                        outputFolderPath = fullPath;
                        outputFolderPathEl.textContent = fullPath;
                    }
                    updateStartButton();
                } else {
                    // Fallback to folder name if path cannot be determined
                    const fallbackPath = await constructFallbackPath(dirHandle.name, type);
                    if (type === 'input') {
                        inputFolderPath = fallbackPath;
                        inputFolderPathEl.textContent = fallbackPath;
                    } else {
                        outputFolderPath = fallbackPath;
                        outputFolderPathEl.textContent = fallbackPath;
                    }
                    updateStartButton();
                }
            } else {
                // Fallback for older browsers
                await legacyFolderSelector(type);
            }
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Folder selection failed:', error);
                addLog('文件夹选择失败: ' + error.message, 'error');
            }
        }
    }

    // Try to get full path from directory handle
    async function getFullPathFromHandle(dirHandle, type) {
        try {
            // Try to resolve the path using different approaches

            // Approach 1: Try to use file system API to get path
            if ('resolve' in dirHandle) {
                try {
                    const resolvedPath = await dirHandle.resolve();
                    if (resolvedPath && resolvedPath.length > 0) {
                        // Try to reconstruct the path
                        let pathParts = [];
                        let currentHandle = dirHandle;

                        // Try to walk up the directory tree
                        while (currentHandle && 'name' in currentHandle) {
                            pathParts.unshift(currentHandle.name);
                            // Note: We can't actually walk up due to browser security restrictions
                            break;
                        }

                        // If we got meaningful path parts, construct a path
                        if (pathParts.length > 0) {
                            // Try to get the user's home directory as a base
                            const basePath = await getUserHomeDirectory();
                            if (basePath) {
                                return `${basePath}/${pathParts.join('/')}`;
                            }
                        }
                    }
                } catch (e) {
                    console.log('Path resolution failed:', e);
                }
            }

            // Approach 2: Try to use the directory name as a clue
            const dirName = dirHandle.name;
            const commonPaths = [
                '/Users/dabaobaodemac/Desktop/关键词分析保存路径',
                '/Users/dabaobaodemac/Desktop',
                '/Users/dabaobaodemac/Documents',
                '/Users/dabaobaodemac/Downloads'
            ];

            // Check if the directory name matches common patterns
            for (const basePath of commonPaths) {
                const testPath = `${basePath}/${dirName}`;
                // We can't actually check if the path exists due to browser security
                // But we can make an educated guess
                if (await isLikelyValidPath(testPath, dirName, type)) {
                    return testPath;
                }
            }

            return null;

        } catch (error) {
            console.error('Failed to get full path:', error);
            return null;
        }
    }

    // Get user home directory (best effort)
    async function getUserHomeDirectory() {
        try {
            // Try to infer from browser environment
            if (navigator.userAgent.includes('Mac')) {
                return '/Users/dabaobaodemac';
            }
            return null;
        } catch (error) {
            return null;
        }
    }

    // Check if a path is likely valid based on naming patterns
    async function isLikelyValidPath(path, dirName, type) {
        try {
            const expectedNames = type === 'input' ?
                ['input', 'Input', '输入', '源文件', 'source'] :
                ['output', 'Output', '输出', '结果', 'result'];

            return expectedNames.some(name =>
                dirName.toLowerCase().includes(name.toLowerCase()) ||
                path.toLowerCase().includes(name.toLowerCase())
            );
        } catch (error) {
            return false;
        }
    }

    // Construct fallback path when full path cannot be determined
    async function constructFallbackPath(folderName, type) {
        const basePath = '/Users/dabaobaodemac/Desktop/关键词分析保存路径';
        return `${basePath}/${folderName}`;
    }

    // Legacy folder selector for older browsers
    async function legacyFolderSelector(type) {
        return new Promise((resolve) => {
            const input = document.createElement('input');
            input.type = 'file';
            input.style.display = 'none';
            input.setAttribute('webkitdirectory', '');
            input.setAttribute('directory', '');

            input.addEventListener('change', function(e) {
                if (e.target.files.length > 0) {
                    const firstFile = e.target.files[0];
                    const relativePath = firstFile.webkitRelativePath;
                    const folderName = relativePath.split('/')[0];

                    // Try to construct a reasonable path
                    let fullPath = `/Users/dabaobaodemac/Desktop/关键词分析保存路径/${folderName}`;

                    if (type === 'input') {
                        inputFolderPath = fullPath;
                        inputFolderPathEl.textContent = fullPath;
                    } else {
                        outputFolderPath = fullPath;
                        outputFolderPathEl.textContent = fullPath;
                    }
                    updateStartButton();
                }

                document.body.removeChild(input);
                resolve();
            });

            input.addEventListener('cancel', function() {
                document.body.removeChild(input);
                resolve();
            });

            document.body.appendChild(input);
            input.click();
        });
    }

    
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

        // Validate that input and output folders are different
        if (inputFolderPath === outputFolderPath) {
            addLog('错误：输入文件夹和输出文件夹不能相同，请选择不同的文件夹', 'error');
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

                // Start real-time monitoring
                startRealtimeMonitoring();
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

    // Initialize log manager
    logManager.init('logContainer');
});

// Real-time monitoring functions
function startRealtimeMonitoring() {
    if (!currentJobId) return;

    progressMonitor.startMonitoring(currentJobId, {
        onProgress: function(status) {
            updateJobStatus(status);
            addLog(`进度更新: ${status.progress.current_file || '无文件'} (${status.progress.processed_keywords}/${status.progress.total_keywords})`, 'info');
        },
        onComplete: function(status) {
            addLog(`任务完成: ${status.status}`, status.status === 'completed' ? 'success' : 'warning');
            showSummary(status);
            resetProcessingState();
        },
        onError: function(error) {
            addLog(`监控错误: ${error.message}`, 'error');
        }
    });

    addLog('实时监控已启动', 'success');
}

// Enhanced log functions with real-time support
function addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;

    if (logContainer) {
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    // Also add to real-time log system if available
    if (window.logManager) {
        window.logManager.showInAppNotification('日志更新', message, type);
    }
}

// Browser compatibility check
function checkBrowserCompatibility() {
    const hasFileSystemAccessAPI = 'showDirectoryPicker' in window;

    if (!hasFileSystemAccessAPI) {
        // Show compatibility warning for older browsers
        const warningDiv = document.createElement('div');
        warningDiv.className = 'alert alert-warning alert-dismissible fade show';
        warningDiv.innerHTML = `
            <strong>浏览器兼容性提示：</strong>
            您的浏览器不支持最新的文件夹选择API，可能会看到"上传"提示。
            推荐使用 Chrome 86+ 或 Edge 86+ 浏览器以获得最佳体验。
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert warning at the top of the container
        const container = document.querySelector('.col-lg-10.mx-auto');
        if (container) {
            container.insertBefore(warningDiv, container.firstChild);
        }
    }
}