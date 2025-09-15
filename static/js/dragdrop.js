/**
 * Drag and Drop Upload Functionality
 * Enhanced folder selection with drag-and-drop support
 */

class DragDropManager {
    constructor() {
        this.dropZones = new Map();
        this.fileProcessors = new Map();
        this.isDragging = false;
        this.init();
    }

    /**
     * Initialize drag and drop functionality
     */
    init() {
        this.setupGlobalDropListeners();
        this.setupKeyboardShortcuts();
    }

    /**
     * Setup drop zone for folder selection
     * @param {string} elementId - Drop zone element ID
     * @param {Object} options - Configuration options
     * @param {Function} callback - Callback function
     */
    setupDropZone(elementId, options = {}, callback = null) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const config = {
            type: 'folder', // 'folder' or 'file'
            multiple: true,
            accept: '*', // file types
            ...options
        };

        this.dropZones.set(elementId, { element, config, callback });

        // Setup event listeners
        element.addEventListener('dragover', this.handleDragOver.bind(this));
        element.addEventListener('dragleave', this.handleDragLeave.bind(this));
        element.addEventListener('drop', this.handleDrop.bind(this, elementId));
        element.addEventListener('click', this.handleClick.bind(this, elementId));

        // Visual feedback
        element.style.cursor = 'pointer';
        element.setAttribute('role', 'button');
        element.setAttribute('tabindex', '0');
        element.setAttribute('aria-label', `Select ${config.type} folder`);
    }

    /**
     * Handle drag over event
     * @param {DragEvent} e - Drag event
     */
    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();

        if (!this.isDragging) {
            this.isDragging = true;
            document.body.classList.add('dragging');
        }

        e.currentTarget.classList.add('drag-over');
    }

    /**
     * Handle drag leave event
     * @param {DragEvent} e - Drag event
     */
    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('drag-over');

        this.isDragging = false;
        document.body.classList.remove('dragging');
    }

    /**
     * Handle drop event
     * @param {string} zoneId - Drop zone ID
     * @param {DragEvent} e - Drop event
     */
    handleDrop(zoneId, e) {
        e.preventDefault();
        e.stopPropagation();

        const zone = this.dropZones.get(zoneId);
        if (!zone) return;

        const element = zone.element;
        element.classList.remove('drag-over');
        this.isDragging = false;
        document.body.classList.remove('dragging');

        const items = e.dataTransfer.items;
        const files = e.dataTransfer.files;

        if (items && items.length > 0) {
            this.handleDataTransferItems(items, zone);
        } else if (files && files.length > 0) {
            this.handleFiles(files, zone);
        }
    }

    /**
     * Handle data transfer items (for folder selection)
     * @param {DataTransferItemList} items - Data transfer items
     * @param {Object} zone - Drop zone configuration
     */
    handleDataTransferItems(items, zone) {
        const entries = [];
        const queue = [];

        // Collect all entries
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            if (item.kind === 'file') {
                const entry = item.webkitGetAsEntry();
                if (entry) {
                    queue.push(entry);
                }
            }
        }

        // Process entries recursively
        const processEntry = (entry) => {
            if (entry.isFile) {
                entry.file((file) => {
                    if (this.isFileAccepted(file, zone.config)) {
                        entries.push({
                            file: file,
                            path: entry.fullPath.replace(/^\//, '')
                        });
                    }
                });
            } else if (entry.isDirectory && zone.config.type === 'folder') {
                const reader = entry.createReader();
                reader.readEntries((moreEntries) => {
                    moreEntries.forEach(processEntry);
                });
            }
        };

        // Start processing
        queue.forEach(processEntry);

        // Call callback after a delay to allow processing
        setTimeout(() => {
            if (zone.callback) {
                zone.callback(entries, zone.config);
            }
        }, 100);
    }

    /**
     * Handle dropped files
     * @param {FileList} files - Dropped files
     * @param {Object} zone - Drop zone configuration
     */
    handleFiles(files, zone) {
        const acceptedFiles = Array.from(files).filter(file =>
            this.isFileAccepted(file, zone.config)
        );

        if (zone.callback) {
            zone.callback(acceptedFiles.map(file => ({
                file: file,
                path: file.name
            })), zone.config);
        }
    }

    /**
     * Check if file is accepted based on configuration
     * @param {File} file - File to check
     * @param {Object} config - Configuration
     * @returns {boolean} - Whether file is accepted
     */
    isFileAccepted(file, config) {
        if (config.accept === '*') return true;

        const extensions = config.accept.split(',').map(ext =>
            ext.trim().toLowerCase().replace('.', '')
        );

        const fileExtension = file.name.split('.').pop().toLowerCase();
        return extensions.includes(fileExtension);
    }

    /**
     * Handle click event (fallback to file input)
     * @param {string} zoneId - Drop zone ID
     * @param {Event} e - Click event
     */
    handleClick(zoneId, e) {
        const zone = this.dropZones.get(zoneId);
        if (!zone) return;

            // Create hidden file input
        const input = document.createElement('input');
        input.type = 'file';
        input.style.display = 'none';

        if (zone.config.type === 'folder') {
            input.setAttribute('webkitdirectory', '');
            input.setAttribute('directory', '');
        }

        if (zone.config.multiple) {
            input.multiple = true;
        }

        if (zone.config.accept !== '*') {
            input.accept = zone.config.accept;
        }

        input.addEventListener('change', (e) => {
            const files = Array.from(e.target.files).map(file => ({
                file: file,
                path: file.webkitRelativePath || file.name
            }));

            if (zone.callback) {
                zone.callback(files, zone.config);
            }

            // Clean up
            document.body.removeChild(input);
        });

        document.body.appendChild(input);
        input.click();
    }

    /**
     * Setup global drop listeners
     */
    setupGlobalDropListeners() {
        document.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();

            if (!this.isDragging) {
                this.isDragging = true;
                document.body.classList.add('dragging');
            }
        });

        document.addEventListener('dragleave', (e) => {
            if (e.target === document) {
                this.isDragging = false;
                document.body.classList.remove('dragging');
            }
        });

        document.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();

            // Only handle drops outside of designated drop zones
            let droppedInZone = false;
            for (const [zoneId, zone] of this.dropZones) {
                if (zone.element.contains(e.target)) {
                    droppedInZone = true;
                    break;
                }
            }

            if (!droppedInZone) {
                this.isDragging = false;
                document.body.classList.remove('dragging');
                this.showGlobalDropFeedback(e);
            }
        });
    }

    /**
     * Show feedback for global drops
     * @param {DragEvent} e - Drop event
     */
    showGlobalDropFeedback(e) {
        const toast = document.createElement('div');
        toast.className = 'alert alert-info position-fixed top-0 start-50 translate-middle-x mt-3';
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            <i class="fas fa-info-circle"></i>
            请拖拽文件到指定的文件夹选择区域
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Skip if typing in input field
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            // Ctrl+O for open file/folder
            if (e.ctrlKey && e.key === 'o') {
                e.preventDefault();
                const firstZone = this.dropZones.keys().next().value;
                if (firstZone) {
                    this.handleClick(firstZone, new Event('click'));
                }
            }

            // Escape to cancel drag operations
            if (e.key === 'Escape' && this.isDragging) {
                this.isDragging = false;
                document.body.classList.remove('dragging');
                this.dropZones.forEach(zone => {
                    zone.element.classList.remove('drag-over');
                });
            }
        });
    }

    /**
     * Register file processor for specific file types
     * @param {string} type - File type identifier
     * @param {Function} processor - Processing function
     */
    registerFileProcessor(type, processor) {
        this.fileProcessors.set(type, processor);
    }

    /**
     * Process files with registered processor
     * @param {Array} files - Files to process
     * @param {string} type - Processor type
     * @returns {Promise} - Processing result
     */
    async processFiles(files, type) {
        const processor = this.fileProcessors.get(type);
        if (!processor) {
            throw new Error(`No processor registered for type: ${type}`);
        }

        return processor(files);
    }

    /**
     * Get file statistics
     * @param {Array} files - File list
     * @returns {Object} - File statistics
     */
    getFileStats(files) {
        const stats = {
            total: files.length,
            size: 0,
            types: {},
            extensions: {}
        };

        files.forEach(({ file }) => {
            stats.size += file.size;

            // Group by type
            const type = file.type || 'unknown';
            stats.types[type] = (stats.types[type] || 0) + 1;

            // Group by extension
            const extension = file.name.split('.').pop().toLowerCase();
            stats.extensions[extension] = (stats.extensions[extension] || 0) + 1;
        });

        stats.size = this.formatFileSize(stats.size);
        return stats;
    }

    
    /**
     * Format file size
     * @param {number} bytes - File size in bytes
     * @returns {string} - Formatted size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Validate files before processing
     * @param {Array} files - Files to validate
     * @param {Object} rules - Validation rules
     * @returns {Object} - Validation result
     */
    validateFiles(files, rules = {}) {
        const errors = [];
        const validFiles = [];

        const {
            maxSize = null, // in bytes
            allowedTypes = [],
            allowedExtensions = [],
            maxFiles = null
        } = rules;

        for (let i = 0; i < files.length; i++) {
            const { file } = files[i];
            let isValid = true;

            // Check file count
            if (maxFiles && i >= maxFiles) {
                errors.push(`最多只能选择 ${maxFiles} 个文件`);
                break;
            }

            // Check file size
            if (maxSize && file.size > maxSize) {
                errors.push(`文件 ${file.name} 超过大小限制 (${this.formatFileSize(maxSize)})`);
                isValid = false;
            }

            // Check file type
            if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
                errors.push(`文件 ${file.name} 类型不被支持`);
                isValid = false;
            }

            // Check file extension
            if (allowedExtensions.length > 0) {
                const extension = file.name.split('.').pop().toLowerCase();
                if (!allowedExtensions.includes(extension)) {
                    errors.push(`文件 ${file.name} 扩展名不被支持`);
                    isValid = false;
                }
            }

            if (isValid) {
                validFiles.push(files[i]);
            }
        }

        return {
            valid: validFiles,
            errors,
            stats: this.getFileStats(validFiles)
        };
    }
}

// Global instance
const dragDropManager = new DragDropManager();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Setup folder drop zones
    if (document.getElementById('inputFolderDropZone')) {
        dragDropManager.setupDropZone('inputFolderDropZone', {
            type: 'folder',
            accept: '.xlsx,.xls,.csv'
        }, (files, config) => {
            // Handle input folder selection
            window.handleInputFolderSelection(files);
        });
    }

    if (document.getElementById('outputFolderDropZone')) {
        dragDropManager.setupDropZone('outputFolderDropZone', {
            type: 'folder'
        }, (files, config) => {
            // Handle output folder selection
            window.handleOutputFolderSelection(files);
        });
    }

    // Register Excel file processor
    dragDropManager.registerFileProcessor('excel', async (files) => {
        // Excel processing logic
        console.log('Processing Excel files:', files);
        return { processed: files.length, success: true };
    });
});

// Export for use in other modules
window.DragDropManager = DragDropManager;
window.dragDropManager = dragDropManager;