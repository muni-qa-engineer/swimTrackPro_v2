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


// --------------------------------------
// V0033.5.0 - Auto Logout After Inactivity
// --------------------------------------
// V0033.5.0 - Auto Logout After Inactivity
(function () {
  const INACTIVITY_MS = 60 * 1000; // 1 minute
  const COUNTDOWN_SEC = 20;

  const toast = document.getElementById('inactiveLogoutToast');
  const countdownElement = document.getElementById('logoutCountdown');
  const stayLoggedInBtn = document.getElementById('stayLoggedInBtn');

  if (!toast || !countdownElement || !stayLoggedInBtn) {
    return;
  }

  let countdownTimer;
  let countdown = COUNTDOWN_SEC;
  let isWarningVisible = false;

  // Initialize if not present
  if (!localStorage.getItem('lastActivityTime')) {
    localStorage.setItem('lastActivityTime', Date.now().toString());
  }

  function updateActivity() {
    localStorage.setItem('lastActivityTime', Date.now().toString());
  }

  function showLogoutWarning() {
    if (isWarningVisible) return;
    
    isWarningVisible = true;
    countdown = COUNTDOWN_SEC;
    countdownElement.textContent = countdown;
    toast.style.display = 'block';

    clearInterval(countdownTimer);

    countdownTimer = setInterval(() => {
      countdown--;
      countdownElement.textContent = countdown;

      if (countdown <= 0) {
        clearInterval(countdownTimer);
        window.location.href = '/logout';
      }
    }, 1000);
  }

  function hideLogoutWarning() {
    if (!isWarningVisible) return;
    
    isWarningVisible = false;
    toast.style.display = 'none';
    clearInterval(countdownTimer);
  }

  function stayLoggedIn() {
    updateActivity();
    hideLogoutWarning();
  }

  stayLoggedInBtn.addEventListener('click', stayLoggedIn);

  // Throttle activity updates to once per second
  let lastEventTime = 0;
  function handleUserActivity() {
    // If warning is visible, require explicit click on "Stay Logged In"
    if (isWarningVisible) return;
    
    const now = Date.now();
    if (now - lastEventTime > 1000) {
      updateActivity();
      lastEventTime = now;
    }
  }

  ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'].forEach(eventName => {
    document.addEventListener(eventName, handleUserActivity, true);
  });

  // Sync state across tabs every second
  setInterval(() => {
    const lastActivityTime = parseInt(localStorage.getItem('lastActivityTime') || '0', 10);
    const timeSinceLastActivity = Date.now() - lastActivityTime;
    
    if (timeSinceLastActivity >= INACTIVITY_MS) {
      // 1 minute has passed since ANY tab was active
      showLogoutWarning();
    } else {
      // Activity occurred recently (perhaps in another tab)
      if (isWarningVisible) {
        hideLogoutWarning();
      }
    }
  }, 1000);

})();


