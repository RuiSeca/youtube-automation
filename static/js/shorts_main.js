// Theme Toggle Functionality
function initThemeToggle() {
  const toggleSwitch = document.getElementById("theme-toggle");
  const themeLabel = document.getElementById("theme-label");

  function switchTheme(e) {
    if (e.target.checked) {
      document.documentElement.setAttribute("data-theme", "dark");
      themeLabel.textContent = "Light Mode";
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.setAttribute("data-theme", "light");
      themeLabel.textContent = "Dark Mode";
      localStorage.setItem("theme", "light");
    }
  }

  // Check for saved theme preference
  const currentTheme = localStorage.getItem("theme") || "light";
  if (currentTheme === "dark") {
    toggleSwitch.checked = true;
    document.documentElement.setAttribute("data-theme", "dark");
    themeLabel.textContent = "Light Mode";
  }

  toggleSwitch.addEventListener("change", switchTheme);
}

// Mobile Menu Toggle
function initMobileMenu() {
  const mobileMenuBtn = document.getElementById("mobile-menu-btn");
  const navLinks = document.getElementById("nav-links");

  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener("click", () => {
      navLinks.classList.toggle("active");
    });
  }
}

// Toast Notifications
function showToast(type, title, message, duration = 5000) {
  const toastContainer = document.getElementById("toast-container");

  if (!toastContainer) {
    const container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  let iconClass = "fas fa-info-circle";
  if (type === "success") iconClass = "fas fa-check-circle";
  if (type === "error") iconClass = "fas fa-exclamation-circle";
  if (type === "warning") iconClass = "fas fa-exclamation-triangle";

  toast.innerHTML = `
        <div class="toast-icon"><i class="${iconClass}"></i></div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <div class="toast-close"><i class="fas fa-times"></i></div>
    `;

  document.getElementById("toast-container").appendChild(toast);

  // Add click event to close button
  toast.querySelector(".toast-close").addEventListener("click", () => {
    toast.style.animation = "slide-out 0.3s forwards";
    setTimeout(() => {
      toast.remove();
    }, 300);
  });

  // Auto remove after duration
  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.animation = "slide-out 0.3s forwards";
      setTimeout(() => {
        if (toast.parentNode) toast.remove();
      }, 300);
    }
  }, duration);
}

// Initialize Dashboard Updates
function initDashboardUpdates() {
  function updateDashboard() {
    fetch("/status")
      .then((response) => response.json())
      .then((data) => {
        // Update stats
        if (document.getElementById("total-shorts")) {
          document.getElementById("total-shorts").textContent =
            data.stats.total_videos;
        }
        if (document.getElementById("shorts-today")) {
          document.getElementById("shorts-today").textContent =
            data.stats.videos_today;
        }
        if (document.getElementById("active-jobs")) {
          document.getElementById("active-jobs").textContent =
            data.stats.active_jobs;
        }
        if (document.getElementById("success-rate")) {
          document.getElementById("success-rate").textContent =
            data.stats.success_rate + "%";
        }

        // Update jobs list
        const jobsList = document.getElementById("jobsList");
        if (jobsList) {
          if (data.jobs && data.jobs.length > 0) {
            let jobsHTML = "";
            data.jobs.forEach((job) => {
              let statusClass = `status-${job.status}`;
              let progress = job.progress || 0;

              if (job.status === "completed") progress = 100;
              if (job.status === "failed") progress = 0;

              let statusIcon = "";
              if (job.status === "completed")
                statusIcon = '<i class="fas fa-check"></i>';
              else if (job.status === "failed")
                statusIcon = '<i class="fas fa-times"></i>';
              else if (job.status === "paused")
                statusIcon = '<i class="fas fa-pause"></i>';

              jobsHTML += `
                                <div class="status-card ${statusClass}" id="job-${
                job.id
              }">
                                    <div class="status-indicator"></div>
                                    <div class="status-message">
                                        <div class="status-title">${
                                          job.niche
                                        } ${statusIcon}</div>
                                        <div class="status-detail">${
                                          job.message
                                        }</div>
                                        <div class="progress-container">
                                            <div class="progress-bar" style="width: ${progress}%"></div>
                                        </div>
                                        ${
                                          job.status === "in-progress"
                                            ? `
                                        <div class="status-controls">
                                            <button class="btn btn-sm btn-outline pause-job" data-job-id="${job.id}">
                                                <i class="fas fa-pause"></i> Pause
                                            </button>
                                            <button class="btn btn-sm btn-danger cancel-job" data-job-id="${job.id}">
                                                <i class="fas fa-times"></i> Cancel
                                            </button>
                                        </div>
                                        `
                                            : job.status === "paused"
                                            ? `
                                        <div class="status-controls">
                                            <button class="btn btn-sm btn-outline resume-job" data-job-id="${job.id}">
                                                <i class="fas fa-play"></i> Resume
                                            </button>
                                            <button class="btn btn-sm btn-danger cancel-job" data-job-id="${job.id}">
                                                <i class="fas fa-times"></i> Cancel
                                            </button>
                                        </div>
                                        `
                                            : ""
                                        }
                                    </div>
                                    <div class="status-time">
                                        <div><i class="far fa-clock"></i> ${
                                          job.started || "N/A"
                                        }</div>
                                        <div>${
                                          job.status === "completed"
                                            ? `<i class="far fa-check-circle"></i> Completed`
                                            : job.status === "failed"
                                            ? `<i class="far fa-times-circle"></i> Failed`
                                            : job.status === "paused"
                                            ? `<i class="far fa-pause-circle"></i> Paused`
                                            : `<i class="fas fa-spinner fa-spin"></i> In progress`
                                        }</div>
                                    </div>
                                </div>
                            `;
            });
            jobsList.innerHTML = jobsHTML;

            // Add event listeners for job control buttons
            document.querySelectorAll(".pause-job").forEach((btn) => {
              btn.addEventListener("click", (e) => {
                const jobId = btn.getAttribute("data-job-id");
                fetch(`/job/${jobId}/pause`, { method: "POST" })
                  .then((response) => response.json())
                  .then((data) => {
                    if (data.success) {
                      showToast(
                        "info",
                        "Job Paused",
                        `Job #${jobId} has been paused.`
                      );
                    } else {
                      showToast("error", "Error", data.message);
                    }
                  });
              });
            });

            document.querySelectorAll(".resume-job").forEach((btn) => {
              btn.addEventListener("click", (e) => {
                const jobId = btn.getAttribute("data-job-id");
                fetch(`/job/${jobId}/resume`, { method: "POST" })
                  .then((response) => response.json())
                  .then((data) => {
                    if (data.success) {
                      showToast(
                        "info",
                        "Job Resumed",
                        `Job #${jobId} has been resumed.`
                      );
                    } else {
                      showToast("error", "Error", data.message);
                    }
                  });
              });
            });

            document.querySelectorAll(".cancel-job").forEach((btn) => {
              btn.addEventListener("click", (e) => {
                const jobId = btn.getAttribute("data-job-id");
                if (confirm("Are you sure you want to cancel this job?")) {
                  fetch(`/job/${jobId}/cancel`, { method: "POST" })
                    .then((response) => response.json())
                    .then((data) => {
                      if (data.success) {
                        showToast(
                          "warning",
                          "Job Cancelled",
                          `Job #${jobId} has been cancelled.`
                        );
                      } else {
                        showToast("error", "Error", data.message);
                      }
                    });
                }
              });
            });
          } else {
            jobsList.innerHTML = `
                            <div class="empty-state">
                                <i class="fas fa-tasks"></i>
                                <p>No active jobs. Start a new Shorts automation job to see status here.</p>
                            </div>
                        `;
          }
        }

        // Update shorts gallery
        const shortsGallery = document.getElementById("shortsGallery");
        if (shortsGallery) {
          if (data.videos && data.videos.length > 0) {
            let shortsHTML = "";
            data.videos.forEach((video) => {
              shortsHTML += `
                                <div class="video-item">
                                    <div class="video-thumbnail">
                                        <div class="shorts-badge">#SHORTS</div>
                                        <!-- Use onerror to fallback to placeholder if the thumbnail fails to load -->
                                        <img src="${
                                          video.thumbnail ||
                                          "/static/images/placeholder_vertical.jpg"
                                        }" 
                                            alt="${video.title}" 
                                            onerror="this.onerror=null; this.src='/static/images/placeholder_vertical.jpg';">
                                        <a href="#" class="play-button" data-video-path="${
                                          video.path
                                        }" data-video-title="${
                video.title
              }"></a>
                                    </div>
                                    <div class="video-info">
                                        <h3 class="video-title">${
                                          video.title
                                        }</h3>
                                        <div class="video-meta">
                                            <span><i class="far fa-calendar-alt"></i> ${
                                              video.date
                                            }</span>
                                            <span class="badge badge-${
                                              video.uploaded
                                                ? "success"
                                                : "warning"
                                            }">${
                video.uploaded ? "Uploaded" : "Local"
              }</span>
                                        </div>
                                        <div class="video-options">
                                            <button class="btn btn-sm btn-outline preview-video" data-video-path="${
                                              video.path
                                            }" data-video-title="${
                video.title
              }">
                                                <i class="fas fa-play"></i> Preview
                                            </button>
                                            ${
                                              !video.uploaded
                                                ? `
                                            <button class="btn btn-sm btn-primary upload-video" data-video-path="${video.path}" data-video-title="${video.title}">
                                                <i class="fas fa-upload"></i> Upload
                                            </button>
                                            `
                                                : ""
                                            }
                                        </div>
                                    </div>
                                </div>
                            `;
            });
            shortsGallery.innerHTML = shortsHTML;

            // Add event listeners for video preview
            document
              .querySelectorAll(".preview-video, .play-button")
              .forEach((btn) => {
                btn.addEventListener("click", (e) => {
                  e.preventDefault();
                  const videoPath = btn.getAttribute("data-video-path");
                  const videoTitle = btn.getAttribute("data-video-title");
                  openVideoModal(videoPath, videoTitle);
                });
              });

            // Add event listeners for video upload
            document.querySelectorAll(".upload-video").forEach((btn) => {
              btn.addEventListener("click", (e) => {
                e.preventDefault();
                const videoPath = btn.getAttribute("data-video-path");
                const videoTitle = btn.getAttribute("data-video-title");
                if (
                  confirm(
                    `Are you sure you want to upload "${videoTitle}" to YouTube as a Short?`
                  )
                ) {
                  uploadVideo(videoPath, videoTitle);
                }
              });
            });
          } else {
            shortsGallery.innerHTML = `
                            <div class="empty-state">
                                <i class="fas fa-video"></i>
                                <p>No Shorts generated yet. Start creating content to see your Shorts here.</p>
                            </div>
                        `;
          }
        }

        // Check for notifications
        if (data.notifications && data.notifications.length > 0) {
          data.notifications.forEach((notification) => {
            showToast(
              notification.type,
              notification.title,
              notification.message
            );
          });
        }
      })
      .catch((error) => console.error("Error fetching status:", error));
  }

  // Function to open video preview modal
  function openVideoModal(videoPath, videoTitle) {
    // Create modal if it doesn't exist
    if (!document.getElementById("videoPreviewModal")) {
      const modal = document.createElement("div");
      modal.id = "videoPreviewModal";
      modal.className = "modal-backdrop";
      modal.innerHTML = `
                <div class="modal">
                    <div class="modal-header">
                        <div class="modal-title" id="videoModalTitle">Shorts Preview</div>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body" style="display: flex; justify-content: center;">
                        <video id="videoPlayer" controls style="max-height: 70vh; max-width: 100%;"></video>
                    </div>
                </div>
            `;
      document.body.appendChild(modal);

      // Add event listener to close button
      modal.querySelector(".modal-close").addEventListener("click", () => {
        modal.classList.remove("active");
        const videoPlayer = document.getElementById("videoPlayer");
        videoPlayer.pause();
        videoPlayer.src = "";
      });

      // Close modal when clicking outside
      modal.addEventListener("click", (e) => {
        if (e.target === modal) {
          modal.classList.remove("active");
          const videoPlayer = document.getElementById("videoPlayer");
          videoPlayer.pause();
          videoPlayer.src = "";
        }
      });
    }

    // Update modal content and open it
    const modal = document.getElementById("videoPreviewModal");
    document.getElementById("videoModalTitle").textContent = videoTitle;

    const videoPlayer = document.getElementById("videoPlayer");
    videoPlayer.src = `/video/${encodeURIComponent(videoPath)}`;

    modal.classList.add("active");
  }

  // Function to upload video to YouTube
  function uploadVideo(videoPath, videoTitle) {
    showToast(
      "info",
      "Upload Started",
      `Starting upload of "${videoTitle}" to YouTube as a Short...`
    );

    fetch("/upload", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        video_path: videoPath,
        title: videoTitle,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showToast(
            "success",
            "Upload Success",
            `"${videoTitle}" has been uploaded to YouTube Shorts!`
          );
        } else {
          showToast(
            "error",
            "Upload Failed",
            data.message || "There was an error uploading the video."
          );
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        showToast(
          "error",
          "Upload Error",
          "There was a network error while uploading the video."
        );
      });
  }

  // Update dashboard every 2 seconds
  setInterval(updateDashboard, 2000);

  // Initialize dashboard on page load
  updateDashboard();
}

// Document Ready
document.addEventListener("DOMContentLoaded", function () {
  initThemeToggle();
  initMobileMenu();
  initDashboardUpdates();

  // Handle trending topics click
  document.querySelectorAll(".trending-topic").forEach((btn) => {
    btn.addEventListener("click", function () {
      document.getElementById("niche").value = this.textContent.trim();
    });
  });

  // Form submission handling
  const automationForm = document.getElementById("automationForm");
  if (automationForm) {
    automationForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const formData = new FormData(this);

      fetch("/run", {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            showToast(
              "success",
              "Job Started",
              `New Shorts automation job "${formData.get(
                "niche"
              )}" has been started.`
            );
          } else {
            showToast(
              "error",
              "Error",
              data.message || "There was an error starting the job."
            );
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          showToast(
            "error",
            "Submission Error",
            "There was a problem with your submission."
          );
        });
    });
  }
});

// YouTube connection functionality
document.addEventListener("DOMContentLoaded", function () {
  // Toast notification function
  function showToast(type, title, message, duration = 5000) {
    const toastContainer = document.getElementById("toast-container");

    if (!toastContainer) {
      const container = document.createElement("div");
      container.id = "toast-container";
      container.className = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    let iconClass = "fas fa-info-circle";
    if (type === "success") iconClass = "fas fa-check-circle";
    if (type === "error") iconClass = "fas fa-exclamation-circle";
    if (type === "warning") iconClass = "fas fa-exclamation-triangle";

    toast.innerHTML = `
            <div class="toast-icon"><i class="${iconClass}"></i></div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <div class="toast-close"><i class="fas fa-times"></i></div>
        `;

    document.getElementById("toast-container").appendChild(toast);

    // Add click event to close button
    toast.querySelector(".toast-close").addEventListener("click", () => {
      toast.style.animation = "slide-out 0.3s forwards";
      setTimeout(() => {
        toast.remove();
      }, 300);
    });

    // Auto remove after duration
    setTimeout(() => {
      if (toast.parentNode) {
        toast.style.animation = "slide-out 0.3s forwards";
        setTimeout(() => {
          if (toast.parentNode) toast.remove();
        }, 300);
      }
    }, duration);
  }

  // Function to check YouTube connection status
  function checkConnectionStatus() {
    // Show loading spinner
    document.getElementById("connection-status").innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i> Checking YouTube connection status...
            </div>
        `;

    // Hide all sections
    document.getElementById("not-connected-section").style.display = "none";
    document.getElementById("connected-section").style.display = "none";
    document.getElementById("error-section").style.display = "none";

    // Check connection status
    fetch("/api/youtube/channel")
      .then((response) => response.json())
      .then((data) => {
        if (data.success && data.channel) {
          // Update connection status
          document.getElementById("connection-status").innerHTML = `
                        <div class="alert alert-success">
                            <div class="alert-icon"><i class="fas fa-check-circle"></i></div>
                            <div class="alert-content">
                                <div class="alert-message">Connected to YouTube as <strong>${data.channel.title}</strong></div>
                            </div>
                        </div>
                    `;

          // Update channel info
          document.getElementById("channel-name").textContent =
            data.channel.title;
          document.getElementById("subscriber-count").textContent =
            formatNumber(data.channel.subscriberCount);
          document.getElementById("video-count").textContent = formatNumber(
            data.channel.videoCount
          );

          // Update avatar if available
          if (data.channel.thumbnail) {
            document.getElementById("channel-avatar").src =
              data.channel.thumbnail;
          }

          // Show connected section
          document.getElementById("connected-section").style.display = "block";
        } else {
          // Show not connected section
          document.getElementById("connection-status").innerHTML = `
                        <div class="alert alert-warning">
                            <div class="alert-icon"><i class="fas fa-exclamation-triangle"></i></div>
                            <div class="alert-content">
                                <div class="alert-message">Not connected to YouTube. Please connect your channel.</div>
                            </div>
                        </div>
                    `;
          document.getElementById("not-connected-section").style.display =
            "block";
        }
      })
      .catch((error) => {
        console.error("Error checking connection status:", error);

        // Show error section
        document.getElementById("connection-status").innerHTML = `
                    <div class="alert alert-error">
                        <div class="alert-icon"><i class="fas fa-exclamation-circle"></i></div>
                        <div class="alert-content">
                            <div class="alert-message">Error checking connection status.</div>
                        </div>
                    </div>
                `;
        document.getElementById("error-section").style.display = "block";
        document.getElementById("error-message").textContent =
          "Error checking YouTube connection status. Please try again.";
      });
  }

  // Function to connect to YouTube
  function connectToYouTube() {
    // Show loading state
    document.getElementById("connect-youtube-btn").innerHTML = `
            <i class="fas fa-spinner fa-spin"></i> Connecting...
        `;
    document.getElementById("connect-youtube-btn").disabled = true;

    // Call authentication endpoint
    fetch("/api/youtube/auth?force_refresh=true")
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showToast(
            "success",
            "Connected",
            "Successfully connected to YouTube!"
          );
          // Refresh connection status
          setTimeout(checkConnectionStatus, 1000);
        } else {
          showToast(
            "error",
            "Connection Failed",
            data.message || "Failed to connect to YouTube."
          );
          document.getElementById("connect-youtube-btn").innerHTML = `
                        <i class="fas fa-plug"></i> Connect Channel
                    `;
          document.getElementById("connect-youtube-btn").disabled = false;
        }
      })
      .catch((error) => {
        console.error("Error connecting to YouTube:", error);
        showToast(
          "error",
          "Connection Error",
          "An error occurred while connecting to YouTube."
        );
        document.getElementById("connect-youtube-btn").innerHTML = `
                    <i class="fas fa-plug"></i> Connect Channel
                `;
        document.getElementById("connect-youtube-btn").disabled = false;
      });
  }

  // Function to disconnect from YouTube
  function disconnectFromYouTube() {
    if (
      confirm(
        "Are you sure you want to disconnect your YouTube channel? You will need to reconnect to upload videos."
      )
    ) {
      // Call disconnect endpoint
      fetch("/api/youtube/auth?disconnect=true")
        .then((response) => response.json())
        .then((data) => {
          showToast(
            "info",
            "Disconnected",
            "Your YouTube channel has been disconnected."
          );
          // Refresh connection status
          setTimeout(checkConnectionStatus, 1000);
        })
        .catch((error) => {
          console.error("Error disconnecting from YouTube:", error);
          showToast(
            "error",
            "Error",
            "An error occurred while disconnecting from YouTube."
          );
        });
    }
  }

  // Function to format numbers
  function formatNumber(num) {
    if (!num) return "0";

    num = parseInt(num);
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + "M";
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + "K";
    } else {
      return num.toString();
    }
  }

  // Add event listeners
  document
    .getElementById("connect-youtube-btn")
    .addEventListener("click", connectToYouTube);
  document
    .getElementById("refresh-connection-btn")
    .addEventListener("click", checkConnectionStatus);
  document
    .getElementById("retry-connection-btn")
    .addEventListener("click", checkConnectionStatus);
  document
    .getElementById("disconnect-btn")
    .addEventListener("click", disconnectFromYouTube);

  // Check connection status on page load
  checkConnectionStatus();
});
