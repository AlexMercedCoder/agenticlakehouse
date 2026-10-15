document.addEventListener('DOMContentLoaded', () => {
    // Mobile Menu Toggle
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    const siteNav = document.querySelector('.site-nav');

    const setMenuIcon = (open) => {
        if (!mobileToggle) return;
        const list = mobileToggle.querySelector('.ph-list');
        const x = mobileToggle.querySelector('.ph-x');
        // SVG elements have no .hidden property, so set the attribute.
        if (list) list.toggleAttribute('hidden', open);
        if (x) x.toggleAttribute('hidden', !open);
    };

    if (mobileToggle) {
        mobileToggle.addEventListener('click', () => {
            siteNav.classList.toggle('active');
            
            // Toggle icon (inline SVGs: list when closed, x when open)
            setMenuIcon(siteNav.classList.contains('active'));
        });
    }

    // Intersection Observer for Scroll Animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target); // Only animate once
            }
        });
    }, observerOptions);

    const fadeElements = document.querySelectorAll('.fade-in-on-scroll');
    fadeElements.forEach(el => {
        observer.observe(el);
    });

    // Smooth Scrolling for Anchors
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            // Close mobile menu if open
            if (siteNav.classList.contains('active')) {
                siteNav.classList.remove('active');
                setMenuIcon(false);
            }

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Dynamic Footer Year
    const yearEl = document.getElementById('footer-year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();
});
