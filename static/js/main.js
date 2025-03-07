
// Theme Toggle Functionality
function initThemeToggle() {
    const toggleSwitch = document.getElementById('theme-toggle');
    const themeLabel = document.getElementById('theme-label');
    
    function switchTheme(e) {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            themeLabel.textContent = 'Light Mode';
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            themeLabel.textContent = 'Dark Mode';
            localStorage.setItem('theme', 'light');
        }
    }
    
    // Check for saved theme preference
    const currentTheme = localStorage.getItem('theme') || 'light';
    if (currentTheme === 'dark') {
        toggleSwitch.checked = true;
        document.documentElement.setAttribute('data-theme', 'dark');
        themeLabel.textContent = 'Light Mode';
    }
    
    toggleSwitch.addEventListener('change', switchTheme);
}

// Mobile Menu Toggle
function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const navLinks = document.getElementById('nav-links');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });
    }
}

// Toast Notifications
function showToast(type, title, message, duration = 5000) {
    const toastContainer = document.getElementById('toast-container');
    
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let iconClass = 'fas fa-info-circle';
    if (type === 'success') iconClass = 'fas fa-check-circle';
    if (type === 'error') iconClass = 'fas fa-exclamation-circle';
    if (type === 'warning') iconClass = 'fas fa-exclamation-triangle';
    
    toast.innerHTML = `
        <div class="toast-icon"><i class="${iconClass}"></i></div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <div class="toast-close"><i class="fas fa-times"></i></div>
    `;
    
    document.getElementById('toast-container').appendChild(toast);
    
    // Add click event to close button
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.style.animation = 'slide-out 0.3s forwards';
        setTimeout(() => {
            toast.remove();
        }, 300);
    });
    
    // Auto remove after duration
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = 'slide-out 0.3s forwards';
            setTimeout(() => {
                if (toast.parentNode) toast.remove();
            }, 300);
        }
    }, duration);
}

// Modal Functionality
function initModals() {
    // Open modal
    document.querySelectorAll('[data-modal-target]').forEach(button => {
        button.addEventListener('click', () => {
            const modalId = button.getAttribute('data-modal-target');
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('active');
            }
        });
    });
    
    // Close modal with close button
    document.querySelectorAll('.modal-close').forEach(closeBtn => {
        closeBtn.addEventListener('click', () => {
            closeBtn.closest('.modal-backdrop').classList.remove('active');
        });
    });
    
    // Close modal when clicking outside
    document.querySelectorAll('.modal-backdrop').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
}

// Tab Functionality
function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabGroup = tab.closest('.tabs');
            const tabId = tab.getAttribute('data-tab');
            
            // Remove active class from all tabs in this group
            tabGroup.querySelectorAll('.tab').forEach(t => {
                t.classList.remove('active');
            });
            
            // Add active class to clicked tab
            tab.classList.add('active');
            
            // Hide all tab content
            const tabContainer = tabGroup.closest('.tab-container');
            tabContainer.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Show selected tab content
            const selectedContent = tabContainer.querySelector(`.tab-content[data-tab="${tabId}"]`);
            if (selectedContent) {
                selectedContent.classList.add('active');
            }
        });
    });
}

// File Upload Preview
function initFileUpload() {
    const dropzone = document.getElementById('dropzone');
    if (!dropzone) return;
    
    const fileInput = document.getElementById('file-input');
    const preview = document.getElementById('file-preview');
    
    // Handle file selection
    fileInput.addEventListener('change', handleFiles);
    
    // Handle drag and drop
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });
    
    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });
    
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFiles();
        }
    });
    
    dropzone.addEventListener('click', () => {
        fileInput.click();
    });
    
    function handleFiles() {
        const files = fileInput.files;
        if (files.length === 0) {
            preview.innerHTML = '';
            return;
        }
        
        preview.innerHTML = '';
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const fileSize = (file.size / 1024).toFixed(2);
            const fileExt = file.name.split('.').pop().toLowerCase();
            
            let iconClass = 'fas fa-file';
            if (['jpg', 'jpeg', 'png', 'gif'].includes(fileExt)) {
                iconClass = 'fas fa-file-image';
            } else if (['mp4', 'mov', 'avi'].includes(fileExt)) {
                iconClass = 'fas fa-file-video';
            } else if (['mp3', 'wav'].includes(fileExt)) {
                iconClass = 'fas fa-file-audio';
            }
            
            const filePreview = document.createElement('div');
            filePreview.className = 'file-preview';
            filePreview.innerHTML = `
                <div class="file-preview-icon"><i class="${iconClass}"></i></div>
                <div class="file-preview-info">
                    <div class="file-preview-name">${file.name}</div>
                    <div class="file-preview-size">${fileSize} KB</div>
                </div>
                <div class="file-preview-remove" data-index="${i}"><i class="fas fa-times"></i></div>
            `;
            
            preview.appendChild(filePreview);
        }
        
        // Add event listeners for remove buttons
        document.querySelectorAll('.file-preview-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                removeFile(parseInt(btn.getAttribute('data-index')));
            });
        });
    }
    
    function removeFile(index) {
        // Create a new FileList without the removed file
        const dt = new DataTransfer();
        const files = fileInput.files;
        
        for (let i = 0; i < files.length; i++) {
            if (i !== index) {
                dt.items.add(files[i]);
            }
        }
        
        fileInput.files = dt.files;
        handleFiles();
    }
}

// Initialize Dashboard Updates
function initDashboardUpdates() {
    function updateDashboard() {
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                // Update stats
                if (document.getElementById('total-videos')) {
                    document.getElementById('total-videos').textContent = data.stats.total_videos;
                }
                if (document.getElementById('videos-today')) {
                    document.getElementById('videos-today').textContent = data.stats.videos_today;
                }
                if (document.getElementById('active-jobs')) {
                    document.getElementById('active-jobs').textContent = data.stats.active_jobs;
                }
                if (document.getElementById('success-rate')) {
                    document.getElementById('success-rate').textContent = data.stats.success_rate + '%';
                }
                
                // Update jobs list
                const jobsList = document.getElementById('jobsList');
                if (jobsList) {
                    if (data.jobs && data.jobs.length > 0) {
                        let jobsHTML = '';
                        data.jobs.forEach(job => {
                            let statusClass = `status-${job.status}`;
                            let progress = job.progress || 0;
                            
                            if (job.status === 'completed') progress = 100;
                            if (job.status === 'failed') progress = 0;
                            
                            let statusIcon = '';
                            if (job.status === 'completed') statusIcon = '<i class="fas fa-check"></i>';
                            else if (job.status === 'failed') statusIcon = '<i class="fas fa-times"></i>';
                            else if (job.status === 'paused') statusIcon = '<i class="fas fa-pause"></i>';
                            
                            jobsHTML += `
                                <div class="status-card ${statusClass}" id="job-${job.id}">
                                    <div class="status-indicator"></div>
                                    <div class="status-message">
                                        <div class="status-title">${job.niche} ${statusIcon}</div>
                                        <div class="status-detail">${job.message}</div>
                                        <div class="progress-container">
                                            <div class="progress-bar" style="width: ${progress}%"></div>
                                        </div>
                                        ${job.status === 'in-progress' ? `
                                        <div class="status-controls">
                                            <button class="btn btn-sm btn-outline pause-job" data-job-id="${job.id}">
                                                <i class="fas fa-pause"></i> Pause
                                            </button>
                                            <button class="btn btn-sm btn-danger cancel-job" data-job-id="${job.id}">
                                                <i class="fas fa-times"></i> Cancel
                                            </button>
                                        </div>
                                        ` : job.status === 'paused' ? `
                                        <div class="status-controls">
                                            <button class="btn btn-sm btn-outline resume-job" data-job-id="${job.id}">
                                                <i class="fas fa-play"></i> Resume
                                            </button>
                                            <button class="btn btn-sm btn-danger cancel-job" data-job-id="${job.id}">
                                                <i class="fas fa-times"></i> Cancel
                                            </button>
                                        </div>
                                        ` : ''}
                                    </div>
                                    <div class="status-time">
                                        <div><i class="far fa-clock"></i> ${job.started || 'N/A'}</div>
                                        <div>${job.status === 'completed' ? `<i class="far fa-check-circle"></i> Completed` : 
                                               job.status === 'failed' ? `<i class="far fa-times-circle"></i> Failed` : 
                                               job.status === 'paused' ? `<i class="far fa-pause-circle"></i> Paused` :
                                               `<i class="fas fa-spinner fa-spin"></i> In progress`}</div>
                                    </div>
                                </div>
                            `;
                        });
                        jobsList.innerHTML = jobsHTML;
                        
                        // Add event listeners for job control buttons
                        document.querySelectorAll('.pause-job').forEach(btn => {
                            btn.addEventListener('click', (e) => {
                                const jobId = btn.getAttribute('data-job-id');
                                fetch(`/job/${jobId}/pause`, { method: 'POST' })
                                    .then(response => response.json())
                                    .then(data => {
                                        if (data.success) {
                                            showToast('info', 'Job Paused', `Job #${jobId} has been paused.`);
                                        } else {
                                            showToast('error', 'Error', data.message);
                                        }
                                    });
                            });
                        });
                        
                        document.querySelectorAll('.resume-job').forEach(btn => {
                            btn.addEventListener('click', (e) => {
                                const jobId = btn.getAttribute('data-job-id');
                                fetch(`/job/${jobId}/resume`, { method: 'POST' })
                                    .then(response => response.json())
                                    .then(data => {
                                        if (data.success) {
                                            showToast('info', 'Job Resumed', `Job #${jobId} has been resumed.`);
                                        } else {
                                            showToast('error', 'Error', data.message);
                                        }
                                    });
                            });
                        });
                        
                        document.querySelectorAll('.cancel-job').forEach(btn => {
                            btn.addEventListener('click', (e) => {
                                const jobId = btn.getAttribute('data-job-id');
                                if (confirm('Are you sure you want to cancel this job?')) {
                                    fetch(`/job/${jobId}/cancel`, { method: 'POST' })
                                        .then(response => response.json())
                                        .then(data => {
                                            if (data.success) {
                                                showToast('warning', 'Job Cancelled', `Job #${jobId} has been cancelled.`);
                                            } else {
                                                showToast('error', 'Error', data.message);
                                            }
                                        });
                                }
                            });
                        });
                        
                    } else {
                        jobsList.innerHTML = `
                            <div class="empty-state">
                                <i class="fas fa-tasks"></i>
                                <p>No active jobs. Start a new automation job to see status here.</p>
                            </div>
                        `;
                    }
                }
                
                // Update video gallery
                const videoGallery = document.getElementById('videoGallery');
                if (videoGallery) {
                    if (data.videos && data.videos.length > 0) {
                        let videosHTML = '';
                        data.videos.forEach(video => {
                            videosHTML += `
                                <div class="video-item">
                                    <div class="video-thumbnail">
                                        <!-- Use onerror to fallback to placeholder if the thumbnail fails to load -->
                                        <img src="${video.thumbnail || '/static/images/placeholder.jpg'}" 
                                            alt="${video.title}" 
                                            onerror="this.onerror=null; this.src='/static/images/placeholder.jpg';">
                                        <a href="#" class="play-button" data-video-path="${video.path}" data-video-title="${video.title}"></a>
                                    </div>
                                    <div class="video-info">
                                        <h3 class="video-title">${video.title}</h3>
                                        <div class="video-meta">
                                            <span><i class="far fa-calendar-alt"></i> ${video.date}</span>
                                            <span class="badge badge-${video.uploaded ? 'success' : 'warning'}">${video.uploaded ? 'Uploaded' : 'Local'}</span>
                                        </div>
                                        <div class="video-options">
                                            <button class="btn btn-sm btn-outline preview-video" data-video-path="${video.path}" data-video-title="${video.title}">
                                                <i class="fas fa-play"></i> Preview
                                            </button>
                                            ${!video.uploaded ? `
                                            <button class="btn btn-sm btn-primary upload-video" data-video-path="${video.path}" data-video-title="${video.title}">
                                                <i class="fas fa-upload"></i> Upload
                                            </button>
                                            ` : ''}
                                        </div>
                                    </div>
                                </div>
                            `;
                        });
                        videoGallery.innerHTML = videosHTML;
                        
                        // Add event listeners for video preview
                        document.querySelectorAll('.preview-video, .play-button').forEach(btn => {
                            btn.addEventListener('click', (e) => {
                                e.preventDefault();
                                const videoPath = btn.getAttribute('data-video-path');
                                const videoTitle = btn.getAttribute('data-video-title');
                                openVideoModal(videoPath, videoTitle);
                            });
                        });
                        
                        // Add event listeners for video upload
                        document.querySelectorAll('.upload-video').forEach(btn => {
                            btn.addEventListener('click', (e) => {
                                e.preventDefault();
                                const videoPath = btn.getAttribute('data-video-path');
                                const videoTitle = btn.getAttribute('data-video-title');
                                if (confirm(`Are you sure you want to upload "${videoTitle}" to YouTube?`)) {
                                    uploadVideo(videoPath, videoTitle);
                                }
                            });
                        });
                        
                    } else {
                        videoGallery.innerHTML = `
                            <div class="empty-state">
                                <i class="fas fa-video"></i>
                                <p>No videos generated yet. Start creating content to see your videos here.</p>
                            </div>
                        `;
                    }
                }
                
                // Check for notifications
                if (data.notifications && data.notifications.length > 0) {
                    data.notifications.forEach(notification => {
                        showToast(notification.type, notification.title, notification.message);
                    });
                }
            })
            .catch(error => console.error('Error fetching status:', error));
    }
    
    // Function to open video preview modal
    function openVideoModal(videoPath, videoTitle) {
        // Create modal if it doesn't exist
        if (!document.getElementById('videoPreviewModal')) {
            const modal = document.createElement('div');
            modal.id = 'videoPreviewModal';
            modal.className = 'modal-backdrop';
            modal.innerHTML = `
                <div class="modal">
                    <div class="modal-header">
                        <div class="modal-title" id="videoModalTitle">Video Preview</div>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <video id="videoPlayer" controls style="width:100%;max-height:70vh;"></video>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            
            // Add event listener to close button
            modal.querySelector('.modal-close').addEventListener('click', () => {
                modal.classList.remove('active');
                const videoPlayer = document.getElementById('videoPlayer');
                videoPlayer.pause();
                videoPlayer.src = '';
            });
            
            // Close modal when clicking outside
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                    const videoPlayer = document.getElementById('videoPlayer');
                    videoPlayer.pause();
                    videoPlayer.src = '';
                }
            });
        }
        
        // Update modal content and open it
        const modal = document.getElementById('videoPreviewModal');
        document.getElementById('videoModalTitle').textContent = videoTitle;
        
        const videoPlayer = document.getElementById('videoPlayer');
        videoPlayer.src = `/video/${encodeURIComponent(videoPath)}`;
        
        modal.classList.add('active');
    }
    
    // Function to upload video to YouTube
    function uploadVideo(videoPath, videoTitle) {
        showToast('info', 'Upload Started', `Starting upload of "${videoTitle}" to YouTube...`);
        
        fetch('/upload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                video_path: videoPath,
                title: videoTitle
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('success', 'Upload Success', `"${videoTitle}" has been uploaded to YouTube!`);
            } else {
                showToast('error', 'Upload Failed', data.message || 'There was an error uploading the video.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('error', 'Upload Error', 'There was a network error while uploading the video.');
        });
    }
    
    // Update dashboard every 2 seconds
    setInterval(updateDashboard, 2000);
    
    // Initialize dashboard on page load
    updateDashboard();
}

// Initialize charts using Chart.js
function initCharts() {
    const viewsCanvas = document.getElementById('viewsChart');
    if (viewsCanvas) {
        fetch('/analytics/views')
            .then(response => response.json())
            .then(data => {
                const ctx = viewsCanvas.getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Views',
                            data: data.views,
                            borderColor: '#0066cc',
                            backgroundColor: 'rgba(0, 102, 204, 0.1)',
                            tension: 0.3,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    precision: 0
                                }
                            }
                        }
                    }
                });
            });
    }
    
    const performanceCanvas = document.getElementById('performanceChart');
    if (performanceCanvas) {
        fetch('/analytics/performance')
            .then(response => response.json())
            .then(data => {
                const ctx = performanceCanvas.getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.videos,
                        datasets: [{
                            label: 'Views',
                            data: data.views,
                            backgroundColor: '#0066cc'
                        }, {
                            label: 'Likes',
                            data: data.likes,
                            backgroundColor: '#28a745'
                        }, {
                            label: 'Comments',
                            data: data.comments,
                            backgroundColor: '#ffc107'
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top'
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    precision: 0
                                }
                            }
                        }
                    }
                });
            });
    }
}

// Document Ready
document.addEventListener('DOMContentLoaded', function() {
    initThemeToggle();
    initMobileMenu();
    initModals();
    initTabs();
    initFileUpload();
    initDashboardUpdates();
    
    // Load charts if the page has chart elements
    if (document.getElementById('viewsChart') || document.getElementById('performanceChart')) {
        // Dynamically load Chart.js
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        script.onload = initCharts;
        document.head.appendChild(script);
    }
    
    // Form submission handling
    const automationForm = document.getElementById('automationForm');
    if (automationForm) {
        automationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('/run', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('success', 'Job Started', `New automation job "${formData.get('niche')}" has been started.`);
                } else {
                    showToast('error', 'Error', data.message || 'There was an error starting the job.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('error', 'Submission Error', 'There was a problem with your submission.');
            });
        });
    }
});
    