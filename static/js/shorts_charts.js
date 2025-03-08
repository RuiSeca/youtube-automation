/**
 * Add this JavaScript code to a new file called shorts_charts.js
 * Include it in your templates after the main.js file
 */

// Initialize charts for the analytics page
function initializeAnalyticsCharts() {
  // Only initialize if we're on the analytics page
  if (!document.getElementById("views-chart")) {
    return;
  }

  // Load the selected date range
  const startDate = document.getElementById("start-date").value;
  const endDate = document.getElementById("end-date").value;

  // Fetch analytics data from the API
  fetch(`/api/analytics?start_date=${startDate}&end_date=${endDate}`)
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Update summary stats
        updateAnalyticsSummary(data.summary);

        // Create charts
        createViewsChart(data.views_data);
        createEngagementChart(data.engagement_data);
        createSourcesChart(data.device_data);
        createDemographicsChart(data.demographics_data);
        createGeographicChart(data.geographic_data);
        createPerformanceChart(data.performance_data);

        // Create top videos table
        createTopVideosTable(data.top_videos);

        // Generate insights
        generateInsights(data);
      } else {
        showToast("error", "Error", "Failed to load analytics data.");
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

// Update summary statistics
function updateAnalyticsSummary(summary) {
  // Update KPI values
  document.getElementById("total-views").textContent = formatNumber(
    summary.total_views
  );
  document.getElementById("total-likes").textContent = formatNumber(
    summary.total_likes
  );
  document.getElementById("total-comments").textContent = formatNumber(
    summary.total_comments
  );
  document.getElementById("total-shares").textContent = formatNumber(
    summary.total_shares
  );
  document.getElementById("new-subscribers").textContent = formatNumber(
    summary.total_likes * 0.05
  ); // Estimate for demo
  document.getElementById("watch-time").textContent = formatNumber(
    summary.total_views * 0.02
  ); // Estimate for demo
}

// Create views over time chart
function createViewsChart(viewsData) {
  const ctx = document.createElement("canvas");
  document.getElementById("views-chart").innerHTML = "";
  document.getElementById("views-chart").appendChild(ctx);

  // Prepare data for the chart
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

// Create engagement chart
function createEngagementChart(engagementData) {
  const ctx = document.createElement("canvas");
  document.getElementById("engagement-chart").innerHTML = "";
  document.getElementById("engagement-chart").appendChild(ctx);

  // Prepare data for the chart
  const labels = Object.keys(engagementData);
  const data = Object.values(engagementData);

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels.map(
        (label) => label.charAt(0).toUpperCase() + label.slice(1)
      ), // Capitalize
      datasets: [
        {
          label: "Count",
          data: data,
          backgroundColor: [
            "rgba(54, 162, 235, 0.7)",
            "rgba(255, 99, 132, 0.7)",
            "rgba(75, 192, 192, 0.7)",
            "rgba(255, 206, 86, 0.7)",
            "rgba(153, 102, 255, 0.7)",
          ],
          borderColor: [
            "rgba(54, 162, 235, 1)",
            "rgba(255, 99, 132, 1)",
            "rgba(75, 192, 192, 1)",
            "rgba(255, 206, 86, 1)",
            "rgba(153, 102, 255, 1)",
          ],
          borderWidth: 1,
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
      },
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });
}

// Create sources chart
function createSourcesChart(deviceData) {
  const ctx = document.createElement("canvas");
  document.getElementById("sources-chart").innerHTML = "";
  document.getElementById("sources-chart").appendChild(ctx);

  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: deviceData.devices,
      datasets: [
        {
          data: deviceData.percentages,
          backgroundColor: [
            "rgba(255, 99, 132, 0.7)",
            "rgba(54, 162, 235, 0.7)",
            "rgba(255, 206, 86, 0.7)",
            "rgba(75, 192, 192, 0.7)",
            "rgba(153, 102, 255, 0.7)",
          ],
          borderColor: [
            "rgba(255, 99, 132, 1)",
            "rgba(54, 162, 235, 1)",
            "rgba(255, 206, 86, 1)",
            "rgba(75, 192, 192, 1)",
            "rgba(153, 102, 255, 1)",
          ],
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
        },
      },
    },
  });
}

// Create demographics chart
function createDemographicsChart(demographicsData) {
  const ctx = document.createElement("canvas");
  document.getElementById("demographics-chart").innerHTML = "";
  document.getElementById("demographics-chart").appendChild(ctx);

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: demographicsData.age_groups,
      datasets: [
        {
          label: "Male",
          data: demographicsData.male,
          backgroundColor: "rgba(54, 162, 235, 0.7)",
          borderColor: "rgba(54, 162, 235, 1)",
          borderWidth: 1,
        },
        {
          label: "Female",
          data: demographicsData.female,
          backgroundColor: "rgba(255, 99, 132, 0.7)",
          borderColor: "rgba(255, 99, 132, 1)",
          borderWidth: 1,
        },
        {
          label: "Other",
          data: demographicsData.other,
          backgroundColor: "rgba(75, 192, 192, 0.7)",
          borderColor: "rgba(75, 192, 192, 1)",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
        },
      },
      scales: {
        x: {
          stacked: true,
        },
        y: {
          stacked: true,
          beginAtZero: true,
          ticks: {
            callback: function (value) {
              return value + "%";
            },
          },
        },
      },
    },
  });
}

// Create geographic chart
function createGeographicChart(geographicData) {
  const ctx = document.createElement("canvas");
  document.getElementById("geography-chart").innerHTML = "";
  document.getElementById("geography-chart").appendChild(ctx);

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: geographicData.countries,
      datasets: [
        {
          label: "Views Percentage",
          data: geographicData.percentages,
          backgroundColor: "rgba(54, 162, 235, 0.7)",
          borderColor: "rgba(54, 162, 235, 1)",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: "y",
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        x: {
          beginAtZero: true,
          ticks: {
            callback: function (value) {
              return value + "%";
            },
          },
        },
      },
    },
  });
}

// Create performance chart
function createPerformanceChart(performanceData) {
  const ctx = document.createElement("canvas");
  document.getElementById("performance-chart").innerHTML = "";
  document.getElementById("performance-chart").appendChild(ctx);

  new Chart(ctx, {
    type: "line",
    data: {
      labels: performanceData.videos,
      datasets: [
        {
          label: "Views",
          data: performanceData.views,
          borderColor: "#FF0000",
          backgroundColor: "rgba(255, 0, 0, 0.1)",
          fill: false,
          tension: 0.1,
          yAxisID: "y",
        },
        {
          label: "Engagement Rate",
          data: performanceData.engagement_rates,
          borderColor: "#4CAF50",
          backgroundColor: "rgba(76, 175, 80, 0.1)",
          fill: false,
          tension: 0.1,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          position: "top",
        },
      },
      scales: {
        y: {
          type: "linear",
          display: true,
          position: "left",
          title: {
            display: true,
            text: "Views",
          },
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          title: {
            display: true,
            text: "Engagement Rate (%)",
          },
          grid: {
            drawOnChartArea: false,
          },
          ticks: {
            callback: function (value) {
              return value + "%";
            },
          },
        },
      },
    },
  });
}

// Create top videos table
function createTopVideosTable(topVideos) {
  const tableBody = document.getElementById("top-videos-body");
  if (!tableBody) return;

  tableBody.innerHTML = "";

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

    tableBody.appendChild(row);
  });
}

// Generate insights based on analytics data
function generateInsights(data) {
  const insightsContainer = document.getElementById("insights-container");
  if (!insightsContainer) return;

  // Sample insights for demo purposes
  const insights = [
    {
      icon: "chart-line",
      title: "Strong Growth Trend",
      description:
        "Your channel is experiencing consistent growth with a 27% increase in views over the selected period. Continue creating content around your top-performing topics to maintain this momentum.",
    },
    {
      icon: "lightbulb",
      title: "Content Opportunity",
      description:
        "Your finance-related shorts are generating 35% higher engagement than other topics. Consider creating more content in this category to capitalize on audience interest.",
    },
    {
      icon: "clock",
      title: "Optimal Posting Times",
      description:
        "Shorts posted on weekends between 6-9 PM are performing 42% better than other times. Adjust your publishing schedule to maximize reach and engagement.",
    },
    {
      icon: "users",
      title: "Audience Insight",
      description:
        "Your content is resonating strongly with the 25-34 age group. Consider tailoring future content to address the specific interests and needs of this demographic.",
    },
  ];

  // Build the insights HTML
  let insightsHTML = "";

  insights.forEach((insight) => {
    insightsHTML += `
            <div class="insight-card">
                <div class="insight-icon"><i class="fas fa-${insight.icon}"></i></div>
                <div class="insight-content">
                    <div class="insight-title">${insight.title}</div>
                    <div class="insight-description">${insight.description}</div>
                </div>
            </div>
        `;
  });

  insightsContainer.innerHTML = insightsHTML;
}

// Helper functions for formatting numbers
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

// Initialize when document is loaded
document.addEventListener("DOMContentLoaded", function () {
  // Initialize analytics charts if we're on the analytics page
  initializeAnalyticsCharts();

  // Add event listeners for analytics page
  if (document.getElementById("update-analytics")) {
    document
      .getElementById("update-analytics")
      .addEventListener("click", function () {
        initializeAnalyticsCharts();
      });
  }

  // Add event listeners for tab navigation
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", function () {
      // If switching to the analytics tab, refresh charts
      if (
        this.getAttribute("data-tab") === "overview" &&
        this.parentElement.parentElement.id === "analytics-tab"
      ) {
        setTimeout(initializeAnalyticsCharts, 100);
      }
    });
  });

  // Add event listeners for date range presets
  document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      // The date range has changed, so refresh charts
      if (document.getElementById("views-chart")) {
        setTimeout(initializeAnalyticsCharts, 100);
      }
    });
  });
});
