function escapePaymentHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

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
    else if (status === 'pending' || status === 'pending verification') {
      pendingAmount += amount;
    }
    else {
      notPaidAmount += amount;
    }
  });

  const paidCard = document.getElementById('paidAmountCard');
  const pendingCard = document.getElementById('pendingAmountCard');
  const notPaidCard = document.getElementById('notPaidAmountCard');

  if (paidCard) paidCard.innerHTML = `<i class="fa-solid fa-indian-rupee-sign"></i>${paidAmount.toLocaleString()}`;
  if (pendingCard) pendingCard.innerHTML = `<i class="fa-solid fa-indian-rupee-sign"></i>${pendingAmount.toLocaleString()}`;
  if (notPaidCard) notPaidCard.innerHTML = `<i class="fa-solid fa-indian-rupee-sign"></i>${notPaidAmount.toLocaleString()}`;
}

function updatePaymentTable() {
  const bookings = window.bookingsData || [];
  const currentRole = window.currentUserRole || '';
  const tableBody = document.getElementById('paymentTableBody');

  if (!tableBody) return;

  if (bookings.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-muted py-4" style="color: var(--color-text-muted) !important;">
          No payment records found.
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = bookings.map((booking, index) => {
    const sNo = index + 1;
    const owner = booking.owner || booking.created_by || '-';
    const swimmer = booking.student || '-';
    const packageName = booking.package || '-';
    const status = booking.status || 'Not Paid';
    const amount = Number(booking.fee || 0).toLocaleString();
    const isTrainer = currentRole === 'trainer' || currentRole === 'admin';
    const isPendingVerification = status === 'Pending Verification';
    const isPaid = status === 'Paid';

    return `
      <tr>
        <td style="text-align: center; color: var(--color-text-muted); font-weight: 600; font-size: 0.85rem; width: 50px;">${sNo}</td>
        <td style="color: white; font-weight: 600;">${escapePaymentHtml(owner)}</td>
        <td>${escapePaymentHtml(swimmer)}</td>
        <td>${escapePaymentHtml(packageName)}</td>
        <td>
          ${isTrainer ? `
            ${isPendingVerification ? `
              <div class="flex gap-2">
                <button type="button" class="btn btn-primary btn-sm payment-status-action-btn" data-booking-id="${booking.id || ''}" data-status="Paid" style="padding: 0.35rem 0.75rem; font-size: 0.8rem; border-radius: var(--radius-sm);">
                  <i class="fa-solid fa-circle-check"></i> Verify
                </button>
                <button type="button" class="btn btn-outline btn-sm payment-status-action-btn" data-booking-id="${booking.id || ''}" data-status="Not Paid" style="border-color: var(--color-danger); color: var(--color-danger); padding: 0.35rem 0.75rem; font-size: 0.8rem; border-radius: var(--radius-sm);">
                  <i class="fa-solid fa-circle-xmark"></i> Reject
                </button>
              </div>
            ` : `
              <span class="badge ${isPaid ? 'badge-success' : 'badge-danger'}">
                ${status}
              </span>
            `}
          ` : `
            ${isPaid ? `
              <span class="badge badge-success">Paid</span>
            ` : isPendingVerification ? `
              <span class="badge badge-warning">Pending Verification</span>
            ` : `
              <select class="form-select form-select-sm payment-status-select" data-booking-id="${booking.id || ''}" style="background: rgba(0,0,0,0.4); color: white; border: 1px solid rgba(255,255,255,0.1); width: 150px; font-size: 0.8rem;">
                <option value="Not Paid" ${status === 'Not Paid' ? 'selected' : ''}>Not Paid</option>
                <option value="Paid">Mark as Paid</option>
              </select>
            `}
          `}
        </td>
        <td>₹${amount}</td>
        <td>
          ${isTrainer ? `
            ${isPendingVerification ? 'Awaiting Decision' : 'Verified'}
          ` : `
            ${isPaid ? `
              <span class="badge badge-success"><i class="fa-solid fa-circle-check"></i> Verified</span>
            ` : isPendingVerification ? `
              <span class="badge badge-warning"><i class="fa-solid fa-hourglass-half"></i> Pending</span>
            ` : `
              <a href="upi://pay?pa=${window.upiId || ''}&pn=${encodeURIComponent(window.accountHolderName || '')}&am=${booking.fee || 0}&cu=INR&tn=SwimTrackPro%20Payment"
                class="btn btn-primary btn-sm" style="padding: 0.35rem 0.75rem; font-size: 0.8rem;"
                title="Open UPI App">
                <i class="fa-solid fa-credit-card"></i> Pay Now (₹${booking.fee || 0})
              </a>
            `}
          `}
        </td>
      </tr>
    `;
  }).join('');
  
  // Re-bind actions since table was populated
  initializePaymentStatusActions();
}

function initializePaymentStatusActions() {
  // Trainer action buttons for verifying/rejecting payment
  const trainerButtons = document.querySelectorAll('.payment-status-action-btn');
  trainerButtons.forEach(button => {
    button.addEventListener('click', async function() {
      const bookingId = this.dataset.bookingId;
      const selectedStatus = this.dataset.status;
      this.disabled = true;
      this.textContent = 'Processing...';

      try {
        const formData = new FormData();
        formData.append('status', selectedStatus);

        const response = await fetch(`/update_payment_status/${bookingId}`, {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          window.location.reload();
        } else {
          throw new Error('Update failed');
        }
      } catch (error) {
        alert('Failed to update payment status');
        this.disabled = false;
        this.innerHTML = 'Retry';
      }
    });
  });

  // Swimmer status select dropdown change
  const selectDropdowns = document.querySelectorAll('.payment-status-select');
  selectDropdowns.forEach(select => {
    select.addEventListener('change', async function() {
      const bookingId = this.dataset.bookingId;
      const selectedStatus = this.value;
      
      if (selectedStatus === 'Paid') {
        const confirmChange = await (typeof showConfirmToast === 'function' ? showConfirmToast({
          title: 'Confirm Payment Status',
          message: 'Have you successfully paid for this booking? Changing this status will alert the coach/admin for verification.',
          confirmText: 'Yes',
          cancelText: 'No',
          type: 'primary'
        }) : Promise.resolve(window.confirm('Have you successfully paid for this booking? Changing this status will alert the coach/admin for verification.')));
        if (!confirmChange) {
          this.value = 'Not Paid';
          return;
        }
      }

      this.disabled = true;

      try {
        const formData = new FormData();
        formData.append('status', selectedStatus);

        const response = await fetch(`/update_payment_status/${bookingId}`, {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          window.location.reload();
        } else {
          throw new Error('Update failed');
        }
      } catch (error) {
        alert('Failed to update payment status');
        this.disabled = false;
        this.value = 'Not Paid';
      }
    });
  });
}

// -------------------------------------------------------------
// Payment Calculations Section (Member-by-Member Breakdown)
// -------------------------------------------------------------
let currentCalcFilter = 'all';
let currentCalcSearch = '';

function updatePaymentCalculations(statusFilter = currentCalcFilter, searchQuery = currentCalcSearch) {
  currentCalcFilter = statusFilter;
  currentCalcSearch = searchQuery;

  const bookings = window.bookingsData || [];
  const currentRole = window.currentUserRole || 'guest';
  const container = document.getElementById('paymentCalculationsList');
  const totalReceivedEl = document.getElementById('calcTotalReceived');
  const totalPendingEl = document.getElementById('calcTotalPending');
  const grandTotalEl = document.getElementById('calcGrandTotal');
  const countAllEl = document.getElementById('calcCountAll');
  const countReceivedEl = document.getElementById('calcCountReceived');
  const countPendingEl = document.getElementById('calcCountPending');

  if (!container) return;

  // Group bookings by Member/Owner (or by Swimmer for guest view)
  const memberMap = {};

  bookings.forEach(b => {
    // For trainer/admin: member is owner/parent (fallback to student)
    // For guest: member is student (fallback to owner)
    const rawName = (currentRole === 'trainer' || currentRole === 'admin')
      ? (b.owner || b.created_by || b.student || 'Unknown Member')
      : (b.student || b.owner || 'Swimmer');

    const cleanName = String(rawName).trim() || 'Unknown Member';

    if (!memberMap[cleanName]) {
      memberMap[cleanName] = {
        name: cleanName,
        swimmers: new Set(),
        packages: new Set(),
        received: 0,
        pending: 0,
        total: 0,
        bookingCount: 0
      };
    }

    if (b.student) memberMap[cleanName].swimmers.add(b.student);
    if (b.package) memberMap[cleanName].packages.add(b.package);

    const amount = Number(b.fee || 0);
    const status = String(b.status || '').trim().toLowerCase();

    if (status === 'paid') {
      memberMap[cleanName].received += amount;
    } else {
      memberMap[cleanName].pending += amount;
    }
    memberMap[cleanName].total += amount;
    memberMap[cleanName].bookingCount += 1;
  });

  const memberList = Object.values(memberMap);

  // Compute counts for status pills
  let countAll = memberList.length;
  let countReceived = 0;
  let countPending = 0;

  memberList.forEach(m => {
    if (m.received > 0) countReceived++;
    if (m.pending > 0) countPending++;
  });

  if (countAllEl) countAllEl.textContent = countAll;
  if (countReceivedEl) countReceivedEl.textContent = countReceived;
  if (countPendingEl) countPendingEl.textContent = countPending;

  // Apply filters
  const query = (searchQuery || '').trim().toLowerCase();
  const filtered = memberList.filter(m => {
    // Status filter
    if (statusFilter === 'received' && m.received <= 0) return false;
    if (statusFilter === 'pending' && m.pending <= 0) return false;

    // Search query
    if (query) {
      const matchName = m.name.toLowerCase().includes(query);
      const matchSwimmer = Array.from(m.swimmers).some(s => s.toLowerCase().includes(query));
      if (!matchName && !matchSwimmer) return false;
    }
    return true;
  });

  // Calculate filtered totals for footer
  let filteredReceived = 0;
  let filteredPending = 0;
  filtered.forEach(m => {
    filteredReceived += m.received;
    filteredPending += m.pending;
  });
  const filteredGrandTotal = filteredReceived + filteredPending;

  if (totalReceivedEl) totalReceivedEl.textContent = `₹${filteredReceived.toLocaleString()}`;
  if (totalPendingEl) totalPendingEl.textContent = `₹${filteredPending.toLocaleString()}`;
  if (grandTotalEl) grandTotalEl.textContent = `₹${filteredGrandTotal.toLocaleString()}`;

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="text-center py-4 text-muted small" style="background: rgba(255,255,255,0.02); border-radius: var(--radius-sm); border: 1px dashed rgba(255,255,255,0.08);">
        <i class="fa-solid fa-filter-circle-xmark mb-2 d-block" style="font-size: 1.5rem; opacity: 0.5;"></i>
        No calculations match the selected filter.
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(m => {
    const swimmerNames = Array.from(m.swimmers).join(', ');
    const isFullyPaid = m.received > 0 && m.pending === 0;
    const isPendingOnly = m.pending > 0 && m.received === 0;
    const isPartial = m.received > 0 && m.pending > 0;

    let badgeHtml = '';
    if (isFullyPaid) {
      badgeHtml = `<span class="badge bg-success-subtle text-success border border-success-subtle" style="font-size: 0.7rem; font-weight: 700;"><i class="fa-solid fa-check me-1"></i> Paid</span>`;
    } else if (isPendingOnly) {
      badgeHtml = `<span class="badge bg-danger-subtle text-danger border border-danger-subtle" style="font-size: 0.7rem; font-weight: 700;"><i class="fa-solid fa-hourglass-half me-1"></i> Pending</span>`;
    } else {
      badgeHtml = `<span class="badge bg-warning-subtle text-warning border border-warning-subtle" style="font-size: 0.7rem; font-weight: 700;"><i class="fa-solid fa-circle-exclamation me-1"></i> Partial</span>`;
    }

    let statementHtml = '';
    if (isFullyPaid) {
      statementHtml = `
        <div class="d-flex align-items-center gap-2 text-success small" style="font-size: 0.8rem; font-weight: 600;">
          <i class="fa-solid fa-circle-check"></i>
          <span>You received payment from <strong>${escapePaymentHtml(m.name)}</strong> = <strong>₹${m.received.toLocaleString()}</strong></span>
        </div>
      `;
    } else if (isPendingOnly) {
      statementHtml = `
        <div class="d-flex align-items-center gap-2 text-warning small" style="font-size: 0.8rem; font-weight: 600;">
          <i class="fa-solid fa-clock"></i>
          <span>Your payment pending with <strong>${escapePaymentHtml(m.name)}</strong> = <strong>₹${m.pending.toLocaleString()}</strong></span>
        </div>
      `;
    } else {
      statementHtml = `
        <div class="d-flex flex-column gap-1 small" style="font-size: 0.78rem;">
          <div class="text-success" style="font-weight: 600;">
            <i class="fa-solid fa-circle-check me-1"></i> You received payment from <strong>${escapePaymentHtml(m.name)}</strong> = <strong>₹${m.received.toLocaleString()}</strong>
          </div>
          <div class="text-warning" style="font-weight: 600;">
            <i class="fa-solid fa-clock me-1"></i> Your payment pending with <strong>${escapePaymentHtml(m.name)}</strong> = <strong>₹${m.pending.toLocaleString()}</strong>
          </div>
        </div>
      `;
    }

    return `
      <div class="p-2.5 rounded mb-2" style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06);">
        <div class="d-flex justify-content-between align-items-center mb-1.5">
          <div class="d-flex align-items-center gap-2 min-w-0">
            <span class="text-white fw-bold text-truncate" style="font-size: 0.88rem;" title="${escapePaymentHtml(m.name)}">
              <i class="fa-solid fa-user text-primary me-1" style="font-size: 0.75rem;"></i>${escapePaymentHtml(m.name)}
            </span>
            ${swimmerNames ? `<span class="text-muted small text-truncate" style="font-size: 0.72rem;">(Swimmer: ${escapePaymentHtml(swimmerNames)})</span>` : ''}
          </div>
          <div>${badgeHtml}</div>
        </div>
        ${statementHtml}
      </div>
    `;
  }).join('');
}

// Bind calculations filter buttons and search input
function initializePaymentCalculationsEvents() {
  // If server-rendered calculations are already active and wired, do not duplicate
  if (document.querySelectorAll('.calc-member-item').length > 0) {
    return;
  }

  const filterButtons = document.querySelectorAll('.calc-filter-btn');
  filterButtons.forEach(btn => {
    btn.addEventListener('click', function() {
      filterButtons.forEach(b => {
        b.classList.remove('active');
        b.style.background = 'rgba(255, 255, 255, 0.05)';
        b.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        b.style.color = '#cbd5e1';
      });
      this.classList.add('active');
      this.style.background = 'rgba(6, 182, 212, 0.2)';
      this.style.borderColor = 'rgba(6, 182, 212, 0.5)';
      this.style.color = '#38bdf8';

      const filterType = this.dataset.filter || 'all';
      updatePaymentCalculations(filterType, currentCalcSearch);
    });
  });

  const searchInput = document.getElementById('memberCalculationSearch');
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      updatePaymentCalculations(currentCalcFilter, this.value);
    });
  }
}

// -------------------------------------------------------------
// Download Payment Records Functions (PDF, PNG, JPEG, CSV)
// -------------------------------------------------------------
async function downloadPaymentRecords(format) {
  if (format === 'csv') {
    downloadPaymentRecordsCSV();
    return;
  }

  const recordsPanel = document.getElementById('paymentRecordsPanel');
  if (!recordsPanel) return;

  const downloadDropdown = recordsPanel.querySelector('.dropdown');
  const scrollWrapper = recordsPanel.querySelector('.payment-records-scroll');

  const originalDropdownDisplay = downloadDropdown ? downloadDropdown.style.display : '';
  const originalMaxHeight = scrollWrapper ? scrollWrapper.style.maxHeight : '';
  const originalOverflow = scrollWrapper ? scrollWrapper.style.overflow : '';

  // Expand panel temporarily to capture all rows without scroll cutoff
  if (downloadDropdown) downloadDropdown.style.display = 'none';
  if (scrollWrapper) {
    scrollWrapper.style.maxHeight = 'none';
    scrollWrapper.style.overflow = 'visible';
  }

  try {
    if (typeof html2canvas === 'function') {
      const canvas = await html2canvas(recordsPanel, {
        scale: 2,
        backgroundColor: '#18181b',
        useCORS: true,
        logging: false,
        onclone: (clonedDoc) => {
          const clonedPanel = clonedDoc.getElementById('paymentRecordsPanel');
          if (clonedPanel) {
            clonedPanel.style.backdropFilter = 'none';
            clonedPanel.style.webkitBackdropFilter = 'none';
          }
          const clonedScroll = clonedDoc.querySelector('.payment-records-scroll');
          if (clonedScroll) {
            clonedScroll.style.maxHeight = 'none';
            clonedScroll.style.overflow = 'visible';
            clonedScroll.style.backdropFilter = 'none';
          }
        }
      });

      const filename = `payment_records_swimtrackpro`;

      if (format === 'png' || format === 'jpeg') {
        const mime = format === 'jpeg' ? 'image/jpeg' : 'image/png';
        const imgData = canvas.toDataURL(mime, 0.95);
        const link = document.createElement('a');
        link.download = `${filename}.${format}`;
        link.href = imgData;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        return;
      }

      if (format === 'pdf') {
        const JsPDFClass = (window.jspdf && window.jspdf.jsPDF) ? window.jspdf.jsPDF : window.jsPDF;
        if (JsPDFClass) {
          const imgData = canvas.toDataURL('image/png');
          const isLandscape = canvas.width > canvas.height;
          const pdf = new JsPDFClass({
            orientation: isLandscape ? 'landscape' : 'portrait',
            unit: 'px',
            format: [canvas.width, canvas.height]
          });
          pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height);
          pdf.save(`${filename}.pdf`);
          return;
        }
      }
    }

    // Fallback for PDF
    if (format === 'pdf') {
      window.print();
    } else {
      alert('Image capture library is still loading. Please choose CSV Spreadsheet or try again.');
    }
  } catch (err) {
    console.error('Error generating payment records download:', err);
    if (format === 'pdf') {
      window.print();
    } else {
      alert('Could not generate download. Please try again.');
    }
  } finally {
    if (downloadDropdown) downloadDropdown.style.display = originalDropdownDisplay;
    if (scrollWrapper) {
      scrollWrapper.style.maxHeight = originalMaxHeight;
      scrollWrapper.style.overflow = originalOverflow;
    }
  }
}

function downloadPaymentRecordsCSV() {
  const table = document.querySelector('#paymentRecordsPanel table');
  let rows = [];

  if (table) {
    const ths = table.querySelectorAll('thead th');
    rows.push(Array.from(ths).map(th => '"' + th.textContent.trim().replace(/"/g, '""') + '"').join(','));

    const trs = table.querySelectorAll('tbody tr');
    trs.forEach(tr => {
      if (tr.querySelector('td[colspan]')) return;
      const tds = tr.querySelectorAll('td');
      const rowData = Array.from(tds).map(td => {
        const select = td.querySelector('select');
        if (select) return '"' + select.value.replace(/"/g, '""') + '"';
        return '"' + td.textContent.trim().replace(/\s+/g, ' ').replace(/"/g, '""') + '"';
      });
      if (rowData.length > 0) rows.push(rowData.join(','));
    });
  }

  if (rows.length <= 1) {
    const bookings = window.bookingsData || [];
    if (bookings.length === 0) {
      alert('No payment records to download.');
      return;
    }
    rows = ['"S.No","Owner","Swimmer","Package","Status","Amount (INR)"'];
    bookings.forEach((b, index) => {
      const sNo = index + 1;
      const owner = (b.owner || b.created_by || '-').replace(/"/g, '""');
      const swimmer = (b.student || '-').replace(/"/g, '""');
      const pkg = (b.package || '-').replace(/"/g, '""');
      const status = (b.status || 'Not Paid').replace(/"/g, '""');
      const fee = Number(b.fee || 0);
      rows.push(`"${sNo}","${owner}","${swimmer}","${pkg}","${status}","${fee}"`);
    });
  }

  const blob = new Blob([rows.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'payment_records_swimtrackpro.csv';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Expose to window for global inline accessibility
window.downloadPaymentRecords = downloadPaymentRecords;
window.downloadPaymentRecordsCSV = downloadPaymentRecordsCSV;

// Auto-initialize calculation events on load
document.addEventListener('DOMContentLoaded', function () {
  initializePaymentCalculationsEvents();
});
