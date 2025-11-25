document.addEventListener('DOMContentLoaded', function () {
    const navToggle = document.querySelector('.nav-toggle');
    const navContent = document.querySelector('.nav-content');

    if (navToggle && navContent) {
        navToggle.addEventListener('click', function () {
            // Toggle active class on both button and nav content
            navToggle.classList.toggle('active');
            navContent.classList.toggle('active');

            // Update ARIA attribute for accessibility
            const isExpanded = navToggle.classList.contains('active');
            navToggle.setAttribute('aria-expanded', isExpanded);
        });

        // Close menu when clicking on a nav link (optional)
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function () {
                navToggle.classList.remove('active');
                navContent.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
            });
        });

        // Close menu when clicking outside (optional)
        document.addEventListener('click', function (event) {
            const isClickInsideNav = navToggle.contains(event.target) || navContent.contains(event.target);

            if (!isClickInsideNav && navContent.classList.contains('active')) {
                navToggle.classList.remove('active');
                navContent.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }
});
