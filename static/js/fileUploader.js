/**
 * Modern File Uploader UI - Jira KAN-8
 * Matches Attachment 2: Badge, progress track, status, cancel/trash action, dropzone
 */
(function(window) {
    'use strict';

    function formatBytes(bytes, decimals = 1) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    function getExt(filename) {
        const parts = filename.split('.');
        if (parts.length > 1) {
            return parts.pop().toUpperCase().slice(0, 4);
        }
        return 'FILE';
    }

    class STPFileUploader {
        constructor(container, options = {}) {
            this.container = typeof container === 'string' ? document.querySelector(container) : container;
            if (!this.container) return;

            this.options = Object.assign({
                inputName: 'training_pics',
                accept: 'image/jpeg,image/png,image/webp,image/jpg,application/pdf',
                multiple: true,
                title: 'FILE UPLOADER',
                dropText: 'Drag files here or',
                browseText: 'browse',
                maxSizeMB: 15,
                onFilesChange: null
            }, options);

            this.files = [];
            this.fileStates = new Map(); // fileId -> { percent: 100, status: 'completed' }
            this._buildDOM();
            this._bindEvents();
        }

        _buildDOM() {
            this.container.innerHTML = `
                <div class="stp-uploader-card">
                    <div class="stp-uploader-header">
                        <h4 class="stp-uploader-title">${this.options.title}</h4>
                        <span class="stp-uploader-counter" data-stp-counter>0 / 0 files completed</span>
                    </div>
                    <div class="stp-uploader-list" data-stp-list></div>
                    <div class="stp-dropzone" data-stp-dropzone>
                        <span class="stp-dropzone-text">
                            ${this.options.dropText} <span class="stp-dropzone-browse" data-stp-browse>${this.options.browseText}</span>
                        </span>
                        <input type="file" style="display: none;" 
                               name="${this.options.inputName}" 
                               accept="${this.options.accept}" 
                               ${this.options.multiple ? 'multiple' : ''} 
                               data-stp-input>
                    </div>
                </div>
            `;

            this.listEl = this.container.querySelector('[data-stp-list]');
            this.counterEl = this.container.querySelector('[data-stp-counter]');
            this.dropzoneEl = this.container.querySelector('[data-stp-dropzone]');
            this.inputEl = this.container.querySelector('[data-stp-input]');
            this.browseBtn = this.container.querySelector('[data-stp-browse]');
        }

        _bindEvents() {
            this.dropzoneEl.addEventListener('click', () => this.inputEl.click());
            this.browseBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.inputEl.click();
            });

            this.inputEl.addEventListener('change', (e) => {
                this.addFiles(Array.from(e.target.files));
            });

            // Drag and drop handlers
            ['dragenter', 'dragover'].forEach(eventName => {
                this.dropzoneEl.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.dropzoneEl.classList.add('drag-over');
                }, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                this.dropzoneEl.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.dropzoneEl.classList.remove('drag-over');
                }, false);
            });

            this.dropzoneEl.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                if (dt && dt.files && dt.files.length) {
                    this.addFiles(Array.from(dt.files));
                }
            });
        }

        addFiles(newFiles) {
            if (!this.options.multiple) {
                this.files = [];
            }
            newFiles.forEach(file => {
                // Prevent duplicate files by name and size
                const exists = this.files.some(f => f.name === file.name && f.size === file.size);
                if (!exists) {
                    const id = 'f_' + Math.random().toString(36).substr(2, 9);
                    file.__stp_id = id;
                    this.files.push(file);
                    this.fileStates.set(id, {
                        percent: 100,
                        status: 'completed',
                        sizeText: formatBytes(file.size) + ' / ' + formatBytes(file.size)
                    });
                }
            });

            this._syncNativeInput();
            this.render();
            if (typeof this.options.onFilesChange === 'function') {
                this.options.onFilesChange(this.files);
            }
        }

        removeFile(fileId) {
            this.files = this.files.filter(f => f.__stp_id !== fileId);
            this.fileStates.delete(fileId);
            this._syncNativeInput();
            this.render();
            if (typeof this.options.onFilesChange === 'function') {
                this.options.onFilesChange(this.files);
            }
        }

        _syncNativeInput() {
            try {
                const dt = new DataTransfer();
                this.files.forEach(f => dt.items.add(f));
                this.inputEl.files = dt.files;
            } catch (err) {
                console.warn('DataTransfer sync fallback:', err);
            }
        }

        render() {
            if (this.files.length === 0) {
                this.listEl.innerHTML = '';
                this.counterEl.textContent = '0 / 0 files completed';
                return;
            }

            const completedCount = Array.from(this.fileStates.values()).filter(s => s.status === 'completed').length;
            this.counterEl.textContent = `${completedCount} / ${this.files.length} files completed`;

            this.listEl.innerHTML = this.files.map(file => {
                const ext = getExt(file.name);
                const state = this.fileStates.get(file.__stp_id) || { percent: 100, status: 'completed', sizeText: formatBytes(file.size) };
                const badgeClass = `badge-${ext.toLowerCase()}`;
                const isCompleted = state.status === 'completed';
                const actionIcon = isCompleted ? '<i class="fa-solid fa-trash-can"></i>' : '<i class="fa-solid fa-xmark"></i>';

                return `
                    <div class="stp-uploader-item" data-file-id="${file.__stp_id}">
                        <div class="stp-file-badge ${badgeClass}">${ext}</div>
                        <div class="stp-file-details">
                            <p class="stp-file-name" title="${file.name}">${file.name}</p>
                            <div class="stp-file-meta">
                                <span>${state.sizeText}</span>
                                <span>•</span>
                                <span class="stp-file-status ${state.status}">
                                    ${state.status.charAt(0).toUpperCase() + state.status.slice(1)}
                                </span>
                            </div>
                            <div class="stp-progress-track">
                                <div class="stp-progress-fill" style="width: ${state.percent}%;"></div>
                            </div>
                        </div>
                        <button type="button" class="stp-file-action-btn" title="Remove file" data-remove-id="${file.__stp_id}">
                            ${actionIcon}
                        </button>
                    </div>
                `;
            }).join('');

            // Bind remove buttons
            this.listEl.querySelectorAll('[data-remove-id]').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const fid = btn.getAttribute('data-remove-id');
                    this.removeFile(fid);
                });
            });
        }

        clear() {
            this.files = [];
            this.fileStates.clear();
            this._syncNativeInput();
            this.render();
        }
    }

    window.STPFileUploader = STPFileUploader;
})(window);
