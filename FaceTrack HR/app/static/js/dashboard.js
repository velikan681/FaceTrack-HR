(() => {
    const data = window.dashboardData;
    if (!data) {
        return;
    }

    const trendCanvas = document.getElementById("attendanceTrendChart");
    if (trendCanvas) {
        new Chart(trendCanvas, {
            type: "line",
            data: {
                labels: data.trendLabels,
                datasets: [
                    {
                        label: "Количество отметок",
                        data: data.trendValues,
                        fill: true,
                        borderColor: "#0d6efd",
                        backgroundColor: "rgba(13, 110, 253, 0.12)",
                        tension: 0.3,
                        pointRadius: 2
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: true } },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    }
                }
            }
        });
    }

    const departmentCanvas = document.getElementById("departmentChart");
    if (departmentCanvas) {
        new Chart(departmentCanvas, {
            type: "doughnut",
            data: {
                labels: data.departmentLabels,
                datasets: [
                    {
                        data: data.departmentValues,
                        backgroundColor: ["#0d6efd", "#198754", "#ffc107", "#dc3545", "#20c997", "#6f42c1"]
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: "bottom" } }
            }
        });
    }
})();
