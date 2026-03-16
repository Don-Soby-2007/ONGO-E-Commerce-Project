/**
 * ONGO About Page — Contact Form Logic
 * Handles: validation, file slots, fetch POST, SweetAlert UX
 */
(function () {
  'use strict';

  /* ── helpers ─────────────────────────────────────────────── */
  function getCsrfToken() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  function showFieldError(fieldId, msg) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    field.classList.add('border-red-500', 'ring-red-200');
    field.classList.remove('border-gray-300');
    let err = field.parentElement.querySelector('.field-error');
    if (!err) {
      err = document.createElement('p');
      err.className = 'field-error mt-1 text-xs text-red-500';
      field.parentElement.appendChild(err);
    }
    err.textContent = msg;
  }

  function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    field.classList.remove('border-red-500', 'ring-red-200');
    field.classList.add('border-gray-300');
    const err = field.parentElement.querySelector('.field-error');
    if (err) err.textContent = '';
  }

  function validateField(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return true;
    const value = field.value.trim();

    if (fieldId === 'contact-name') {
      if (!value) { showFieldError(fieldId, 'Name is required.'); return false; }
    }
    if (fieldId === 'contact-email') {
      if (!value) { showFieldError(fieldId, 'Email is required.'); return false; }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) { showFieldError(fieldId, 'Enter a valid email address.'); return false; }
    }
    if (fieldId === 'contact-subject') {
      if (!value) { showFieldError(fieldId, 'Please select a subject.'); return false; }
    }
    if (fieldId === 'contact-message') {
      if (!value) { showFieldError(fieldId, 'Message is required.'); return false; }
      if (value.length < 50) { showFieldError(fieldId, `Message must be at least 50 characters (${value.length}/50).`); return false; }
    }

    clearFieldError(fieldId);
    return true;
  }

  /* ── file slots ───────────────────────────────────────────── */
  const MAX_FILES = 3;
  const MAX_SIZE_MB = 5;
  const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/svg+xml'];
  let attachedFiles = [null, null, null]; // three slots

  function renderFileSlots() {
    for (let i = 0; i < MAX_FILES; i++) {
      const slot = document.getElementById(`file-slot-${i}`);
      if (!slot) continue;
      if (attachedFiles[i]) {
        slot.innerHTML = `
          <div class="flex items-center justify-between bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm">
            <span class="text-gray-700 truncate max-w-[140px]">${attachedFiles[i].name}</span>
            <button type="button" data-slot="${i}" class="remove-file ml-2 text-red-500 hover:text-red-700 flex-shrink-0">
              <i data-lucide="x" class="w-4 h-4"></i>
            </button>
          </div>`;
      } else {
        slot.innerHTML = `
          <label class="flex items-center gap-2 cursor-pointer border border-dashed border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-400 hover:border-red-400 hover:text-red-500 transition-colors">
            <i data-lucide="paperclip" class="w-4 h-4 flex-shrink-0"></i>
            <span>Attach image ${i + 1}</span>
            <input type="file" accept=".jpg,.jpeg,.png,.svg" class="hidden file-input" data-slot="${i}">
          </label>`;
      }
    }
    if (typeof lucide !== 'undefined') lucide.createIcons();
    bindSlotEvents();
  }

  function bindSlotEvents() {
    document.querySelectorAll('.file-input').forEach(input => {
      input.addEventListener('change', function () {
        const slot = parseInt(this.dataset.slot, 10);
        const file = this.files[0];
        if (!file) return;

        if (!ALLOWED_TYPES.includes(file.type)) {
          Swal.fire({ icon: 'error', title: 'Invalid file type', text: 'Only JPEG, PNG, and SVG allowed.', confirmButtonColor: '#dc2626' });
          return;
        }
        if (file.size > MAX_SIZE_MB * 1024 * 1024) {
          Swal.fire({ icon: 'error', title: 'File too large', text: `Max file size is ${MAX_SIZE_MB}MB.`, confirmButtonColor: '#dc2626' });
          return;
        }

        attachedFiles[slot] = file;
        renderFileSlots();
      });
    });

    document.querySelectorAll('.remove-file').forEach(btn => {
      btn.addEventListener('click', function () {
        const slot = parseInt(this.dataset.slot, 10);
        attachedFiles[slot] = null;
        renderFileSlots();
      });
    });
  }

  /* ── blur validation ─────────────────────────────────────── */
  ['contact-name', 'contact-email', 'contact-subject', 'contact-message'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('blur', () => validateField(id));

    // live message counter
    if (id === 'contact-message' && el) {
      el.addEventListener('input', () => {
        const counter = document.getElementById('msg-counter');
        if (counter) counter.textContent = `${el.value.length} / 50 min`;
        if (el.value.trim().length >= 50) clearFieldError(id);
      });
    }
  });

  /* ── form submit ─────────────────────────────────────────── */
  const form = document.getElementById('contact-form');
  if (!form) return;

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    // validate all
    const fields = ['contact-name', 'contact-email', 'contact-subject', 'contact-message'];
    let valid = true;
    fields.forEach(id => { if (!validateField(id)) valid = false; });

    if (!valid) {
      Swal.fire({
        icon: 'warning',
        title: 'Please fix errors',
        text: 'Check the highlighted fields before sending.',
        confirmButtonColor: '#dc2626'
      });
      return;
    }

    // loading
    Swal.fire({
      title: 'Sending message...',
      text: 'Please wait a moment.',
      allowOutsideClick: false,
      showConfirmButton: false,
      didOpen: () => Swal.showLoading()
    });

    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', getCsrfToken());
    formData.append('name', document.getElementById('contact-name').value.trim());
    formData.append('email', document.getElementById('contact-email').value.trim());
    formData.append('subject', document.getElementById('contact-subject').value.trim());
    formData.append('message', document.getElementById('contact-message').value.trim());
    const orderIdEl = document.getElementById('contact-order-id');
    if (orderIdEl && orderIdEl.value.trim()) {
      formData.append('order_id', orderIdEl.value.trim());
    }
    attachedFiles.forEach(file => {
      if (file) formData.append('attachments', file);
    });

    try {
      const response = await fetch('/contact/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': getCsrfToken() }
      });
      const data = await response.json();

      if (data.success) {
        Swal.fire({
          icon: 'success',
          title: 'Message Sent!',
          text: 'Your message has been sent successfully!',
          confirmButtonColor: '#dc2626'
        });
        form.reset();
        attachedFiles = [null, null, null];
        renderFileSlots();
        const counter = document.getElementById('msg-counter');
        if (counter) counter.textContent = '0 / 50 min';
      } else {
        Swal.fire({
          icon: 'error',
          title: 'Failed to send',
          text: data.message || 'Something went wrong. Please try again.',
          confirmButtonColor: '#dc2626'
        });
      }
    } catch (err) {
      Swal.fire({
        icon: 'error',
        title: 'Network Error',
        text: 'Could not reach the server. Please check your connection.',
        confirmButtonColor: '#dc2626'
      });
    }
  });

  /* ── init ────────────────────────────────────────────────── */
  renderFileSlots();
})();
