document.addEventListener('DOMContentLoaded', function () {
    const calendarMonthInput = document.getElementById('calendarMonthInput');
    const calendarGrid = document.getElementById('calendarGrid');

    if (!calendarMonthInput || !calendarGrid) {
        return;
    }

    function renderCalendar(year, month) {
        calendarGrid.innerHTML = '';

        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);

        const startDay = firstDay.getDay();
        const totalDays = lastDay.getDate();

        const bookings = window.bookingsData || [];

        const sessionMap = {};

        // // Debug: log all bookings loaded for the calendar
        // console.log('Calendar bookings loaded:', bookings);

        bookings.forEach(booking => {
            // New booking structure stores generated session dates in calendar_dates
            if (Array.isArray(booking.calendar_dates) && booking.calendar_dates.length > 0) {
                booking.calendar_dates.forEach(dateKey => {
                    if (!sessionMap[dateKey]) {
                        sessionMap[dateKey] = [];
                    }

                    const dateIndex = booking.calendar_dates.indexOf(dateKey);
                    const completedCount = booking.completed_classes || 0;

                    sessionMap[dateKey].push({
                        student: booking.student || booking.student_name || booking.owner_name || 'Swimmer',
                        time: booking.time || booking.session_time || '',
                        completed: dateIndex < completedCount
                    });
                });

                return;
            }

            // Support both recurring-package bookings and generated session dates
            if (booking.session_date) {
                const dateKey = booking.session_date;

                if (!sessionMap[dateKey]) {
                    sessionMap[dateKey] = [];
                }

                sessionMap[dateKey].push({
                    student: booking.student || booking.student_name || 'Swimmer',
                    time: booking.time || booking.session_time || ''
                });

                return;
            }

            const startDate = new Date(booking.start_date);
            const endDate = new Date(booking.end_date || booking.start_date);

            const selectedDays = (booking.selected_days || '')
                .split(',')
                .map(d => d.trim().toLowerCase())
                .filter(Boolean);

            const current = new Date(startDate);

            while (current <= endDate) {
                const dayName = current.toLocaleDateString('en-US', {
                    weekday: 'long'
                }).toLowerCase();

                if (selectedDays.length === 0 || selectedDays.includes(dayName)) {
                    const dateKey = current.toISOString().split('T')[0];

                    if (!sessionMap[dateKey]) {
                        sessionMap[dateKey] = [];
                    }

                    sessionMap[dateKey].push({
                        student: booking.student || booking.student_name || 'Swimmer',
                        time: booking.time || booking.session_time || ''
                    });
                }

                current.setDate(current.getDate() + 1);
            }
        });

        for (let i = 0; i < startDay; i++) {
            const emptyCell = document.createElement('div');
            emptyCell.className = 'col border rounded p-3';
            calendarGrid.appendChild(emptyCell);
        }

        const today = new Date();

        for (let day = 1; day <= totalDays; day++) {
            const cell = document.createElement('div');

            const dateKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

            const dayBookings = sessionMap[dateKey] || [];

            const isToday =
                day === today.getDate() &&
                month === today.getMonth() &&
                year === today.getFullYear();

            cell.className = isToday
                ? 'calendar-day-card border border-primary rounded shadow-sm p-2 bg-primary-subtle'
                : 'calendar-day-card border rounded shadow-sm bg-white p-2';

            cell.style.minHeight = '100px';

            let bookingsHtml = '';

            if (dayBookings.length > 0) {
                bookingsHtml += `
                    <div class="calendar-session-count">
                        ${dayBookings.length} Session${dayBookings.length > 1 ? 's' : ''}
                    </div>
                    <div class="calendar-bookings-container">`;

                dayBookings.forEach(b => {
                    bookingsHtml += `
                        <div class="calendar-booking-chip ${b.completed ? 'completed-session' : ''}">
                            <div class="calendar-booking-name">
                                <span>🏊</span>
                                <span class="${b.completed ? 'completed-text' : ''}">${b.student}</span>
                            </div>
                            <div class="calendar-booking-time ${b.completed ? 'completed-text' : ''}">${b.time}</div>
                        </div>`;
                });

                bookingsHtml += '</div>';
            }

            const dayLabel = new Date(year, month, day)
                .toLocaleDateString('en-US', { weekday: 'short' });

            cell.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div class="fw-bold text-primary" style="font-size:18px;line-height:1;">${day}</div>
                    <div class="text-muted small fw-bold ${dayLabel === 'Sat' ? 'text-warning' : dayLabel === 'Sun' ? 'text-danger' : ''}">${dayLabel}</div>
                </div>
                ${bookingsHtml}
            `;  

            calendarGrid.appendChild(cell);
        }
    }

    const today = new Date();
    const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;

    calendarMonthInput.value = currentMonth;

    renderCalendar(today.getFullYear(), today.getMonth());

    calendarMonthInput.addEventListener('change', function () {
        const [year, month] = this.value.split('-').map(Number);
        renderCalendar(year, month - 1);
    });
});