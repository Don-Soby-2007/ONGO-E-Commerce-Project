// toast.js — Auto-initializing, Django-compatible toast system
// No hover pause. Simple setTimeout-based progress bar.

(function () {
  'use strict';

  // Wait for DOM + ensure Django messages exist
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initToasts);
  } else {
    initToasts();
  }

  function initToasts() {
    const container = document.getElementById('toast-container');
    const template = document.getElementById('toast-template');

    if (!container || !template) return;

    const levelClasses = {
      debug: 'border-l-blue-500',
      info: 'border-l-blue-500',
      success: 'border-l-green-500',
      warning: 'border-l-yellow-500',
      error: 'border-l-red-500',
    };

    // Public API (optional: expose globally for manual use)
    window.showToast = function (message, level = 'info', duration = 5000) {
      const clone = template.content.cloneNode(true);
      const toastEl = clone.querySelector('div');
      
      // Set content
      clone.getElementById('toast-message').textContent = message;

      // Set color
      const borderClass = levelClasses[level] || levelClasses.info;
      toastEl.classList.remove('border-l-gray-400');
      toastEl.classList.add(borderClass, 'toast');

      container.appendChild(toastEl);

      // Progress bar
      const progressBar = toastEl.querySelector('#toast-progress');
      const totalSteps = 50;
      const stepDelay = duration / totalSteps;
      let step = totalSteps;

      const tick = () => {
        step--;
        const percent = (step / totalSteps) * 100;
        progressBar.style.width = `${percent}%`;

        if (step > 0) {
          setTimeout(tick, stepDelay);
        } else {
          // Auto-dismiss
          toastEl.style.transition = 'opacity 0.2s ease';
          toastEl.style.opacity = '0';
          setTimeout(() => {
            if (toastEl.parentNode === container) {
              container.removeChild(toastEl);
            }
          }, 200);
        }
      };

      setTimeout(tick, stepDelay);
    };

    // Auto-show Django messages
    const djangoMessages = document.querySelectorAll(
      '#django-messages > [data-message]'
    );
    djangoMessages.forEach((el) => {
      const msg = el.getAttribute('data-message');
      const level = el.getAttribute('data-level') || 'info';
      const duration = level === 'error' ? 7000 : 5000;
      if (msg) window.showToast(msg, level, duration);
    });
  }
})();