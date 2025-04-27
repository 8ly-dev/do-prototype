/**
 * Mobile menu toggle functionality
 * Handles the responsive menu for screens below 720px
 * Menu slides in from the left side (standard menu pattern)
 */
document.addEventListener('DOMContentLoaded', function() {
  // Create menu toggle button for mobile view
  function createMenuToggle() {
    // Check if it already exists
    if (document.querySelector('.menu-toggle')) return;

    const menuToggle = document.createElement('button');
    menuToggle.className = 'menu-toggle';
    menuToggle.setAttribute('aria-label', 'Toggle menu');
    menuToggle.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="3" y1="12" x2="21" y2="12"></line>
        <line x1="3" y1="6" x2="21" y2="6"></line>
        <line x1="3" y1="18" x2="21" y2="18"></line>
      </svg>
    `;
    document.body.appendChild(menuToggle);

    // Add click event to toggle menu
    menuToggle.addEventListener('click', function(e) {
      e.stopPropagation();
      const rightColumn = document.querySelector('.right-column');
      if (rightColumn) {
        rightColumn.classList.toggle('show-menu');
        // Add overlay when menu is open
        toggleMenuOverlay(rightColumn.classList.contains('show-menu'));
      }
    });
  }

  // Create and toggle menu overlay
  function toggleMenuOverlay(show) {
    let overlay = document.querySelector('.menu-overlay');

    if (show) {
      if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'menu-overlay';
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100vh';
        overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        overlay.style.zIndex = '999';
        document.body.appendChild(overlay);

        // Close menu when clicking the overlay
        overlay.addEventListener('click', function() {
          const rightColumn = document.querySelector('.right-column');
          if (rightColumn) {
            rightColumn.classList.remove('show-menu');
            toggleMenuOverlay(false);
          }
        });
      }
    } else if (overlay) {
      overlay.remove();
    }
  }

  // Handle clicks outside the menu to close it
  document.addEventListener('click', function(event) {
    const rightColumn = document.querySelector('.right-column');
    const menuToggle = document.querySelector('.menu-toggle');

    if (rightColumn && rightColumn.classList.contains('show-menu') &&
        !rightColumn.contains(event.target) &&
        menuToggle && !menuToggle.contains(event.target)) {
      rightColumn.classList.remove('show-menu');
      toggleMenuOverlay(false);
    }
  });

  // Only create the menu toggle on mobile
  if (window.innerWidth <= 720) {
    createMenuToggle();
  }

  // Update on window resize
  window.addEventListener('resize', function() {
    if (window.innerWidth <= 720) {
      createMenuToggle();
    } else {
      const menuToggle = document.querySelector('.menu-toggle');
      const rightColumn = document.querySelector('.right-column');

      if (menuToggle) {
        menuToggle.remove();
      }

      if (rightColumn) {
        rightColumn.classList.remove('show-menu');
      }

      // Remove overlay if it exists
      toggleMenuOverlay(false);
    }
  });
});
