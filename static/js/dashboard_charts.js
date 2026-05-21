// EduPilot Chart.js Visualizations Setup
document.addEventListener("DOMContentLoaded", () => {
    
    // Helpers to detect theme-specific colors
    const isDark = () => document.documentElement.getAttribute("data-theme") === "dark";
    const getGridColor = () => isDark() ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.05)";
    const getTextColor = () => isDark() ? "#9ca3af" : "#475569";
    
    // 1. CGPA Progress Line Chart (Student Dashboard)
    const gpaCtx = document.getElementById("cgpaTrendChart");
    if (gpaCtx) {
        try {
            const rawData = JSON.parse(gpaCtx.getAttribute("data-chart-values") || "[]");
            const rawLabels = JSON.parse(gpaCtx.getAttribute("data-chart-labels") || "[]");
            
            const gpaGradient = gpaCtx.getContext("2d").createLinearGradient(0, 0, 0, 250);
            gpaGradient.addColorStop(0, "rgba(99, 102, 241, 0.35)");
            gpaGradient.addColorStop(1, "rgba(99, 102, 241, 0.0)");
            
            const cgpaChart = new Chart(gpaCtx, {
                type: "line",
                data: {
                    labels: rawLabels,
                    datasets: [{
                        label: "GPA per Semester",
                        data: rawData,
                        borderColor: "#6366f1",
                        borderWidth: 3,
                        backgroundColor: gpaGradient,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: "#6366f1",
                        pointHoverRadius: 7
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            min: 0,
                            max: 10,
                            grid: { color: getGridColor() },
                            ticks: { color: getTextColor() }
                        },
                        x: {
                            grid: { color: "transparent" },
                            ticks: { color: getTextColor() }
                        }
                    }
                }
            });
            
            // Watch for theme change and redraw charts if needed
            document.getElementById("theme-toggle")?.addEventListener("click", () => {
                setTimeout(() => {
                    cgpaChart.options.scales.y.grid.color = getGridColor();
                    cgpaChart.options.scales.y.ticks.color = getTextColor();
                    cgpaChart.options.scales.x.ticks.color = getTextColor();
                    cgpaChart.update();
                }, 100);
            });
        } catch (e) {
            console.error("Error creating CGPA chart:", e);
        }
    }
    
    // 2. Subject Performance Radar/Bar Chart (Student Dashboard)
    const marksCtx = document.getElementById("subjectPerformanceChart");
    if (marksCtx) {
        try {
            const rawMarks = JSON.parse(marksCtx.getAttribute("data-chart-values") || "[]");
            const rawSubjects = JSON.parse(marksCtx.getAttribute("data-chart-labels") || "[]");
            
            const radarChart = new Chart(marksCtx, {
                type: "radar",
                data: {
                    labels: rawSubjects,
                    datasets: [{
                        label: "Marks (%)",
                        data: rawMarks,
                        borderColor: "#06b6d4",
                        borderWidth: 2,
                        backgroundColor: "rgba(6, 182, 212, 0.2)",
                        pointBackgroundColor: "#06b6d4"
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        r: {
                            angleLines: { color: getGridColor() },
                            grid: { color: getGridColor() },
                            pointLabels: { color: getTextColor(), font: { size: 11, family: "Outfit" } },
                            ticks: { display: false },
                            min: 0,
                            max: 100
                        }
                    }
                }
            });
            
            document.getElementById("theme-toggle")?.addEventListener("click", () => {
                setTimeout(() => {
                    radarChart.options.scales.r.angleLines.color = getGridColor();
                    radarChart.options.scales.r.grid.color = getGridColor();
                    radarChart.options.scales.r.pointLabels.color = getTextColor();
                    radarChart.update();
                }, 100);
            });
        } catch (e) {
            console.error("Error creating marks chart:", e);
        }
    }
    
    // 3. Department Risk Distribution Doughnut (Teacher / Admin Dashboard)
    const riskCtx = document.getElementById("riskDistributionChart");
    if (riskCtx) {
        try {
            const lowRiskCount = parseInt(riskCtx.getAttribute("data-low-count") || "0");
            const medRiskCount = parseInt(riskCtx.getAttribute("data-med-count") || "0");
            const highRiskCount = parseInt(riskCtx.getAttribute("data-high-count") || "0");
            
            new Chart(riskCtx, {
                type: "doughnut",
                data: {
                    labels: ["Low Risk", "Medium Risk", "High Risk"],
                    datasets: [{
                        data: [lowRiskCount, medRiskCount, highRiskCount],
                        backgroundColor: [
                            "rgba(16, 185, 129, 0.8)", // Green
                            "rgba(245, 158, 11, 0.8)",  // Orange/Yellow
                            "rgba(239, 68, 68, 0.8)"   // Red
                        ],
                        borderColor: isDark() ? "#131b2e" : "#ffffff",
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: {
                                color: getTextColor(),
                                font: { family: "Outfit" }
                            }
                        }
                    },
                    cutout: "70%"
                }
            });
        } catch (e) {
            console.error("Error creating risk distribution chart:", e);
        }
    }
    
    // 4. Attendance Stats Chart (Analytics Page)
    const attCtx = document.getElementById("attendanceDistributionChart");
    if (attCtx) {
        try {
            const rawCategories = JSON.parse(attCtx.getAttribute("data-categories") || "[]");
            const rawCounts = JSON.parse(attCtx.getAttribute("data-counts") || "[]");
            
            new Chart(attCtx, {
                type: "bar",
                data: {
                    labels: rawCategories,
                    datasets: [{
                        label: "Students",
                        data: rawCounts,
                        backgroundColor: "rgba(99, 102, 241, 0.75)",
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            grid: { color: getGridColor() },
                            ticks: { color: getTextColor() }
                        },
                        x: {
                            grid: { color: "transparent" },
                            ticks: { color: getTextColor() }
                        }
                    }
                }
            });
        } catch (e) {
            console.error("Error creating attendance distribution chart:", e);
        }
    }
});
