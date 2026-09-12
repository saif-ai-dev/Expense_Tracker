document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.flash-msg').forEach(function (el) {
        setTimeout(function () {
            el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            el.style.opacity = '0';
            el.style.transform = 'translateY(-6px)';
            setTimeout(function () { el.remove(); }, 400);
        }, 3500);
    });

    var here = window.location.pathname;
    document.querySelectorAll('nav a, .nav-links a').forEach(function (link) {
        if (link.getAttribute('href') === here) {
            link.classList.add('active');
        }
    });

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
});