import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/static/booking.js"
with open(file_path, "r") as f:
    content = f.read()

# 1. End Date readonly
end_date_target = "endDateInput.value = formatDate(autoEndDate);"
end_date_replacement = """endDateInput.value = formatDate(autoEndDate);
        
        if (['3_months', '6_months', '9_months', '12_months'].includes(pkg.value)) {
            endDateInput.readOnly = true;
            endDateInput.style.pointerEvents = 'none';
        } else {
            endDateInput.readOnly = false;
            endDateInput.style.pointerEvents = 'auto';
        }"""
content = content.replace(end_date_target, end_date_replacement, 1)

# 2. Alert message change
content = content.replace(
    "alert('Monthly package allows maximum 3 class days');",
    "alert('Maximum 3 class days allowed');"
)

# 3. selected.length === 1 replacement
len_1_target = """    if (['Monthly', '3_months', '6_months', '9_months', '12_months'].includes(pkg.value) && selected.length === 1) {
      feeInput.value = '';
      feeInput.placeholder = 'Select 2 or 3 class days';
      return;
    }"""
len_1_replacement = """    if (['Monthly', '3_months', '6_months', '9_months', '12_months'].includes(pkg.value) && selected.length === 1) {
      feeInput.value = '';
      feeInput.placeholder = pkg.value === 'Monthly' ? 'Select 2 or 3 class days' : 'Select exactly 3 class days';
      return;
    }
    if (['3_months', '6_months', '9_months', '12_months'].includes(pkg.value) && selected.length === 2) {
      feeInput.value = '';
      feeInput.placeholder = 'Select exactly 3 class days';
      return;
    }"""
content = content.replace(len_1_target, len_1_replacement)

# 4. Fee logic replacement
fee_target = """    else if (['Monthly', '3_months', '6_months', '9_months', '12_months'].includes(pkg.value)) {
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
    }"""
fee_replacement = """    else if (['Monthly', '3_months', '6_months', '9_months', '12_months'].includes(pkg.value)) {
      if (pkg.value === 'Monthly') {
          if (selected.length < 2 || selected.length > 3) {
            feeInput.value = '';
            feeInput.placeholder = 'Select 2 or 3 class days';
            return;
          }
          if (selected.length === 2) {
            actualAmount = 6000 * persons;
          } else {
            actualAmount = 9000 * persons;
          }
      } else {
          if (selected.length !== 3) {
            feeInput.value = '';
            feeInput.placeholder = 'Select exactly 3 class days';
            return;
          }
          const isGroup = persons > 1;
          const category = isGroup ? 'group' : 'individual';
          const pricingData = window.LONG_TERM_PACKAGES && window.LONG_TERM_PACKAGES[category] && window.LONG_TERM_PACKAGES[category][pkg.value];
          if (pricingData) {
              actualAmount = Math.round((pricingData.final_price * persons * 100) / (100 - discountPercent));
          } else {
              actualAmount = 0;
          }
      }
    }"""
content = content.replace(fee_target, fee_replacement)

# 5. Form submission logic
submit_target = """    if (pkg && ['Monthly', '3_months', '6_months', '9_months', '12_months'].includes(pkg.value)) {
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
    }"""
submit_replacement = """    if (pkg && ['Monthly', '3_months', '6_months', '9_months', '12_months'].includes(pkg.value)) {
      const selectedCount = document.querySelectorAll('.class-day:checked').length;

      if (pkg.value === 'Monthly' && (selectedCount < 2 || selectedCount > 3)) {
        event.preventDefault();
        createToast('Monthly package requires selecting 2 or 3 class days.', 'danger', 3000);
        return;
      } else if (pkg.value !== 'Monthly' && selectedCount !== 3) {
        event.preventDefault();
        createToast('Long term packages require selecting exactly 3 class days.', 'danger', 3000);
        return;
      }
    }"""
content = content.replace(submit_target, submit_replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Updated booking.js successfully.")
