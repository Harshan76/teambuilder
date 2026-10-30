// AI Group Project Team Builder - Main JavaScript

document.addEventListener("DOMContentLoaded", function () {
    // Demo login helpers
    const fillFacultyBtn = document.getElementById("fill-faculty-btn");
    const fillStudentBtn = document.getElementById("fill-student-btn");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");

    if (fillFacultyBtn && emailInput && passwordInput) {
        fillFacultyBtn.addEventListener("click", function () {
            emailInput.value = "faculty@college.edu";
            passwordInput.value = "Faculty@123";
        });
    }

    if (fillStudentBtn && emailInput && passwordInput) {
        fillStudentBtn.addEventListener("click", function () {
            emailInput.value = "alex.chen@college.edu";
            passwordInput.value = "Student@123";
        });
    }

    // Weight slider live feedback & normalization helper
    const weightSliders = document.querySelectorAll(".weight-slider");
    const totalWeightsDisplay = document.getElementById("total-weights-display");

    function updateWeightSum() {
        if (!weightSliders.length || !totalWeightsDisplay) return;
        let sum = 0;
        weightSliders.forEach(slider => {
            const val = parseFloat(slider.value) || 0;
            const targetId = slider.dataset.targetDisplay;
            if (targetId) {
                const disp = document.getElementById(targetId);
                if (disp) disp.textContent = Math.round(val * 100) + "%";
            }
            sum += val;
        });

        const roundedPct = Math.round(sum * 100);
        totalWeightsDisplay.textContent = roundedPct + "%";
        if (Math.abs(sum - 1.0) > 0.05) {
            totalWeightsDisplay.className = "badge bg-warning text-dark";
        } else {
            totalWeightsDisplay.className = "badge bg-success";
        }
    }

    weightSliders.forEach(slider => {
        slider.addEventListener("input", updateWeightSum);
    });
    updateWeightSum();
});
