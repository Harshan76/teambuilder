// Comparison Chart Visualization with Chart.js

document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("comparisonChart");
    if (!canvas || !window.comparisonChartData) return;

    const ctx = canvas.getContext("2d");
    const data = window.comparisonChartData;

    new Chart(ctx, {
        type: "bar",
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function (val) {
                            return val + "%";
                        }
                    },
                    title: {
                        display: true,
                        text: "Evaluation Score (%)"
                    }
                },
                x: {
                    ticks: {
                        font: {
                            weight: "600"
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    position: "top",
                    labels: {
                        font: {
                            size: 13,
                            weight: "bold"
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.dataset.label}: ${context.parsed.y}%`;
                        }
                    }
                }
            }
        }
    });
});
