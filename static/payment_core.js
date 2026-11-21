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

  const totalReceivedEl = document.getElementById('calcTotalReceived');
  const totalPendingEl = document.getElementById('calcTotalPending');
  const grandTotalEl = document.getElementById('calcGrandTotal');
  const totalPending = pendingAmount + notPaidAmount;
  const grandTotal = paidAmount + totalPending;

  if (totalReceivedEl) totalReceivedEl.textContent = `₹${paidAmount.toLocaleString()}`;
  if (totalPendingEl) totalPendingEl.textContent = `₹${totalPending.toLocaleString()}`;
  if (grandTotalEl) grandTotalEl.textContent = `₹${grandTotal.toLocaleString()}`;
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
// Payment Calculations Section (Summary Totals)
// -------------------------------------------------------------
function updatePaymentCalculations() {
  updatePaymentSummary();
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

// Auto-initialize summary on load
document.addEventListener('DOMContentLoaded', function () {
  updatePaymentSummary();
});
