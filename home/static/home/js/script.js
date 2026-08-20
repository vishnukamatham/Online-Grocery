/* ═══════════════════════════════════════════════
   GROCERY ONLINE — JavaScript
   ═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  // ─── Mobile Navigation Toggle ───────────────
  const menuBtn = document.querySelector('.menu-btn');
  const navLinks = document.querySelector('.nav-links');

  if (menuBtn && navLinks) {
    menuBtn.addEventListener('click', function () {
      navLinks.classList.toggle('open');
      const icon = menuBtn.querySelector('i');
      if (navLinks.classList.contains('open')) {
        icon.classList.replace('fa-bars', 'fa-times');
      } else {
        icon.classList.replace('fa-times', 'fa-bars');
      }
    });

    // Close nav when link clicked
    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('open');
        const icon = menuBtn.querySelector('i');
        icon.classList.replace('fa-times', 'fa-bars');
      });
    });
  }



  // ─── Auto-dismiss Flash Messages ────────────
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    // Auto close after 4 seconds
    setTimeout(function () {
      alert.style.opacity = '0';
      alert.style.transform = 'translateX(30px)';
      alert.style.transition = 'all 0.4s ease';
      setTimeout(() => alert.remove(), 400);
    }, 4000);

    // Manual close button
    const closeBtn = alert.querySelector('.close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(30px)';
        alert.style.transition = 'all 0.3s ease';
        setTimeout(() => alert.remove(), 300);
      });
    }
  });

  // ─── Wishlist Button Heart Toggle (visual) ──
  document.querySelectorAll('.btn-icon').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const icon = btn.querySelector('i');
      if (icon) {
        icon.classList.toggle('fa-regular');
        icon.classList.toggle('fa-solid');
        btn.classList.toggle('active');
      }
    });
  });

  // ─── Navbar scroll shrink ───────────────────
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 50) {
        navbar.style.padding = '0';
        navbar.style.boxShadow = '0 4px 30px rgba(0,0,0,0.1)';
      } else {
        navbar.style.boxShadow = '0 2px 20px rgba(0,0,0,0.06)';
      }
    });
  }

  // ─── Active nav link ────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-links a').forEach(function (link) {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // ─── Smooth reveal on scroll ────────────────
  const observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
        }
      });
    },
    { threshold: 0.1 }
  );

  document.querySelectorAll('.card').forEach(function (card) {
    card.style.opacity = '0';
    card.style.transform = 'translateY(24px)';
    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(card);
  });

  // ─── Password toggle (register page) ────────
  document.querySelectorAll('.toggle-password').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const input = document.querySelector('#' + btn.dataset.target);
      if (input) {
        const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
        input.setAttribute('type', type);
        btn.querySelector('i').classList.toggle('fa-eye');
        btn.querySelector('i').classList.toggle('fa-eye-slash');
      }
    });
  });

  // ─── Quantity validation on checkout ────────
  document.querySelectorAll('input[type="number"]').forEach(function (input) {
    input.addEventListener('change', function () {
      if (parseInt(input.value) < 1) input.value = 1;
    });
  });

  // ─── Cart quantity buttons ───────────────────
  // These are handled by form submission in Django.
  // No extra JS needed.

  console.log('🛒 Grocery Online JS loaded successfully!');
});
