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

function ensureConfirmToastStyles() {
  if (document.getElementById('confirmToastStyles')) return;
  const style = document.createElement('style');
  style.id = 'confirmToastStyles';
  style.textContent = `
    .confirm-toast-overlay {
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      right: 0 !important;
      bottom: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      background: rgba(0, 0, 0, 0.72) !important;
      backdrop-filter: blur(8px) !important;
      -webkit-backdrop-filter: blur(8px) !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      z-index: 9999999 !important;
      padding: 1.25rem !important;
      box-sizing: border-box !important;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .confirm-toast-overlay.active {
      opacity: 1 !important;
      pointer-events: auto !important;
    }
    .confirm-toast-card {
      background: #0f172a !important;
      background: rgba(15, 23, 42, 0.98) !important;
      border: 1px solid rgba(255, 255, 255, 0.18) !important;
      border-radius: 18px !important;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 35px rgba(6, 182, 212, 0.18) !important;
      width: 100% !important;
      max-width: 420px !important;
      padding: 1.75rem !important;
      margin: auto !important;
      transform: scale(0.92) translateY(12px) !important;
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
      color: #ffffff !important;
      font-family: inherit !important;
      box-sizing: border-box !important;
      text-align: left !important;
    }
    .confirm-toast-overlay.active .confirm-toast-card {
      transform: scale(1) translateY(0) !important;
    }
    .confirm-toast-header {
      display: flex !important;
      align-items: flex-start !important;
      gap: 1.15rem !important;
      margin-bottom: 1.5rem !important;
    }
    .confirm-toast-icon {
      width: 48px !important;
      height: 48px !important;
      border-radius: 14px !important;
      background: rgba(239, 68, 68, 0.15) !important;
      border: 1px solid rgba(239, 68, 68, 0.35) !important;
      color: #ef4444 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      font-size: 1.4rem !important;
      flex-shrink: 0 !important;
    }
    .confirm-toast-icon.warning {
      background: rgba(245, 158, 11, 0.15) !important;
      border-color: rgba(245, 158, 11, 0.35) !important;
      color: #f59e0b !important;
    }
    .confirm-toast-icon.primary {
      background: rgba(6, 182, 212, 0.15) !important;
      border-color: rgba(6, 182, 212, 0.35) !important;
      color: #06b6d4 !important;
    }
    .confirm-toast-title {
      font-size: 1.18rem !important;
      font-weight: 700 !important;
      color: #ffffff !important;
      margin: 0 0 0.35rem 0 !important;
      line-height: 1.3 !important;
    }
    .confirm-toast-msg {
      font-size: 0.94rem !important;
      color: #cbd5e1 !important;
      line-height: 1.48 !important;
      margin: 0 !important;
    }
    .confirm-toast-actions {
      display: flex !important;
      gap: 0.85rem !important;
      margin-top: 1.5rem !important;
    }
    .confirm-toast-btn-no,
    .confirm-toast-btn-yes {
      flex: 1 !important;
      padding: 0.75rem 1.25rem !important;
      border-radius: 10px !important;
      font-size: 0.95rem !important;
      font-weight: 600 !important;
      cursor: pointer !important;
      border: none !important;
      transition: all 0.15s ease !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      text-align: center !important;
      box-sizing: border-box !important;
    }
    .confirm-toast-btn-no {
      background: rgba(255, 255, 255, 0.08) !important;
      border: 1px solid rgba(255, 255, 255, 0.18) !important;
      color: #e2e8f0 !important;
    }
    .confirm-toast-btn-no:hover {
      background: rgba(255, 255, 255, 0.16) !important;
      color: #ffffff !important;
    }
    .confirm-toast-btn-yes {
      background: #ef4444 !important;
      color: #ffffff !important;
      border: 1px solid rgba(239, 68, 68, 0.5) !important;
      box-shadow: 0 4px 14px rgba(239, 68, 68, 0.35) !important;
      font-weight: 700 !important;
    }
    .confirm-toast-btn-yes:hover {
      background: #dc2626 !important;
      box-shadow: 0 6px 18px rgba(239, 68, 68, 0.45) !important;
    }
    .confirm-toast-btn-yes.primary-yes {
      background: #06b6d4 !important;
      border-color: rgba(6, 182, 212, 0.5) !important;
      color: #000000 !important;
      font-weight: 700 !important;
      box-shadow: 0 4px 14px rgba(6, 182, 212, 0.35) !important;
    }
    .confirm-toast-btn-yes.primary-yes:hover {
      background: #0891b2 !important;
    }
  `;
  document.head.appendChild(style);
}

function showConfirmToast(options, onConfirmCb, onCancelCb) {
  ensureConfirmToastStyles();

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
    overlay.style.cssText = 'position:fixed !important;top:0 !important;left:0 !important;right:0 !important;bottom:0 !important;width:100vw !important;height:100vh !important;background:rgba(0,0,0,0.72) !important;backdrop-filter:blur(8px) !important;-webkit-backdrop-filter:blur(8px) !important;display:flex !important;align-items:center !important;justify-content:center !important;z-index:9999999 !important;padding:1.25rem !important;margin:0 !important;box-sizing:border-box !important;opacity:0;pointer-events:none;transition:opacity 0.2s cubic-bezier(0.16,1,0.3,1);';

    let iconClass = 'fa-solid fa-triangle-exclamation';
    let iconStyle = 'background:rgba(239,68,68,0.15) !important;border:1px solid rgba(239,68,68,0.35) !important;color:#ef4444 !important;';
    if (type === 'primary') {
      iconClass = 'fa-solid fa-circle-question';
      iconStyle = 'background:rgba(6,182,212,0.15) !important;border:1px solid rgba(6,182,212,0.35) !important;color:#06b6d4 !important;';
    } else if (type === 'warning') {
      iconClass = 'fa-solid fa-triangle-exclamation';
      iconStyle = 'background:rgba(245,158,11,0.15) !important;border:1px solid rgba(245,158,11,0.35) !important;color:#f59e0b !important;';
    }

    const yesBtnStyle = (type === 'primary')
      ? 'background:#06b6d4 !important;color:#000000 !important;box-shadow:0 4px 14px rgba(6,182,212,0.35) !important;'
      : 'background:#ef4444 !important;color:#ffffff !important;box-shadow:0 4px 14px rgba(239,68,68,0.35) !important;';

    overlay.innerHTML = `
      <div class="confirm-toast-card" style="background:#0f172a !important;background:rgba(15,23,42,0.98) !important;border:1px solid rgba(255,255,255,0.18) !important;border-radius:18px !important;box-shadow:0 25px 50px -12px rgba(0,0,0,0.8),0 0 35px rgba(6,182,212,0.18) !important;width:100% !important;max-width:420px !important;padding:1.75rem !important;margin:auto !important;transform:scale(0.92) translateY(12px);transition:transform 0.25s cubic-bezier(0.16,1,0.3,1);color:#ffffff !important;font-family:Inter,system-ui,-apple-system,sans-serif !important;box-sizing:border-box !important;text-align:left !important;" role="dialog" aria-modal="true" aria-labelledby="confirmToastTitle">
        <div class="confirm-toast-header" style="display:flex !important;align-items:flex-start !important;gap:1.15rem !important;margin-bottom:1.5rem !important;">
          <div class="confirm-toast-icon" style="width:48px !important;height:48px !important;border-radius:14px !important;display:flex !important;align-items:center !important;justify-content:center !important;font-size:1.4rem !important;flex-shrink:0 !important;${iconStyle}">
            <i class="${iconClass}"></i>
          </div>
          <div class="confirm-toast-text" style="flex:1 !important;">
            <div class="confirm-toast-title" id="confirmToastTitle" style="font-size:1.18rem !important;font-weight:700 !important;color:#ffffff !important;margin:0 0 0.35rem 0 !important;line-height:1.3 !important;">${title}</div>
            <div class="confirm-toast-msg" style="font-size:0.94rem !important;color:#cbd5e1 !important;line-height:1.48 !important;margin:0 !important;">${message}</div>
          </div>
        </div>
        <div class="confirm-toast-actions" style="display:flex !important;gap:0.85rem !important;margin-top:1.5rem !important;">
          <button type="button" class="confirm-toast-btn-no" id="confirmToastNoBtn" style="flex:1 !important;padding:0.75rem 1.25rem !important;border-radius:10px !important;font-size:0.95rem !important;font-weight:600 !important;cursor:pointer !important;border:1px solid rgba(255,255,255,0.18) !important;background:rgba(255,255,255,0.08) !important;color:#e2e8f0 !important;display:inline-flex !important;align-items:center !important;justify-content:center !important;text-align:center !important;box-sizing:border-box !important;">${cancelText}</button>
          <button type="button" class="confirm-toast-btn-yes" id="confirmToastYesBtn" style="flex:1 !important;padding:0.75rem 1.25rem !important;border-radius:10px !important;font-size:0.95rem !important;font-weight:700 !important;cursor:pointer !important;border:none !important;display:inline-flex !important;align-items:center !important;justify-content:center !important;text-align:center !important;box-sizing:border-box !important;${yesBtnStyle}">${confirmText}</button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    const card = overlay.querySelector('.confirm-toast-card');

    requestAnimationFrame(() => {
      overlay.classList.add('active');
      overlay.style.opacity = '1';
      overlay.style.pointerEvents = 'auto';
      if (card) {
        card.style.transform = 'scale(1) translateY(0)';
      }
      const noBtn = overlay.querySelector('#confirmToastNoBtn');
      if (noBtn) noBtn.focus();
    });

    let isDone = false;
    function cleanup(confirmed) {
      if (isDone) return;
      isDone = true;
      overlay.classList.remove('active');
      overlay.style.opacity = '0';
      overlay.style.pointerEvents = 'none';
      if (card) {
        card.style.transform = 'scale(0.92) translateY(12px)';
      }
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
            // Skip forms with custom delete or confirmation handlers or custom AJAX pricing forms
            if (this.id === 'adminPricingForm' || this.classList.contains('delete-booking-form') || this.classList.contains('no-loading-spinner')) {
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

if (typeof window.showCenteredToast !== 'function') {
    window.showCenteredToast = function(options, optType, optTitle) {
        let message = '';
        let title = optTitle || 'Notice';
        let type = optType || 'warning';
        let duration = 4000;

        if (typeof options === 'string') {
            message = options;
        } else if (typeof options === 'object' && options !== null) {
            message = options.message || '';
            title = options.title || title;
            type = options.type || type;
            if (options.duration !== undefined) duration = options.duration;
        }

        const existing = document.getElementById('centeredToastOverlay');
        if (existing) existing.remove();

        const overlay = document.createElement('div');
        overlay.id = 'centeredToastOverlay';
        overlay.className = 'confirm-toast-overlay';
        overlay.style.cssText = 'position:fixed !important;top:0 !important;left:0 !important;right:0 !important;bottom:0 !important;width:100vw !important;height:100vh !important;background:rgba(0,0,0,0.65) !important;backdrop-filter:blur(8px) !important;-webkit-backdrop-filter:blur(8px) !important;display:flex !important;align-items:center !important;justify-content:center !important;z-index:9999999 !important;padding:1.25rem !important;margin:0 !important;box-sizing:border-box !important;opacity:0;pointer-events:none;transition:opacity 0.2s cubic-bezier(0.16,1,0.3,1);';

        let iconClass = 'fa-solid fa-triangle-exclamation';
        let iconStyle = 'background:rgba(245,158,11,0.15) !important;border:1px solid rgba(245,158,11,0.35) !important;color:#f59e0b !important;';
        let btnStyle = 'background:#f59e0b !important;color:#000000 !important;box-shadow:0 4px 14px rgba(245,158,11,0.35) !important;';

        if (type === 'danger') {
            iconClass = 'fa-solid fa-circle-xmark';
            iconStyle = 'background:rgba(239,68,68,0.15) !important;border:1px solid rgba(239,68,68,0.35) !important;color:#ef4444 !important;';
            btnStyle = 'background:#ef4444 !important;color:#ffffff !important;box-shadow:0 4px 14px rgba(239,68,68,0.35) !important;';
        } else if (type === 'info' || type === 'primary') {
            iconClass = 'fa-solid fa-circle-info';
            iconStyle = 'background:rgba(6,182,212,0.15) !important;border:1px solid rgba(6,182,212,0.35) !important;color:#06b6d4 !important;';
            btnStyle = 'background:#06b6d4 !important;color:#000000 !important;box-shadow:0 4px 14px rgba(6,182,212,0.35) !important;';
        } else if (type === 'success') {
            iconClass = 'fa-solid fa-circle-check';
            iconStyle = 'background:rgba(16,185,129,0.15) !important;border:1px solid rgba(16,185,129,0.35) !important;color:#10b981 !important;';
            btnStyle = 'background:#10b981 !important;color:#ffffff !important;box-shadow:0 4px 14px rgba(16,185,129,0.35) !important;';
        }

        overlay.innerHTML = `
            <div class="confirm-toast-card" style="background:#0f172a !important;background:rgba(15,23,42,0.98) !important;border:1px solid rgba(255,255,255,0.18) !important;border-radius:18px !important;box-shadow:0 25px 50px -12px rgba(0,0,0,0.8),0 0 35px rgba(245,158,11,0.18) !important;width:100% !important;max-width:400px !important;padding:1.75rem !important;margin:auto !important;transform:scale(0.92) translateY(12px);transition:transform 0.25s cubic-bezier(0.16,1,0.3,1);color:#ffffff !important;font-family:Inter,system-ui,-apple-system,sans-serif !important;box-sizing:border-box !important;text-align:left !important;" role="dialog">
                <div class="confirm-toast-header" style="display:flex !important;align-items:center !important;gap:1.15rem !important;margin-bottom:1.25rem !important;">
                    <div class="confirm-toast-icon" style="width:48px !important;height:48px !important;border-radius:14px !important;display:flex !important;align-items:center !important;justify-content:center !important;font-size:1.4rem !important;flex-shrink:0 !important;${iconStyle}">
                        <i class="${iconClass}"></i>
                    </div>
                    <div class="confirm-toast-text" style="flex:1 !important;">
                        <div class="confirm-toast-title" style="font-size:1.15rem !important;font-weight:700 !important;color:#ffffff !important;margin:0 0 0.25rem 0 !important;line-height:1.3 !important;">${title}</div>
                        <div class="confirm-toast-msg" style="font-size:0.95rem !important;color:#cbd5e1 !important;line-height:1.4 !important;margin:0 !important;">${message}</div>
                    </div>
                </div>
                <div class="confirm-toast-actions" style="display:flex !important;justify-content:flex-end !important;margin-top:1.25rem !important;">
                    <button type="button" class="confirm-toast-btn-yes" id="centeredToastOkBtn" style="padding:0.6rem 1.5rem !important;border-radius:10px !important;font-size:0.95rem !important;font-weight:700 !important;cursor:pointer !important;border:none !important;display:inline-flex !important;align-items:center !important;justify-content:center !important;text-align:center !important;box-sizing:border-box !important;${btnStyle}">OK</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);
        const card = overlay.querySelector('.confirm-toast-card');

        requestAnimationFrame(() => {
            overlay.classList.add('active');
            overlay.style.opacity = '1';
            overlay.style.pointerEvents = 'auto';
            if (card) card.style.transform = 'scale(1) translateY(0)';
            const okBtn = overlay.querySelector('#centeredToastOkBtn');
            if (okBtn) okBtn.focus();
        });

        let dismissed = false;
        function dismissToast() {
            if (dismissed) return;
            dismissed = true;
            overlay.classList.remove('active');
            overlay.style.opacity = '0';
            overlay.style.pointerEvents = 'none';
            if (card) card.style.transform = 'scale(0.92) translateY(12px)';
            setTimeout(() => { if (overlay.parentNode) overlay.parentNode.removeChild(overlay); }, 250);
        }

        overlay.querySelector('#centeredToastOkBtn').addEventListener('click', dismissToast);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) dismissToast(); });

        if (duration > 0) {
            setTimeout(dismissToast, duration);
        }
    };
    window.showToastMessage = window.showCenteredToast;
}

// Global alert auto-dismiss within 5 seconds
(function() {
    function autoDismissAlerts() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alertElem) {
            if (alertElem.closest('.modal') || alertElem.id === 'bookingClientAlert') return;
            if (alertElem.dataset.autoDismissInitialized) return;
            alertElem.dataset.autoDismissInitialized = 'true';

            setTimeout(function() {
                alertElem.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                alertElem.style.opacity = '0';
                alertElem.style.transform = 'translateY(-10px)';
                setTimeout(function() {
                    if (alertElem.parentNode) {
                        try {
                            if (window.bootstrap && bootstrap.Alert) {
                                const bsAlert = bootstrap.Alert.getInstance(alertElem) || new bootstrap.Alert(alertElem);
                                bsAlert.close();
                            } else {
                                alertElem.remove();
                            }
                        } catch (e) {
                            alertElem.remove();
                        }
                    }
                }, 600);
            }, 5000); // 5 seconds
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoDismissAlerts);
    } else {
        autoDismissAlerts();
    }
    window.autoDismissAlerts = autoDismissAlerts;
})();

