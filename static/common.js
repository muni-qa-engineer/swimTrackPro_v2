// ================================
// SwimTrack Pro Dashboard Scripts
// Phase: V0015.10 JS Modular Split
// ================================

// ---------- DATE HELPERS ----------
function formatDate(dateObj) {
  const yyyy = dateObj.getFullYear();
  const mm = String(dateObj.getMonth() + 1).padStart(2, '0');
  const dd = String(dateObj.getDate()).padStart(2, '0');

  return `${yyyy}-${mm}-${dd}`;
}

function getTodayDate() {
  return formatDate(new Date());
}

function getWeekDays() {
  return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
}

function getSelectedMonthParts(monthValue) {
  return monthValue.split('-');
}

function getFormattedDay(day) {
  return String(day).padStart(2, '0');
}

function isPastDate(dateObj) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return dateObj < today;
}

// ---------- TOAST HELPERS ----------
function createToast(message, type = 'success', duration = 2000) {
  const toast = document.createElement('div');

  toast.innerText = message;
  toast.classList.add('toast-popup');

  if (type === 'danger') {
    toast.classList.add('toast-danger');
  } else {
    toast.classList.add('toast-success');
  }

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, duration);
}

function showConfirmToast(options, onConfirmCb, onCancelCb) {
  return new Promise((resolve) => {
    let title = 'Are you sure?';
    let message = 'Are you sure you want to proceed?';
    let confirmText = 'Yes';
    let cancelText = 'No';
    let type = 'danger';
    let onConfirm = onConfirmCb;
    let onCancel = onCancelCb;

    if (typeof options === 'string') {
      message = options;
    } else if (typeof options === 'object' && options !== null) {
      if (options.title) title = options.title;
      if (options.message) message = options.message;
      if (options.confirmText) confirmText = options.confirmText;
      if (options.cancelText) cancelText = options.cancelText;
      if (options.type) type = options.type;
      if (typeof options.onConfirm === 'function') onConfirm = options.onConfirm;
      if (typeof options.onCancel === 'function') onCancel = options.onCancel;
    }

    const existing = document.getElementById('confirmToastOverlay');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = 'confirmToastOverlay';
    overlay.className = 'confirm-toast-overlay';

    let iconClass = 'fa-solid fa-triangle-exclamation';
    let iconType = 'danger';
    if (type === 'primary') {
      iconClass = 'fa-solid fa-circle-question';
      iconType = 'primary';
    } else if (type === 'warning') {
      iconClass = 'fa-solid fa-triangle-exclamation';
      iconType = 'warning';
    }

    overlay.innerHTML = `
      <div class="confirm-toast-card" role="dialog" aria-modal="true" aria-labelledby="confirmToastTitle">
        <div class="confirm-toast-header">
          <div class="confirm-toast-icon ${iconType}">
            <i class="${iconClass}"></i>
          </div>
          <div class="confirm-toast-text">
            <div class="confirm-toast-title" id="confirmToastTitle">${title}</div>
            <div class="confirm-toast-msg">${message}</div>
          </div>
        </div>
        <div class="confirm-toast-actions">
          <button type="button" class="confirm-toast-btn-no" id="confirmToastNoBtn">${cancelText}</button>
          <button type="button" class="confirm-toast-btn-yes ${type === 'primary' ? 'primary-yes' : ''}" id="confirmToastYesBtn">${confirmText}</button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    requestAnimationFrame(() => {
      overlay.classList.add('active');
      const noBtn = overlay.querySelector('#confirmToastNoBtn');
      if (noBtn) noBtn.focus();
    });

    let isDone = false;
    function cleanup(confirmed) {
      if (isDone) return;
      isDone = true;
      overlay.classList.remove('active');
      document.removeEventListener('keydown', keyHandler);
      setTimeout(() => {
        if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
      }, 250);

      if (confirmed) {
        if (typeof onConfirm === 'function') onConfirm();
        resolve(true);
      } else {
        if (typeof onCancel === 'function') onCancel();
        resolve(false);
      }
    }

    function keyHandler(e) {
      if (e.key === 'Escape') {
        e.preventDefault();
        cleanup(false);
      }
    }
    document.addEventListener('keydown', keyHandler);

    overlay.querySelector('#confirmToastNoBtn').addEventListener('click', (e) => {
      e.stopPropagation();
      cleanup(false);
    });

    overlay.querySelector('#confirmToastYesBtn').addEventListener('click', (e) => {
      e.stopPropagation();
      const yesBtn = e.currentTarget;
      yesBtn.disabled = true;
      yesBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Processing...';
      cleanup(true);
    });

    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        cleanup(false);
      }
    });
  });
}

window.showConfirmToast = showConfirmToast;
window.confirmToast = showConfirmToast;




// ---------- SCROLL POSITION HELPERS ----------
// V0043.x Fix
// Always open pages from the top.
// Previous scroll restoration caused Dashboard,
// Booking, My Bookings and other pages to reopen
// in the middle of the page after navigation.
function saveScrollPosition() {
  // Disabled intentionally.
}

function restoreScrollPosition() {
  window.scrollTo(0, 0);
}

// ---------- UX / FORM IMPROVEMENTS ----------
// Globally prevent accidental duplicate form submissions
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            // If submission was already canceled or default prevented by confirmation, do nothing
            if (e.defaultPrevented) {
                return;
            }
            // Skip forms with custom delete or confirmation handlers
            if (this.classList.contains('delete-booking-form') || this.classList.contains('no-loading-spinner')) {
                return;
            }
            // Check if form is valid before disabling button (if HTML5 validation is used)
            if (this.checkValidity && !this.checkValidity()) {
                return;
            }
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                // If it already has loading state, don't submit again
                if (submitBtn.dataset.isSubmitting === 'true') {
                    e.preventDefault();
                    return false;
                }
                
                // Add loading state
                submitBtn.dataset.isSubmitting = 'true';
                submitBtn.dataset.originalText = submitBtn.innerHTML;
                
                // Set fixed width so button doesn't shrink when text changes to spinner
                const width = submitBtn.offsetWidth;
                if (width > 0) submitBtn.style.width = width + 'px';
                
                submitBtn.style.opacity = '0.8';
                submitBtn.style.pointerEvents = 'none';
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Loading...';
            }
        });
    });
});
