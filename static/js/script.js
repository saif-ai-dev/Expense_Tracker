// Apply saved dark-mode preference as early as possible (before DOMContentLoaded)
// to avoid a flash of the light theme on page load.
(function () {
    var saved = localStorage.getItem('theme');
    if (saved === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
})();

// Auto-dismiss flash messages after a few seconds
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.flash-msg').forEach(function (el) {
        setTimeout(function () {
            el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            el.style.opacity = '0';
            el.style.transform = 'translateY(-6px)';
            setTimeout(function () { el.remove(); }, 400);
        }, 3500);
    });

    // Mark the current page's nav link as active
    var here = window.location.pathname;
    document.querySelectorAll('nav a, .nav-links a').forEach(function (link) {
        if (link.getAttribute('href') === here) {
            link.classList.add('active');
        }
    });

    // One orchestrated count-up moment for dashboard/report figures
    document.querySelectorAll('[data-count]').forEach(function (el) {
        var target = parseFloat(el.getAttribute('data-count')) || 0;
        var duration = 650;
        var start = performance.now();
        var prefix = el.getAttribute('data-prefix') || '';

        function tick(now) {
            var progress = Math.min((now - start) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            var current = target * eased;
            el.textContent = prefix + Math.round(current).toLocaleString('en-IN');
            if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    });

    // Category / source quick-select chips (Add Income / Add Expense pages)
    document.querySelectorAll('.chip').forEach(function (chip) {
        chip.addEventListener('click', function () {
            var targetId = chip.getAttribute('data-target');
            var input = document.getElementById(targetId);
            if (!input) return;

            input.value = chip.textContent.trim();

            document.querySelectorAll('.chip[data-target="' + targetId + '"]').forEach(function (c) {
                c.classList.remove('chip-active');
            });
            chip.classList.add('chip-active');
        });
    });

    // Dark mode toggle — floating button, appended to every page
    var toggle = document.createElement('button');
    toggle.className = 'theme-toggle';
    toggle.setAttribute('aria-label', 'Toggle dark mode');
    toggle.type = 'button';

    function setIcon() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        toggle.textContent = isDark ? '☀️' : '🌙';
    }
    setIcon();

    toggle.addEventListener('click', function () {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (isDark) {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        }
        setIcon();
    });

    document.body.appendChild(toggle);
});

