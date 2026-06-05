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

function formatDate(dateObj) {
  const yyyy = dateObj.getFullYear();
  const mm = String(dateObj.getMonth() + 1).padStart(2, '0');
  const dd = String(dateObj.getDate()).padStart(2, '0');

  return `${yyyy}-${mm}-${dd}`;
}

function getTodayDate() {
  return formatDate(new Date());
}

// --- Calendar/Date Helper Utility Functions V0015.8 ---
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

(function(){
  const today = getTodayDate();

    const el = document.querySelector('input[name="date"]');

    if (el) {
        el.min = today;

        if (!el.value) {
            el.value = today;
        }
    }
  })();
  const pkg = document.getElementById('packageSelect');
  const endDateDiv = document.getElementById('endDateContainer');

  // CENTRALIZED CONFIG
  const PRICING = {
    DEMO_DAY: 500,
    SINGLE_DAY: 750,
    MONTHLY_PACKAGE: 9000,
    CUSTOM_PACKAGE_BASE: 9000
  };

  const GROUP_DISCOUNTS = {
    1: 0,
    2: 6,
    3: 11,
    4: 16,
    5: 21
};

  // Smart weekday validation based on selected Start Date
  const dayCheckboxes = document.querySelectorAll('.class-day');
  const selectedDaysPreview = document.getElementById('selectedDaysPreview');
  const selectedDaysInput = document.getElementById('selectedDaysInput');
  const feeInput = document.getElementById('feeInput');

  function updateAllowedDays() {
    const startDateInput = document.querySelector('input[name="date"]');
    const endDateInput = document.querySelector('input[name="end_date"]');

    if (!startDateInput || !startDateInput.value) return;

    const selectedDate = new Date(startDateInput.value);

    const days = [
      'Sunday',
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
      'Saturday'
    ];

    const allowedDay = days[selectedDate.getDay()];

    if (pkg.value === 'Single' || pkg.value === 'Demo') {
      dayCheckboxes.forEach(cb => {
        cb.checked = false;

        if (cb.value === allowedDay) {
          cb.disabled = false;
          cb.checked = true;
          selectedDaysInput.value = allowedDay;
        } else {
          cb.disabled = true;
        }
      });

      endDateDiv.style.display = 'none';
    }
    else {
      dayCheckboxes.forEach(cb => {
        cb.disabled = false;
      });

      endDateDiv.style.display = 'block';

      if (pkg.value === 'Monthly') {
        const autoEndDate = new Date(selectedDate);
        autoEndDate.setMonth(autoEndDate.getMonth() + 1);
        autoEndDate.setDate(autoEndDate.getDate() - 1);

        endDateInput.value = formatDate(autoEndDate);
      }
      else if (pkg.value === 'Custom') {
        endDateInput.value = startDateInput.value;
      }
    }

    updateSelectedDays();
  }

  function updateSelectedDays() {
    const selected = [];
    const personsInput = document.getElementById('personsInput');
    const persons = Number(personsInput?.value || 1);

    dayCheckboxes.forEach(cb => {
      if (cb.checked) {
        selected.push(cb.value);
      }
    });

    if (pkg.value === 'Monthly' && selected.length > 3) {
      alert('Monthly package allows maximum 3 class days');

      const lastChecked = selected[selected.length - 1];

      dayCheckboxes.forEach(cb => {
        if (cb.value === lastChecked) {
          cb.checked = false;
        }
      });

      return updateSelectedDays();
    }

    // Insert: Monthly package must have 2 or 3 days
    if (pkg.value === 'Monthly' && selected.length === 1) {
      feeInput.value = '';
      feeInput.placeholder = 'Select 2 or 3 class days';
      return;
    }

    if (pkg.value === 'Custom' && selected.length > 7) {
      alert('Custom package allows maximum 7 class days');

      const lastChecked = selected[selected.length - 1];

      dayCheckboxes.forEach(cb => {
        if (cb.value === lastChecked) {
          cb.checked = false;
        }
      });

      return updateSelectedDays();
    }

    selectedDaysInput.value = selected.join(', ');

    selectedDaysPreview.innerText = selected.length
      ? selected.join(', ')
      : 'No days selected';

    // Maximum 5 persons allowed.
    if (persons > 5) {
      feeInput.value = '';
      feeInput.placeholder = 'Discuss with your trainer';
      return;
    }

    const discountMap = {
        1: 0,
        2: 6,
        3: 11,
        4: 16,
        5: 21
    };

    const discountPercent = discountMap[persons] || 0;
    let actualAmount = 0;

    if (pkg.value === 'Demo') {
      actualAmount = 500 * persons;
    }
    else if (pkg.value === 'Single') {
      actualAmount = 750 * persons;
    }
    else if (pkg.value === 'Monthly') {
      if (selected.length < 2 || selected.length > 3) {
        feeInput.value = '';
        feeInput.placeholder = 'Select 2 or 3 class days';
        return;
      }

      if (selected.length === 2) {
        actualAmount = 6000 * persons;
      }
      else {
        actualAmount = 9000 * persons;
      }
    }
    else if (pkg.value === 'Custom') {
      const startDateInput = document.querySelector('input[name="date"]');
      const endDateInput = document.querySelector('input[name="end_date"]');

      if (!startDateInput.value || !endDateInput.value || selected.length === 0) {
        feeInput.value = 0;
        feeInput.placeholder = '';
        return;
      }

      const start = new Date(startDateInput.value + 'T00:00:00');
      const end = new Date(endDateInput.value + 'T00:00:00');

      const dayMap = {
        'Sunday': 0,
        'Monday': 1,
        'Tuesday': 2,
        'Wednesday': 3,
        'Thursday': 4,
        'Friday': 5,
        'Saturday': 6
      };

      const selectedDayIndexes = selected.map(day => dayMap[day]);

      let totalClasses = 0;
      const current = new Date(start);

      while (current <= end) {
        if (selectedDayIndexes.includes(current.getDay())) {
          totalClasses++;
        }
        current.setDate(current.getDate() + 1);
      }

      // More than 14 sessions requires trainer discussion.
      if (totalClasses > 14) {
        feeInput.value = '';
        feeInput.placeholder = 'Discuss with your trainer';
        return;
      }

      // 12 to 14 sessions are capped at monthly equivalent.
      if (totalClasses >= 12) {
        actualAmount = 9000 * persons;
      } else {
        actualAmount = totalClasses * 750 * persons;
      }
    }

    const finalFee = Math.round(
      actualAmount * (100 - discountPercent) / 100
    );

    feeInput.placeholder = '';
    feeInput.value = finalFee;
  }

function handlePackageChange() {
  dayCheckboxes.forEach(cb => {
    cb.checked = false;
  });

  updateAllowedDays();
}

const startDateInput = document.querySelector('input[name="date"]');

const timeSelect = document.getElementById('timeSelect');

function generateTimeSlots() {
  if (!timeSelect) return;

  timeSelect.innerHTML = '';

  const startHour = 6;
  const endHour = 21;

  const selectedDateInput = document.querySelector('input[name="date"]');
  const selectedDate = selectedDateInput ? selectedDateInput.value : '';

  const now = new Date();

  for (let hour = startHour; hour <= endHour; hour++) {
    for (let min of [0, 30]) {

      if (hour === endHour && min > 0) {
        continue;
      }

      const slotDate = new Date();

      if (selectedDate) {
        slotDate.setFullYear(
          Number(selectedDate.split('-')[0]),
          Number(selectedDate.split('-')[1]) - 1,
          Number(selectedDate.split('-')[2])
        );
      }

      slotDate.setHours(hour, min, 0, 0);

      const option = document.createElement('option');

      const displayHour = hour % 12 || 12;
      const displayMin = String(min).padStart(2, '0');
      const ampm = hour >= 12 ? 'PM' : 'AM';

      const label = `${String(displayHour).padStart(2, '0')}:${displayMin} ${ampm}`;

      option.value = label;
      option.textContent = label;

      const isToday = selectedDate === getTodayDate();

      if (isToday && slotDate <= now) {
        option.disabled = true;
      }

      timeSelect.appendChild(option);
    }
  }

  const enabledOption = [...timeSelect.options].find(opt => !opt.disabled);

  if (enabledOption) {
    enabledOption.selected = true;
  }
}

function handleStartDateChange() {
  updateAllowedDays();
  generateTimeSlots();
  checkLocationConflict();
}

const endDateInput = document.querySelector('input[name="end_date"]');
const personsInput = document.getElementById('personsInput');

function initializeBookingEventListeners() {

  if (pkg) {
    pkg.addEventListener('change', handlePackageChange);
  }

  if (startDateInput) {
    startDateInput.addEventListener('change', handleStartDateChange);
  }

  if (endDateInput) {
    endDateInput.addEventListener('change', updateSelectedDays);
  }

  if (personsInput) {
    personsInput.addEventListener('input', updateSelectedDays);
  }

  if (dayCheckboxes.length > 0) {
    dayCheckboxes.forEach(cb => {
      cb.addEventListener('change', updateSelectedDays);
    });
  }

    const locationInput = document.querySelector('input[name="location"]');

  if (timeSelect) {
    timeSelect.addEventListener('change', checkLocationConflict);
  }

  if (startDateInput) {
    startDateInput.addEventListener('change', checkLocationConflict);
  }

  if (locationInput) {
    locationInput.addEventListener('input', checkLocationConflict);
    locationInput.addEventListener('change', checkLocationConflict);
  }
}

initializeBookingEventListeners();
updateAllowedDays();
generateTimeSlots();
const tabBookings = document.getElementById('tabBookings');
const tabBook = document.getElementById('tabBook');
const tabCalendar = document.getElementById('tabCalendar');
const tabPayments = document.getElementById('tabPayments');

const bookingsSection = document.getElementById('bookingsSection');
const bookSlotSection = document.getElementById('bookSlotSection');
const calendarSection = document.getElementById('calendarSection');
const paymentsSection = document.getElementById('paymentsSection');

const calendarMonthInput = document.getElementById('calendarMonthInput');
const calendarGrid = document.getElementById('calendarGrid');
const swimmerRows = document.querySelectorAll('.swimmer-row');
const studentSelect = document.getElementById('studentSelect');

function showBookings() {
  bookingsSection.style.display = 'block';
  if (bookSlotSection) {
    bookSlotSection.style.display = 'none';
  }
  calendarSection.style.display = 'none';
  if (paymentsSection) {
    paymentsSection.style.display = 'none';
  }

  tabBookings.classList.add('active');
  if (tabBook) {
    tabBook.classList.remove('active');
  }
  tabCalendar.classList.remove('active');
  if (tabPayments) {
    tabPayments.classList.remove('active');
  }

  localStorage.setItem('activeTab', 'bookings');
}

function showBookSlot() {
  bookingsSection.style.display = 'none';
  if (bookSlotSection) {
    bookSlotSection.style.display = 'flex';
  }
  calendarSection.style.display = 'none';
  if (paymentsSection) {
    paymentsSection.style.display = 'none';
  }

  if (tabBook) {
    tabBook.classList.add('active');
  }
  tabBookings.classList.remove('active');
  tabCalendar.classList.remove('active');
  if (tabPayments) {
    tabPayments.classList.remove('active');
  }

  localStorage.setItem('activeTab', 'book_slot');
}

function showCalendar() {
  bookingsSection.style.display = 'none';
  if (bookSlotSection) {
    bookSlotSection.style.display = 'none';
  }
  calendarSection.style.display = 'block';
  if (paymentsSection) {
    paymentsSection.style.display = 'none';
  }

  tabCalendar.classList.add('active');
  tabBookings.classList.remove('active');
  if (tabBook) {
    tabBook.classList.remove('active');
  }
  if (tabPayments) {
    tabPayments.classList.remove('active');
  }

  localStorage.setItem('activeTab', 'calendar');

  const today = new Date();

  if (!calendarMonthInput.value) {
    calendarMonthInput.value = formatDate(today).slice(0, 7);
  }

  renderCalendar();
}

// Payment summary calculation support
function updatePaymentSummary() {
  const bookings = window.bookingsData || [];

  let paidAmount = 0;
  let pendingAmount = 0;
  let notPaidAmount = 0;

  bookings.forEach(booking => {
    const amount = Number(booking.fee || 0);
    const status = String(booking.status || '').trim().toLowerCase();

    if (status === 'paid') {
      paidAmount += amount;
    }
    else if (status === 'pending') {
      pendingAmount += amount;
    }
    else {
      notPaidAmount += amount;
    }
  });

  const paidCard = document.getElementById('paidAmountCard');
  const pendingCard = document.getElementById('pendingAmountCard');
  const notPaidCard = document.getElementById('notPaidAmountCard');

  if (paidCard) {
    paidCard.textContent = `₹${paidAmount.toLocaleString()}`;
  }

  if (pendingCard) {
    pendingCard.textContent = `₹${pendingAmount.toLocaleString()}`;
  }

  if (notPaidCard) {
    notPaidCard.textContent = `₹${notPaidAmount.toLocaleString()}`;
  }
}

function updatePaymentTable() {
  const bookings = window.bookingsData || [];
  const currentRole = window.currentUserRole || '';
  const tableBody = document.getElementById('paymentTableBody');

  if (!tableBody) {
    return;
  }

  if (bookings.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-muted py-3">
          No payment records found.
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = bookings.map(booking => {
    const owner = booking.owner || booking.created_by || '-';
    const swimmer = booking.student || '-';
    const packageName = booking.package || '-';
    const status = booking.status || 'Not Paid';
    const amount = Number(booking.fee || 0).toLocaleString();
    const isGuestPaid = currentRole !== 'trainer' && status === 'Paid';

    return `
      <tr>
        <td>${owner}</td>
        <td>${swimmer}</td>
        <td>${packageName}</td>
        <td>
          ${isGuestPaid ? `
            <span class="fw-semibold text-success">Paid</span>
          ` : `
            <select
              class="form-select form-select-sm payment-status-select"
              style="width: 120px;"
              data-booking-id="${booking.id || ''}">
              <option value="Not Paid" ${status === 'Not Paid' ? 'selected' : ''}>Not Paid</option>
              <option value="Pending Verification" ${status === 'Pending Verification' ? 'selected' : ''}>Pending Verification</option>
              <option value="Paid" ${status === 'Paid' ? 'selected' : ''}>Paid</option>
            </select>
          `}
        </td>
        <td>₹${amount}</td>
        <td>
          ${isGuestPaid ? `
            <span class="text-muted">Verified</span>
          ` : `
            <button
              type="button"
              class="btn btn-sm btn-success payment-status-update-btn"
              data-booking-id="${booking.id || ''}">
              Update Payment Status
            </button>
          `}
        </td>
      </tr>
    `;
  }).join('');
}

function initializePaymentStatusActions() {
  const buttons = document.querySelectorAll('.payment-status-update-btn');

  buttons.forEach(button => {
    button.addEventListener('click', async function() {
      const bookingId = this.dataset.bookingId;

      const row = this.closest('tr');
      const statusSelect = row?.querySelector('.payment-status-select');

      if (!bookingId || !statusSelect) {
        createToast('Unable to update payment status.', 'danger');
        return;
      }

      const selectedStatus = statusSelect.value;
      const originalHtml = this.innerHTML;

      this.disabled = true;
      this.innerHTML = `
        <span class="spinner-border spinner-border-sm me-1"></span>
        Updating...
      `;

      try {
        const formData = new FormData();
        formData.append('status', selectedStatus);

        const response = await fetch(
          `/update_payment_status/${bookingId}`,
          {
            method: 'POST',
            body: formData
          }
        );

        if (response.ok) {
          createToast('Payment status updated successfully');

          setTimeout(() => {
            window.location.reload();
          }, 800);
        } else {
          throw new Error('Update failed');
        }
      } catch (error) {
        createToast('Failed to update payment status', 'danger');

        this.disabled = false;
        this.innerHTML = originalHtml;
      }
    });
  });
}

function showPayments() {
  bookingsSection.style.display = 'none';

  if (bookSlotSection) {
    bookSlotSection.style.display = 'none';
  }

  calendarSection.style.display = 'none';

  if (paymentsSection) {
    paymentsSection.style.display = 'block';
    updatePaymentSummary();
    updatePaymentTable();
    initializePaymentStatusActions();
  }

  tabBookings.classList.remove('active');
  tabCalendar.classList.remove('active');

  if (tabBook) {
    tabBook.classList.remove('active');
  }

  if (tabPayments) {
    tabPayments.classList.add('active');
  }

  localStorage.setItem('activeTab', 'payments');
}

function renderCalendar() {

  if (!calendarMonthInput || !calendarGrid) return;

  const selectedMonth = calendarMonthInput.value;

  if (!selectedMonth) return;

  const [year, month] = getSelectedMonthParts(selectedMonth);

  const totalDays = new Date(year, month, 0).getDate();
  const weekDays = getWeekDays();

  const bookings = window.bookingsData || [];

  calendarGrid.innerHTML = '';

  const firstDayIndex = new Date(year, month - 1, 1).getDay();
  const totalCells = 42;

  for (let cellIndex = 0; cellIndex < totalCells; cellIndex++) {
    const day = cellIndex - firstDayIndex + 1;

    // Empty cells before the first day and after the last day
    if (day < 1 || day > totalDays) {
      const emptyCell = document.createElement('div');
      emptyCell.className = 'calendar-empty-cell';
      calendarGrid.appendChild(emptyCell);
      continue;
    }

    const formattedDay = getFormattedDay(day);
    const fullDate = `${year}-${month}-${formattedDay}`;

    const currentDate = new Date(fullDate);
    const dayName = weekDays[currentDate.getDay()];
    const isPastDay = isPastDate(currentDate);

    const dayBookings = bookings.filter(b => {
      const recurringDates = b.calendar_dates || [];
      return recurringDates.includes(fullDate);
    });

    // --------------------------------------
    // V0033.0 Step 12.1 - Add standalone make-up request events
    // --------------------------------------
    const standaloneMakeupEvents = [];

    bookings.forEach(booking => {
      if (!Array.isArray(booking.makeup_requests)) {
        return;
      }

      booking.makeup_requests.forEach(request => {
        // Skip if the requested date is already part of the
        // regular booking schedule.
        const isRegularBookingDate =
          Array.isArray(booking.calendar_dates) &&
          booking.calendar_dates.includes(request.requested_date);

        if (isRegularBookingDate) {
          return;
        }

        // Only render on the requested replacement date.
        if (request.requested_date !== fullDate) {
          return;
        }

        // Create a temporary booking-like object so the existing
        // rendering and modal logic can be reused.
        standaloneMakeupEvents.push({
          ...booking,
          calendar_dates: [request.requested_date],
          pending_request_id:
            request.status === 'pending' ? request.id : '',
          makeup_requests: [request]
        });
      });
    });

    // Merge standalone make-up events into this day's events.
    dayBookings.push(...standaloneMakeupEvents);

    const card = document.createElement('div');
    card.className = 'col-md-2 col-sm-3 col-6';

    card.innerHTML = `
      <div class="border rounded p-2 h-100 shadow-sm ${isPastDay ? 'bg-light text-muted opacity-50' : 'bg-light'}">

        <div class="d-flex justify-content-between align-items-center mb-2">
          <div class="fw-bold text-primary">${day}</div>
          <div class="small fw-semibold text-secondary">${dayName}</div>
        </div>

        <div class="calendar-events"></div>
      </div>
    `;

    calendarGrid.appendChild(card);

    const eventsContainer = card.querySelector('.calendar-events');

    if (dayBookings.length === 0) {
      eventsContainer.innerHTML = '<div class="small text-muted">No Bookings</div>';
      continue;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const eventDate = new Date(fullDate);
    eventDate.setHours(0, 0, 0, 0);

    const isPastSession = eventDate < today;

    dayBookings.forEach(booking => {

      const bookingDiv = document.createElement('div');
      bookingDiv.className = 'calendar-booking calendar-session';
      bookingDiv.style.cursor = 'pointer';
      bookingDiv.title = 'Click to open session options';

      // Data used by the calendar modal in dashboard.html
      bookingDiv.dataset.bookingId = booking.id || '';
      bookingDiv.dataset.student = booking.student || '';
      bookingDiv.dataset.package = booking.package || booking.package_type || '';
      bookingDiv.dataset.sessionDate = fullDate;
      // --------------------------------------
      // V0033.0 Step 9 - Available Make-Up Credit
      // --------------------------------------
      bookingDiv.dataset.availableMakeupCreditId =
        booking.available_makeup_credit_id || '';

      bookingDiv.dataset.hasAvailableMakeupCredit =
        booking.has_available_makeup_credit ? 'true' : 'false';
      bookingDiv.dataset.endDate = booking.end_date || '';
      bookingDiv.dataset.pendingRequestId =
        booking.pending_request_id || '';

      // --------------------------------------
      // V0033.0 Step 7 - Skip Eligibility Rules
      // --------------------------------------
      const packageType = booking.package || booking.package_type || '';
      const scheduledClasses = (booking.calendar_dates || []).length;

      // Count already-used skip credits for this booking from the data
      // loaded on the page, if available.
      const usedSkips = Number(booking.makeup_credits_used || 0);

      let maxSkips = 0;
      let validUntil = '';

      if (packageType === 'Monthly') {
        // Monthly package: maximum 2 skips.
        maxSkips = 2;

        // Valid until package end date + 5 days.
        if (booking.end_date) {
          const expiry = new Date(booking.end_date + 'T00:00:00');
          expiry.setDate(expiry.getDate() + 5);
          validUntil = formatDate(expiry);
        }
      } else if (packageType === 'Custom') {
        // Custom package: 1 skip for every 7 scheduled classes.
        maxSkips = Math.floor(scheduledClasses / 7);

        // Valid within 3 days from the skipped date.
        const sessionDateObj = new Date(fullDate + 'T00:00:00');
        sessionDateObj.setDate(sessionDateObj.getDate() + 3);
        validUntil = formatDate(sessionDateObj);
      }

      const skipRemaining = Math.max(0, maxSkips - usedSkips);

      bookingDiv.dataset.skipRemaining = String(skipRemaining);
      bookingDiv.dataset.validUntil = validUntil;
      bookingDiv.dataset.skipEligible = skipRemaining > 0 ? 'true' : 'false';

      if (isPastSession) {
        bookingDiv.classList.add('past-session');
      }

      // --------------------------------------
      // V0033.0 Step 10 - Calendar Status Indicators
      // --------------------------------------
      let statusLines = [];

      // Show "Skipped" on the original skipped session date.
      if (Array.isArray(booking.skipped_dates) &&
          booking.skipped_dates.includes(fullDate)) {
        statusLines.push(
          '<div class="small text-warning fw-semibold">🔶 Skipped</div>'
        );
      }

      // Show pending/approved/rejected on requested replacement dates.
      if (Array.isArray(booking.makeup_requests)) {
        booking.makeup_requests.forEach(request => {
          if (request.requested_date !== fullDate) {
            return;
          }

          if (request.status === 'pending') {
            statusLines.push(
              '<div class="small text-warning fw-semibold">🟡 Pending Approval</div>'
            );
          } else if (request.status === 'approved') {
            statusLines.push(
              '<div class="small text-success fw-semibold">🟢 Approved</div>'
            );
          } else if (request.status === 'rejected') {
            statusLines.push(
              '<div class="small text-danger fw-semibold">🔴 Rejected</div>'
            );
          }
        });
      }

      bookingDiv.innerHTML =
        `🏊 ${booking.student} • ⏰ ${booking.time || 'N/A'}` +
        (statusLines.length ? `<br>${statusLines.join('')}` : '');

      const existingEvents = eventsContainer.querySelectorAll('.calendar-booking');

      const duplicateExists = Array.from(existingEvents).some(el => {
        return el.innerText.trim() === bookingDiv.innerText.trim();
      });

      if (duplicateExists) {
        return;
      }

      eventsContainer.appendChild(bookingDiv);
    });
  }
}

function activateSwimmer(name) {
  swimmerRows.forEach(row => {
    row.classList.remove('border-primary', 'bg-light');

    const dot = row.querySelector('.swimmer-dot');
    if (dot) {
      dot.classList.remove('text-success');
      dot.classList.add('text-transparent');
    }
  });

  swimmerRows.forEach(row => {
    if (row.dataset.name === name) {
      row.classList.add('border-primary', 'bg-light');

      const dot = row.querySelector('.swimmer-dot');
      if (dot) {
        dot.classList.remove('text-transparent');
        dot.classList.add('text-success');
      }
    }
  });

  if (studentSelect) {
    studentSelect.value = name;
  }

  localStorage.setItem('activeSwimmer', name);
}

if (tabBookings && tabCalendar) {
  tabBookings.addEventListener('click', showBookings);
  tabCalendar.addEventListener('click', showCalendar);

  if (tabBook) {
    tabBook.addEventListener('click', showBookSlot);
  }
  if (tabPayments) {
    tabPayments.addEventListener('click', showPayments);
  }

  const savedTab = localStorage.getItem('activeTab');

  if (savedTab === 'book_slot' && tabBook) {
    showBookSlot();
  }
  else if (savedTab === 'calendar') {
    showCalendar();
  }
  else if (savedTab === 'payments') {
    showPayments();
  }
  else {
    showBookings();
  }
}

swimmerRows.forEach(row => {
  row.addEventListener('click', () => {
    activateSwimmer(row.dataset.name);
  });
});

if (studentSelect) {
  studentSelect.addEventListener('change', function() {
    activateSwimmer(this.value);
  });
}

const savedSwimmer = localStorage.getItem('activeSwimmer');
if (savedSwimmer) {
  activateSwimmer(savedSwimmer);
}

const swimmerAddForm = document.querySelector('form[action="/add_swimmer"]');
const swimmerNameInput = document.getElementById('swimmerNameInput');
const bookingForm = document.querySelector('form[action="/book"]');

function checkLocationConflict() {
  const bookings = window.bookingsData || [];

  const dateInput = document.querySelector('input[name="date"]');
  const locationInput = document.querySelector('input[name="location"]');
  const timeSelect = document.getElementById('timeSelect');
  const confirmBookingBtn = document.getElementById('confirmBookingBtn');
  const warning = document.getElementById('locationConflictWarning');

  if (!dateInput || !locationInput || !timeSelect || !confirmBookingBtn || !warning) {
    return;
  }

  const selectedDate = (dateInput.value || '').trim();
  const selectedTime = (timeSelect.value || '').trim();
  const selectedLocation = (locationInput.value || '').trim().toLowerCase();

  if (!selectedDate || !selectedTime || !selectedLocation) {
    warning.style.display = 'none';
    updateSwimmerBookingState();
    return;
  }

  const conflictFound = bookings.some(booking => {
    const bookingDate = String(booking.start_date || '').trim();
    const bookingTime = String(booking.time || '').trim();
    const bookingLocation = String(booking.location || '').trim().toLowerCase();

    return (
      bookingDate === selectedDate &&
      bookingTime === selectedTime &&
      bookingLocation &&
      bookingLocation !== selectedLocation
    );
  });

  if (conflictFound) {
    warning.style.display = 'block';
    confirmBookingBtn.disabled = true;
  } else {
    warning.style.display = 'none';

    // Re-enable booking when conflict is cleared.
    confirmBookingBtn.disabled = false;

    updateSwimmerBookingState();
  }
}
// ---------- SCROLL POSITION HELPERS ----------
function saveScrollPosition() {
  sessionStorage.setItem('dashboardScrollY', window.scrollY);
}

function restoreScrollPosition() {
  const savedScroll = sessionStorage.getItem('dashboardScrollY');

  if (savedScroll !== null) {
    setTimeout(() => {
      window.scrollTo(0, parseInt(savedScroll));
    }, 100);
  }
}

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

function resetBookingForm() {
  if (bookingForm) {
    bookingForm.reset();
  }

  if (studentSelect) {
    studentSelect.value = '';
  }

  if (startDateInput) {
    startDateInput.value = getTodayDate();
  }

  if (endDateInput) {
    endDateInput.value = '';
  }

  dayCheckboxes.forEach(cb => {
    cb.checked = false;
  });

  if (selectedDaysInput) {
    selectedDaysInput.value = '';
  }

  if (selectedDaysPreview) {
    selectedDaysPreview.innerText = 'No days selected';
  }

  if (feeInput) {
    feeInput.value = 0;
  }

  if (pkg) {
    pkg.value = 'Single';
  }

  localStorage.removeItem('activeSwimmer');

  updateAllowedDays();
  generateTimeSlots();
}

if (swimmerAddForm && swimmerNameInput) {
  swimmerAddForm.addEventListener('submit', () => {
    localStorage.setItem('activeSwimmer', swimmerNameInput.value.trim());
    localStorage.setItem('activeTab', 'book_slot');
    localStorage.setItem('swimmerAdded', 'true');
  });
}

if (bookingForm) {
  bookingForm.addEventListener('submit', (event) => {
    const confirmBookingBtn = document.getElementById('confirmBookingBtn');
    const confirmBookingSpinner = document.getElementById('confirmBookingSpinner');
    const confirmBookingText = document.getElementById('confirmBookingText');

    // Monthly package requires exactly 2 or 3 selected class days.
    if (pkg && pkg.value === 'Monthly') {
      const selectedCount = document.querySelectorAll('.class-day:checked').length;

      if (selectedCount < 2 || selectedCount > 3) {
        event.preventDefault();

        createToast(
          'Monthly package requires selecting 2 or 3 class days.',
          'danger',
          3000
        );

        return;
      }
    }

    // Show loading state immediately to prevent duplicate clicks.
    if (confirmBookingBtn) {
      confirmBookingBtn.disabled = true;
    }

    if (confirmBookingSpinner) {
      confirmBookingSpinner.classList.remove('d-none');
    }

    if (confirmBookingText) {
      confirmBookingText.textContent = 'Processing...';
    }

    localStorage.setItem('activeTab', 'bookings');
    // REMOVED the setTimeout that was clearing form parameters prematurely!
  });
}

window.addEventListener('load', () => {
  restoreScrollPosition();
  const swimmerAdded = localStorage.getItem('swimmerAdded');
  const urlParams = new URLSearchParams(window.location.search);
  const swimmerExists = urlParams.get('swimmer_exists');
  const bookingConflict = window.location.search.includes('booking_conflict');

  if (bookingConflict) {
    createToast('⏰ Duplicate bookings', 'danger', 2500);
    localStorage.removeItem('bookingSuccess');
    window.history.replaceState({}, document.title, window.location.pathname);
  }

  if (swimmerExists === 'true') {
    createToast('⚠️ Swimmer already exists', 'danger', 2000);
    window.history.replaceState({}, document.title, window.location.pathname);
  }
});
  if (calendarMonthInput) {
    calendarMonthInput.addEventListener('change', renderCalendar);
  }

// Disable booking if no swimmers are available
function updateSwimmerBookingState() {
  const studentSelect = document.getElementById('studentSelect');
  const confirmBookingBtn = document.getElementById('confirmBookingBtn');

  if (!confirmBookingBtn) {
    return;
  }

  // V0040 booking page uses an INPUT, not a SELECT.
  if (studentSelect && studentSelect.tagName === 'INPUT') {
    const warning = document.getElementById('noSwimmersWarning');

    if (warning) {
      warning.remove();
    }

    confirmBookingBtn.disabled = !studentSelect.value.trim();
    return;
  }

  if (!studentSelect) {
    return;
  }

  const hasValidOptions = Array.from(studentSelect.options || []).some(option => {
    return option.value && option.value.trim() !== '';
  });

  let warning = document.getElementById('noSwimmersWarning');

  if (!hasValidOptions) {
    confirmBookingBtn.disabled = true;

    if (!warning) {
      warning = document.createElement('div');
      warning.id = 'noSwimmersWarning';
      warning.className = 'alert alert-warning mt-2';
      warning.textContent = 'Add a swimmer to book a slot.';
      studentSelect.parentElement.appendChild(warning);
    }
  } else {
    const conflictWarning = document.getElementById('locationConflictWarning');

    if (!conflictWarning || conflictWarning.style.display === 'none') {
      confirmBookingBtn.disabled = false;
    }

    if (warning) {
      warning.remove();
    }
  }
}



window.addEventListener('load', updateSwimmerBookingState);

const bookingStudentInput = document.getElementById('studentSelect');

if (bookingStudentInput && bookingStudentInput.tagName === 'INPUT') {
  bookingStudentInput.addEventListener('input', updateSwimmerBookingState);
}

// --------------------------------------
// V0034.0.1 - Generic Form Loading Helper
// Used for Update Notice Board spinner.
// --------------------------------------
function enableFormLoading(formId, loadingText) {
  const form = document.getElementById(formId);

  if (!form) {
    return;
  }

  form.addEventListener('submit', function() {
    const submitButton = form.querySelector('button[type="submit"]');

    if (!submitButton || submitButton.disabled) {
      return;
    }

    submitButton.disabled = true;

    const spinner = submitButton.querySelector('.spinner-border');
    if (spinner) {
      spinner.classList.remove('d-none');
    }

    const textSpan =
      submitButton.querySelector('#updateNoticeText') ||
      submitButton.querySelector('span:last-child');

    if (textSpan) {
      textSpan.textContent = loadingText;
    } else {
      submitButton.textContent = loadingText;
    }
  });
}

// Enable loading animation for the trainer Notice Board form.
enableFormLoading('updateNoticeForm', 'Updating...');

// --------------------------------------
// V0033.5.0 - Auto Logout After Inactivity
// --------------------------------------
(function () {
  let inactivityTimer;
  let countdownTimer;
  let countdown = 30;

  const INACTIVITY_MS = 30 * 1000; // 30 seconds

  const toast = document.getElementById('inactiveLogoutToast');
  const countdownElement = document.getElementById('logoutCountdown');
  const stayLoggedInBtn = document.getElementById('stayLoggedInBtn');


  if (!toast || !countdownElement || !stayLoggedInBtn) {
    return;
  }

  function resetInactivityTimer() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(showLogoutWarning, INACTIVITY_MS);
  }

  function showLogoutWarning() {
    countdown = 30;
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

  function stayLoggedIn() {
    toast.style.display = 'none';
    clearInterval(countdownTimer);
    resetInactivityTimer();
  }

  stayLoggedInBtn.addEventListener('click', stayLoggedIn);

  ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll']
    .forEach(eventName => {
      document.addEventListener(
        eventName,
        resetInactivityTimer,
        true
      );
    });

  resetInactivityTimer();
})();

