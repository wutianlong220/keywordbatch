// Main JavaScript file for Keyword Batch Processing Tool

// Global variables
let currentFile = null;
let isProcessing = false;

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function validateFileType(file) {
    const allowedTypes = ['.xlsx', '.xls', '.csv'];
    const fileName = file.name.toLowerCase();
    return allowedTypes.some(type => fileName.endsWith(type));
}

function validateFileSize(file) {
    const maxSize = 50 * 1024 * 1024; // 50MB
    return file.size <= maxSize;
}

// Form validation
function validateForm() {
    const apiKey = document.getElementById('apiKey').value;
    const fileInput = document.getElementById('fileInput');
    
    if (!fileInput.files.length) {
        showNotification('请选择要处理的文件', 'warning');
        return false;
    }
    
    if (!apiKey.trim()) {
        showNotification('请输入DeepSeek API Key', 'warning');
        return false;
    }
    
    return true;
}

// Initialize tooltips
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    console.log('Keyword Batch Processing Tool initialized');
});