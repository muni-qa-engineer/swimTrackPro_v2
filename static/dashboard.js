

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
    SINGLE_DAY: 750,
    MONTHLY_PACKAGE: 9000,
    CUSTOM_PACKAGE_BASE: 9000
  };

  const GROUP_DISCOUNTS = {
    2: 10,
    3: 20,
    4: 25,
    5: 30
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

    if (pkg.value === 'Single') {
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

    let baseFee = 0;

    if (pkg.value === 'Single') {
      baseFee = PRICING.SINGLE_DAY;
    }
    else if (pkg.value === 'Monthly') {
      baseFee = PRICING.MONTHLY_PACKAGE;
    }
    else {
      const startDateInput = document.querySelector('input[name="date"]');
      const endDateInput = document.querySelector('input[name="end_date"]');

      if (!startDateInput.value || !endDateInput.value) {
        feeInput.value = 0;
        return;
      }

      const start = new Date(startDateInput.value);
      const end = new Date(endDateInput.value);

      let totalClasses = 0;

      const selectedDayIndexes = selected.map(day => {
        const map = {
          'Sunday': 0,
          'Monday': 1,
          'Tuesday': 2,
          'Wednesday': 3,
          'Thursday': 4,
          'Friday': 5,
          'Saturday': 6
        };
        return map[day];
      });

      const current = new Date(start);

      while (current <= end) {
        if (selectedDayIndexes.includes(current.getDay())) {
          totalClasses++;
        }
        current.setDate(current.getDate() + 1);
      }

      const feePer12Classes = PRICING.CUSTOM_PACKAGE_BASE;
      baseFee = Math.ceil((totalClasses / 12) * feePer12Classes);
    }

    // GROUP DISCOUNT SLABS
    let discountPercent = 0;

    if (persons >= 4) {
      discountPercent = GROUP_DISCOUNTS[4];
    }
    else if (GROUP_DISCOUNTS[persons]) {
      discountPercent = GROUP_DISCOUNTS[persons];
    }

    const totalFee = baseFee * persons;
    const discountAmount = Math.ceil((totalFee * discountPercent) / 100);
    const finalFee = totalFee - discountAmount;

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
}

initializeBookingEventListeners();
updateAllowedDays();
generateTimeSlots();
const tabBookings = document.getElementById('tabBookings');
const tabBook = document.getElementById('tabBook');
const tabCalendar = document.getElementById('tabCalendar');

const bookingsSection = document.getElementById('bookingsSection');
const bookSlotSection = document.getElementById('bookSlotSection');
const calendarSection = document.getElementById('calendarSection');

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

  tabBookings.classList.add('active');
  if (tabBook) {
    tabBook.classList.remove('active');
  }
  tabCalendar.classList.remove('active');

  localStorage.setItem('activeTab', 'bookings');
}

function showBookSlot() {
  bookingsSection.style.display = 'none';
  if (bookSlotSection) {
    bookSlotSection.style.display = 'flex';
  }
  calendarSection.style.display = 'none';

  if (tabBook) {
    tabBook.classList.add('active');
  }
  tabBookings.classList.remove('active');
  tabCalendar.classList.remove('active');

  localStorage.setItem('activeTab', 'book_slot');
}

function showCalendar() {
  bookingsSection.style.display = 'none';
  if (bookSlotSection) {
    bookSlotSection.style.display = 'none';
  }
  calendarSection.style.display = 'block';

  tabCalendar.classList.add('active');
  tabBookings.classList.remove('active');
  if (tabBook) {
    tabBook.classList.remove('active');
  }

  localStorage.setItem('activeTab', 'calendar');

  const today = new Date();

  if (!calendarMonthInput.value) {
    calendarMonthInput.value = formatDate(today).slice(0, 7);
  }

  renderCalendar();
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
      bookingDiv.className = 'calendar-booking';

      if (isPastSession) {
        bookingDiv.classList.add('past-session');
      }

      bookingDiv.innerHTML = `🏊 ${booking.student} • ⏰ ${booking.time || 'N/A'}`;

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

  const savedTab = localStorage.getItem('activeTab');

  if (savedTab === 'book_slot' && tabBook) {
    showBookSlot();
  }
  else if (savedTab === 'calendar') {
    showCalendar();
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
  bookingForm.addEventListener('submit', () => {
    const confirmBookingBtn = document.getElementById('confirmBookingBtn');
    const confirmBookingSpinner = document.getElementById('confirmBookingSpinner');
    const confirmBookingText = document.getElementById('confirmBookingText');

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

    localStorage.setItem('bookingSuccess', 'true');
    localStorage.setItem('activeTab', 'bookings');

    setTimeout(() => {
      resetBookingForm();
    }, 100);
  });
}

window.addEventListener('load', () => {
  restoreScrollPosition();
  const bookingSuccess = localStorage.getItem('bookingSuccess');
  const swimmerAdded = localStorage.getItem('swimmerAdded');
  const urlParams = new URLSearchParams(window.location.search);
  const swimmerExists = urlParams.get('swimmer_exists');
  const bookingConflict = window.location.search.includes('booking_conflict');

  if (bookingSuccess === 'true' && !bookingConflict) {
    createToast('✅ Booking successful', 'success', 2000);
    localStorage.removeItem('bookingSuccess');
    showBookings();
    resetBookingForm();
  }

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

  if (!studentSelect || !confirmBookingBtn) {
    return;
  }

  const hasValidOptions = Array.from(studentSelect.options).some(option => {
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
    confirmBookingBtn.disabled = false;

    if (warning) {
      warning.remove();
    }
  }
}


window.addEventListener('load', updateSwimmerBookingState);

