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

        bookings.forEach(booking => {
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
                        time: booking.time || ''
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

        for (let day = 1; day <= totalDays; day++) {
            const cell = document.createElement('div');
            cell.className = 'calendar-day-card border rounded shadow-sm bg-white p-2';
            cell.style.minHeight = '100px';

            const dateKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

            const dayBookings = sessionMap[dateKey] || [];

            let bookingsHtml = '';

            dayBookings.slice(0, 3).forEach(b => {
                bookingsHtml += `
                    <div class="calendar-booking-chip">
                        <div class="calendar-booking-name">
                            <span>🏊</span>
                            <span>${b.student}</span>
                        </div>
                        <div class="calendar-booking-time">${b.time}</div>
                    </div>`;
            });

            if (dayBookings.length > 3) {
                bookingsHtml += `<div class="small text-muted mt-1">+${dayBookings.length - 3} more</div>`;
            }

            const dayLabel = new Date(year, month, day)
                .toLocaleDateString('en-US', { weekday: 'short' });

            cell.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div class="fw-bold text-primary" style="font-size:18px;line-height:1;">${day}</div>
                    <div class="text-muted small fw-bold">${dayLabel}</div>
                </div>
                ${bookingsHtml || '<div class="text-muted" style="font-size:12px;">No Bookings</div>'}
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