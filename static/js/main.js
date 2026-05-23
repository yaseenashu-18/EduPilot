document.addEventListener("DOMContentLoaded", () => {
    // 1. Theme Management (Persistent Dark/Light Mode)
    const themeToggleBtn = document.getElementById("theme-toggle");
    const themeIcon = document.getElementById("theme-icon");
    const currentTheme = localStorage.getItem("theme") || "dark"; // Default dark
    
    // Set initial theme
    document.documentElement.setAttribute("data-theme", currentTheme);
    updateThemeIcon(currentTheme);
    
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const theme = document.documentElement.getAttribute("data-theme");
            const newTheme = theme === "dark" ? "light" : "dark";
            
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("theme", newTheme);
            updateThemeIcon(newTheme);
        });
    }
    
    function updateThemeIcon(theme) {
        if (!themeIcon) return;
        if (theme === "dark") {
            themeIcon.className = "fas fa-sun";
            themeToggleBtn.title = "Switch to Light Mode";
        } else {
            themeIcon.className = "fas fa-moon";
            themeToggleBtn.title = "Switch to Dark Mode";
        }
    }
    
    // 2. Mobile Sidebar Toggle
    const sidebarToggleBtn = document.getElementById("sidebar-toggle");
    const sidebar = document.querySelector(".sidebar");
    
    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            sidebar.classList.toggle("show");
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener("click", (e) => {
            if (sidebar.classList.contains("show") && !sidebar.contains(e.target) && e.target !== sidebarToggleBtn) {
                sidebar.classList.remove("show");
            }
        });
    }
    
    // 3. Motivational Quotes Generator
    const quotes = [
        "\"The beautiful thing about learning is that no one can take it away from you.\" — B.B. King",
        "\"Believe you can and you're halfway there.\" — Theodore Roosevelt",
        "\"Education is the most powerful weapon which you can use to change the world.\" — Nelson Mandela",
        "\"Success is not final, failure is not fatal: it is the courage to continue that counts.\" — Winston Churchill",
        "\"The mind is not a vessel to be filled, but a fire to be kindled.\" — Plutarch",
        "\"Data is a precious thing and will last longer than the systems themselves.\" — Tim Berners-Lee",
        "\"Instruction ends in the schoolroom, but education ends only with life.\" — Frederick W. Robertson"
    ];
    
    const quoteElement = document.getElementById("motivational-quote");
    if (quoteElement && quotes.length > 0) {
        const randomIndex = Math.floor(Math.random() * quotes.length);
        quoteElement.textContent = quotes[randomIndex];
    }
    
    // 4. Loading Animations / Progress Bars
    const progressBars = document.querySelectorAll(".readiness-progress");
    progressBars.forEach(bar => {
        const value = bar.getAttribute("data-value") || "0";
        // Trigger reflow to restart transition
        bar.style.width = "0%";
        setTimeout(() => {
            bar.style.width = value + "%";
        }, 150);
    });
});

/**
 * Toggles a password input field's type between 'password' and 'text'
 * and updates the state of its FontAwesome toggle icon.
 * @param {string} fieldId - ID of the password input element
 * @param {string} iconId - ID of the FontAwesome icon element
 */
function togglePasswordVisibility(fieldId, iconId) {
    const passwordField = document.getElementById(fieldId);
    const toggleIcon = document.getElementById(iconId);
    if (!passwordField || !toggleIcon) return;
    
    if (passwordField.type === "password") {
        passwordField.type = "text";
        toggleIcon.classList.remove("fa-eye");
        toggleIcon.classList.add("fa-eye-slash");
    } else {
        passwordField.type = "password";
        toggleIcon.classList.remove("fa-eye-slash");
        toggleIcon.classList.add("fa-eye");
    }
}

