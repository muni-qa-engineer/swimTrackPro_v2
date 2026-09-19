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
