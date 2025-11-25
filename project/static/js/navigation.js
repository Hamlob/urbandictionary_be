document.addEventListener('DOMContentLoaded', function () {
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function () {
            // Toggle active class on both button and nav content
            navToggle.classList.toggle('active');
            navLinks.classList.toggle('active');

            // Update ARIA attribute for accessibility
            const isExpanded = navToggle.classList.contains('active');
            navToggle.setAttribute('aria-expanded', isExpanded);
        });

        // Close menu when clicking on a nav link (optional)
        const navLinkItems = document.querySelectorAll('.nav-link');
        navLinkItems.forEach(link => {
            link.addEventListener('click', function () {
                navToggle.classList.remove('active');
                navLinks.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
            });
        });

        // Close menu when clicking outside (optional)
        document.addEventListener('click', function (event) {
            const isClickInsideNav = navToggle.contains(event.target) || navLinks.contains(event.target);

            if (!isClickInsideNav && navLinks.classList.contains('active')) {
                navToggle.classList.remove('active');
                navLinks.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }
});
