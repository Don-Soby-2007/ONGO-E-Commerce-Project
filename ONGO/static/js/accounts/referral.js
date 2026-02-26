/* referral.js — Referral page interactions */

(function () {
    'use strict';

    /* ── Toast helper ────────────────────────────── */
    function showToast(message) {
        const toast = document.getElementById('referral-toast');
        if (!toast) return;

        const toastMsg = document.getElementById('referral-toast-msg');
        if (toastMsg) toastMsg.textContent = message;

        toast.classList.remove('toast-hidden');
        toast.classList.add('toast-visible');

        clearTimeout(toast._hideTimer);
        toast._hideTimer = setTimeout(() => {
            toast.classList.remove('toast-visible');
            toast.classList.add('toast-hidden');
        }, 2200);
    }

    /* ── Copy helper ─────────────────────────────── */
    function copyText(text, btn, originalLabel) {
        if (!text) return;

        navigator.clipboard.writeText(text).then(() => {
            btn.textContent = 'Copied!';
            btn.classList.add('bg-green-500', 'text-white', 'border-green-500');
            btn.classList.remove('bg-white', 'text-gray-700', 'border-gray-300',
                'hover:bg-gray-50');

            showToast('Copied to clipboard!');

            clearTimeout(btn._resetTimer);
            btn._resetTimer = setTimeout(() => {
                btn.textContent = originalLabel;
                btn.classList.remove('bg-green-500', 'text-white', 'border-green-500');
                btn.classList.add('bg-white', 'text-gray-700', 'border-gray-300',
                    'hover:bg-gray-50');
            }, 2000);
        }).catch(() => {
            /* Fallback for non-secure contexts */
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.cssText = 'position:fixed;opacity:0';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            showToast('Copied to clipboard!');
        });
    }

    /* ── Init ────────────────────────────────────── */
    document.addEventListener('DOMContentLoaded', () => {

        /* Copy referral CODE */
        const copyCodeBtn = document.getElementById('copy-code-btn');
        const referralCodeEl = document.getElementById('referral-code-value');

        if (copyCodeBtn && referralCodeEl) {
            copyCodeBtn.addEventListener('click', () => {
                copyText(referralCodeEl.dataset.code, copyCodeBtn, 'Copy Code');
            });
        }

        /* Copy referral LINK */
        const copyLinkBtn = document.getElementById('copy-link-btn');
        const referralLinkInput = document.getElementById('referral-link-input');

        if (copyLinkBtn && referralLinkInput) {
            copyLinkBtn.addEventListener('click', () => {
                copyText(referralLinkInput.value, copyLinkBtn, 'Copy Link');
            });
        }

        /* Copy link from summary card (optional second button) */
        const copyLinkCardBtn = document.getElementById('copy-link-card-btn');
        if (copyLinkCardBtn && referralLinkInput) {
            copyLinkCardBtn.addEventListener('click', () => {
                copyText(referralLinkInput.value, copyLinkCardBtn, 'Copy Link');
            });
        }

        /* Animate cards on load */
        document.querySelectorAll('.referral-card-animate').forEach((card, i) => {
            card.style.animationDelay = `${0.05 + i * 0.07}s`;
        });
    });
})();
