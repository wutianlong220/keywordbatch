// Index page specific JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const fileUploadArea = document.getElementById('fileUploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    const startProcessingBtn = document.getElementById('startProcessingBtn');
    const previewBtn = document.getElementById('previewBtn');
    
    let selectedFile = null;
    
    // File upload handling
    fileUploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    fileUploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileUploadArea.classList.add('dragover');
    });
    
    fileUploadArea.addEventListener('dragleave', () => {
        fileUploadArea.classList.remove('dragover');
    });
    
    fileUploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        fileUploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });
    
    // File selection handling
    function handleFileSelection(file) {
        // Reset previous state
        hideError();
        
        // Validate file type
        if (!validateFileType(file)) {
            showError('不支持的文件格式，请选择 .xlsx, .xls 或 .csv 文件');
            return;
        }
        
        // Validate file size
        if (!validateFileSize(file)) {
            showError('文件大小超过50MB限制');
            return;
        }
        
        // Store file and update UI
        selectedFile = file;
        fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
        fileInfo.style.display = 'block';
        startProcessingBtn.disabled = false;
        previewBtn.disabled = false;
        
        showNotification('文件选择成功', 'success');
    }
    
    // Clear file
    window.clearFile = function() {
        selectedFile = null;
        fileInput.value = '';
        fileInfo.style.display = 'none';
        startProcessingBtn.disabled = true;
        previewBtn.disabled = true;
        hideError();
    };
    
    // Error handling
    function showError(message) {
        errorText.textContent = message;
        errorMessage.style.display = 'block';
    }
    
    function hideError() {
        errorMessage.style.display = 'none';
    }
    
    // Start processing
    startProcessingBtn.addEventListener('click', async function() {
        if (!validateForm()) {
            return;
        }
        
        if (isProcessing) {
            showNotification('正在处理中，请稍候...', 'info');
            return;
        }
        
        // Collect configuration
        const config = {
            apiKey: document.getElementById('apiKey').value,
            apiBase: document.getElementById('apiBase').value,
            enableTranslation: document.getElementById('enableTranslation').checked,
            enableKdroi: document.getElementById('enableKdroi').checked,
            enableLinkGeneration: document.getElementById('enableLinkGeneration').checked
        };
        
        try {
            // Show loading state
            isProcessing = true;
            startProcessingBtn.disabled = true;
            startProcessingBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>上传中...';
            
            // Upload file
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('config', JSON.stringify(config));
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Start processing
                await startProcessing(config);
            } else {
                showError(result.error || '文件上传失败');
            }
        } catch (error) {
            showError('网络错误：' + error.message);
        } finally {
            isProcessing = false;
            startProcessingBtn.disabled = false;
            startProcessingBtn.innerHTML = '<i class="fas fa-play"></i> 开始处理';
        }
    });
    
    // Start processing function
    async function startProcessing(config) {
        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Redirect to progress page
                window.location.href = `/progress?job_id=${result.job_id}`;
            } else {
                showError(result.error || '启动处理失败');
            }
        } catch (error) {
            showError('处理启动失败：' + error.message);
        }
    }
    
    // Preview functionality
    previewBtn.addEventListener('click', async function() {
        if (!selectedFile) {
            showNotification('请先选择文件', 'warning');
            return;
        }
        
        try {
            const modal = new bootstrap.Modal(document.getElementById('previewModal'));
            const previewContent = document.getElementById('previewContent');
            
            previewContent.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div><p class="mt-2">正在读取文件...</p></div>';
            modal.show();
            
            // Simulate file preview (in real implementation, this would be handled by backend)
            setTimeout(() => {
                previewContent.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        文件名: ${selectedFile.name}<br>
                        文件大小: ${formatFileSize(selectedFile.size)}<br>
                        文件类型: ${selectedFile.name.split('.').pop().toUpperCase()}
                    </div>
                    <p class="text-muted">文件预览功能需要后端支持，当前显示基本信息。</p>
                `;
            }, 1500);
            
        } catch (error) {
            showNotification('预览失败：' + error.message, 'danger');
        }
    });
    
    // Configuration change handling
    document.getElementById('apiKey').addEventListener('input', function() {
        const value = this.value;
        if (value.trim()) {
            this.classList.remove('is-invalid');
            this.classList.add('is-valid');
        } else {
            this.classList.remove('is-valid');
            this.classList.add('is-invalid');
        }
    });
    
    // Processing option interactions
    document.querySelectorAll('.processing-option input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const option = this.closest('.processing-option');
            if (this.checked) {
                option.style.borderColor = '#0d6efd';
                option.style.backgroundColor = '#e7f3ff';
            } else {
                option.style.borderColor = '#dee2e6';
                option.style.backgroundColor = 'white';
            }
        });
    });
});