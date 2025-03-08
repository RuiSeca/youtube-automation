/**
 * YouTube Integration Module
 * This module handles YouTube authentication and API interactions on the client side
 */

// Create a namespace for YouTube functionality
const YouTubeManager = {
  // Initialize the YouTube manager
  init: function () {
    // Add event listeners for YouTube-related buttons
    this.addEventListeners();

    // Check connection status if on the settings or auth page
    if (
      document.getElementById("connection-status") ||
      document.getElementById("youtube-connection-status")
    ) {
      this.checkConnectionStatus();
    }
  },

  // Add event listeners for YouTube-related elements
  addEventListeners: function () {
    // Connect button
    const connectBtn = document.getElementById("connect-youtube-btn");
    if (connectBtn) {
      connectBtn.addEventListener("click", this.connectToYouTube.bind(this));
    }

    // Disconnect button
    const disconnectBtn = document.getElementById("disconnect-btn");
    if (disconnectBtn) {
      disconnectBtn.addEventListener(
        "click",
        this.disconnectFromYouTube.bind(this)
      );
    }

    // Refresh connection button
    const refreshBtn = document.getElementById("refresh-connection-btn");
    if (refreshBtn) {
      refreshBtn.addEventListener(
        "click",
        this.checkConnectionStatus.bind(this)
      );
    }

    // Retry connection button
    const retryBtn = document.getElementById("retry-connection-btn");
    if (retryBtn) {
      retryBtn.addEventListener("click", this.checkConnectionStatus.bind(this));
    }

    // YouTube settings form
    const youtubeSettingsForm = document.getElementById(
      "youtube-settings-form"
    );
    if (youtubeSettingsForm) {
      youtubeSettingsForm.addEventListener(
        "submit",
        this.saveYouTubeSettings.bind(this)
      );
    }
  },

  // Check YouTube connection status
  checkConnectionStatus: function () {
    const statusElement =
      document.getElementById("connection-status") ||
      document.getElementById("youtube-connection-status");

    if (!statusElement) return;

    // Show loading spinner
    statusElement.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i> Checking YouTube connection status...
            </div>
        `;

    // Hide all sections
    const notConnectedSection = document.getElementById(
      "not-connected-section"
    );
    const connectedSection = document.getElementById("connected-section");
    const errorSection = document.getElementById("error-section");

    if (notConnectedSection) notConnectedSection.style.display = "none";
    if (connectedSection) connectedSection.style.display = "none";
    if (errorSection) errorSection.style.display = "none";

    // Check connection status
    fetch("/api/youtube/channel")
      .then((response) => response.json())
      .then((data) => {
        if (data.success && data.channel) {
          // Update connection status
          statusElement.innerHTML = `
                        <div class="alert alert-success">
                            <div class="alert-icon"><i class="fas fa-check-circle"></i></div>
                            <div class="alert-content">
                                <div class="alert-message">Connected to YouTube as <strong>${data.channel.title}</strong></div>
                            </div>
                        </div>
                    `;

          // Update channel info if elements exist
          const channelNameElement = document.getElementById("channel-name");
          const subscriberCountElement =
            document.getElementById("subscriber-count");
          const videoCountElement = document.getElementById("video-count");
          const channelAvatarElement =
            document.getElementById("channel-avatar");

          if (channelNameElement)
            channelNameElement.textContent = data.channel.title;
          if (subscriberCountElement)
            subscriberCountElement.textContent = this.formatNumber(
              data.channel.subscriberCount
            );
          if (videoCountElement)
            videoCountElement.textContent = this.formatNumber(
              data.channel.videoCount
            );
          if (channelAvatarElement && data.channel.thumbnail)
            channelAvatarElement.src = data.channel.thumbnail;

          // Show connected section
          if (connectedSection) connectedSection.style.display = "block";
        } else {
          // Show not connected message
          statusElement.innerHTML = `
                        <div class="alert alert-warning">
                            <div class="alert-icon"><i class="fas fa-exclamation-triangle"></i></div>
                            <div class="alert-content">
                                <div class="alert-message">Not connected to YouTube. Please connect your channel.</div>
                            </div>
                        </div>
                    `;

          // Show not connected section
          if (notConnectedSection) notConnectedSection.style.display = "block";
        }
      })
      .catch((error) => {
        console.error("Error checking YouTube connection:", error);

        // Show error message
        statusElement.innerHTML = `
                    <div class="alert alert-error">
                        <div class="alert-icon"><i class="fas fa-exclamation-circle"></i></div>
                        <div class="alert-content">
                            <div class="alert-message">Error checking YouTube connection. Please try again.</div>
                        </div>
                    </div>
                `;

        // Show error section
        if (errorSection) errorSection.style.display = "block";

        // Set error message if element exists
        const errorMessageElement = document.getElementById("error-message");
        if (errorMessageElement)
          errorMessageElement.textContent =
            "Error checking YouTube connection status. Please try again.";
      });
  },

  // Connect to YouTube
  connectToYouTube: function () {
    // Show loading state
    const connectBtn = document.getElementById("connect-youtube-btn");
    if (connectBtn) {
      connectBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Connecting...`;
      connectBtn.disabled = true;
    }

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
          setTimeout(this.checkConnectionStatus.bind(this), 1000);
        } else if (data.auth_required && data.auth_url) {
          // Redirect to auth URL
          window.location.href = data.auth_url;
        } else {
          showToast(
            "error",
            "Connection Failed",
            data.message || "Failed to connect to YouTube."
          );
          if (connectBtn) {
            connectBtn.innerHTML = `<i class="fas fa-plug"></i> Connect Channel`;
            connectBtn.disabled = false;
          }
        }
      })
      .catch((error) => {
        console.error("Error connecting to YouTube:", error);
        showToast(
          "error",
          "Connection Error",
          "An error occurred while connecting to YouTube."
        );
        if (connectBtn) {
          connectBtn.innerHTML = `<i class="fas fa-plug"></i> Connect Channel`;
          connectBtn.disabled = false;
        }
      });
  },

  // Disconnect from YouTube
  disconnectFromYouTube: function () {
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
          setTimeout(this.checkConnectionStatus.bind(this), 1000);
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
  },

  // Save YouTube settings
  saveYouTubeSettings: function (e) {
    e.preventDefault();

    const form = e.target;
    const formData = new FormData(form);

    fetch("/api/youtube/settings", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showToast(
            "success",
            "Settings Saved",
            "Your YouTube settings have been saved successfully."
          );
        } else {
          showToast(
            "error",
            "Error",
            data.message || "There was an error saving your settings."
          );
        }
      })
      .catch((error) => {
        console.error("Error saving YouTube settings:", error);
        showToast(
          "error",
          "Error",
          "An error occurred while saving your settings."
        );
      });
  },

  // Format number for display (e.g. 1000 -> 1K)
  formatNumber: function (num) {
    if (!num) return "0";

    num = parseInt(num);
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + "M";
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + "K";
    } else {
      return num.toString();
    }
  },
};

// Fetch analytics data for the dashboard
function fetchAnalyticsData() {
  // Get date range if specified
  const startDate = document.getElementById("start-date")?.value;
  const endDate = document.getElementById("end-date")?.value;

  let url = "/api/analytics/mock"; // Use mock data for development

  // Add date range if provided
  if (startDate && endDate) {
    url += `?start_date=${startDate}&end_date=${endDate}`;
  }

  // Show loading state
  document.querySelectorAll(".chart-container").forEach((container) => {
    container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading data...</p>
            </div>
        `;
  });

  // Fetch data
  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Update KPI values
        updateKPIValues(data.summary);

        // Create charts
        createViewsChart(data.views_data);
        createEngagementChart(data.engagement_data);
        createDeviceChart(data.device_data);
        createDemographicsChart(data.demographics_data);
        createGeographicChart(data.geographic_data);
        createPerformanceChart(data.performance_data);

        // Update top videos
        updateTopVideos(data.top_videos);

        // Generate insights
        generateInsights(data);
      } else {
        showToast(
          "error",
          "Error",
          data.message || "Failed to load analytics data."
        );
      }
    })
    .catch((error) => {
      console.error("Error fetching analytics data:", error);
      showToast(
        "error",
        "Error",
        "An error occurred while fetching analytics data."
      );
    });
}

// Update KPI values on analytics page
function updateKPIValues(summary) {
  if (!summary) return;

  // Update values if elements exist
  if (document.getElementById("total-views"))
    document.getElementById("total-views").textContent = formatNumber(
      summary.total_views || 0
    );

  if (document.getElementById("total-likes"))
    document.getElementById("total-likes").textContent = formatNumber(
      summary.total_likes || 0
    );

  if (document.getElementById("total-comments"))
    document.getElementById("total-comments").textContent = formatNumber(
      summary.total_comments || 0
    );

  if (document.getElementById("total-shares"))
    document.getElementById("total-shares").textContent = formatNumber(
      summary.total_shares || 0
    );

  if (document.getElementById("new-subscribers"))
    document.getElementById("new-subscribers").textContent = formatNumber(
      summary.new_subscribers || 0
    );

  // Estimate watch time based on views (for demo purposes)
  if (document.getElementById("watch-time"))
    document.getElementById("watch-time").textContent = formatNumber(
      Math.round((summary.total_views || 0) * 0.02)
    );
}

// Create views chart
function createViewsChart(viewsData) {
  if (!viewsData || !viewsData.length) return;

  const container = document.getElementById("views-chart");
  if (!container) return;

  container.innerHTML = "";
  const canvas = document.createElement("canvas");
  container.appendChild(canvas);

  const ctx = canvas.getContext("2d");

  // Prepare labels and data
  const labels = viewsData.map((item) => item.date);
  const views = viewsData.map((item) => item.views);

  new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Views",
          data: views,
          borderColor: "#FF0000",
          backgroundColor: "rgba(255, 0, 0, 0.1)",
          fill: true,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          mode: "index",
          intersect: false,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function (value) {
              return formatCompactNumber(value);
            },
          },
        },
      },
    },
  });
}

// Update top videos table
function updateTopVideos(topVideos) {
  if (!topVideos || !topVideos.length) return;

  const container = document.getElementById("top-videos-body");
  if (!container) return;

  container.innerHTML = "";

  topVideos.forEach((video) => {
    const row = document.createElement("tr");

    row.innerHTML = `
            <td>
                <div class="video-title-cell">
                    <img src="${
                      video.thumbnail ||
                      "/static/images/placeholder_vertical.jpg"
                    }" 
                         alt="${video.title}" class="video-thumbnail-small"
                         onerror="this.onerror=null; this.src='/static/images/placeholder_vertical.jpg';">
                    <div class="video-title-small">${video.title}</div>
                </div>
            </td>
            <td>${video.publish_date}</td>
            <td>${formatNumber(video.views)}</td>
            <td>${formatNumber(video.likes)}</td>
            <td>${formatNumber(video.comments)}</td>
            <td>${video.ctr}</td>
        `;

    container.appendChild(row);
  });
}

// Format number helper functions
function formatNumber(num) {
  return new Intl.NumberFormat().format(num);
}

function formatCompactNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + "M";
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + "K";
  }
  return num;
}

// Initialize YouTube integration when document is ready
document.addEventListener("DOMContentLoaded", function () {
  // Initialize YouTube manager
  YouTubeManager.init();

  // Initialize analytics if on analytics page
  if (document.getElementById("views-chart")) {
    fetchAnalyticsData();

    // Add event listener for analytics update button
    const updateAnalyticsBtn = document.getElementById("update-analytics");
    if (updateAnalyticsBtn) {
      updateAnalyticsBtn.addEventListener("click", fetchAnalyticsData);
    }
  }
});
