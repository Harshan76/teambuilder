// Interactive Team Review & Editing Script

document.addEventListener("DOMContentLoaded", function () {
    // 1. Role Override Handler
    const roleSelects = document.querySelectorAll(".role-override-select");
    roleSelects.forEach(select => {
        select.addEventListener("change", function () {
            const memberId = this.dataset.memberId;
            const roleId = this.value;

            if (!memberId || !roleId) return;

            fetch("/api/team/override-role", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    member_id: parseInt(memberId),
                    role_id: parseInt(roleId)
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, "success");
                    // Update badge text if present
                    const badge = document.getElementById(`role-badge-${memberId}`);
                    if (badge) {
                        badge.textContent = select.options[select.selectedIndex].text;
                    }
                } else {
                    showToast(data.error || "Failed to override role", "danger");
                }
            })
            .catch(err => {
                showToast("Network error: " + err, "danger");
            });
        });
    });

    // 2. Member Team Reassignment Handler
    const teamSelects = document.querySelectorAll(".team-reassign-select");
    teamSelects.forEach(select => {
        select.addEventListener("change", function () {
            const memberId = this.dataset.memberId;
            const targetTeamId = this.value;

            if (!memberId || !targetTeamId) return;

            if (!confirm(`Reassign this student to ${this.options[this.selectedIndex].text}?`)) {
                return;
            }

            fetch("/api/team/reassign", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    member_id: parseInt(memberId),
                    target_team_id: parseInt(targetTeamId)
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, "success");
                    setTimeout(() => {
                        window.location.reload();
                    }, 600);
                } else {
                    showToast(data.error || "Failed to reassign student", "danger");
                }
            })
            .catch(err => {
                showToast("Network error: " + err, "danger");
            });
        });
    });

    // Lightweight Toast Helper
    function showToast(msg, type = "info") {
        let container = document.getElementById("toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "toast-container";
            container.style.position = "fixed";
            container.style.bottom = "20px";
            container.style.right = "20px";
            container.style.zIndex = "9999";
            document.body.appendChild(container);
        }

        const toast = document.createElement("div");
        toast.className = `alert alert-${type} shadow-sm`;
        toast.style.minWidth = "250px";
        toast.style.marginBottom = "10px";
        toast.textContent = msg;

        container.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 3500);
    }
});
