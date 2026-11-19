// The identity selector submits immediately; its button remains a no-JS fallback.
document.querySelectorAll('[data-member-switch]').forEach((select) => {
  select.addEventListener('change', () => select.form.requestSubmit());
});

// Prevent accidental repeated submissions while retaining native form validation.
document.querySelectorAll('form').forEach((form) => {
  form.addEventListener('submit', () => {
    form.querySelectorAll('button[type="submit"]').forEach((button) => {
      button.dataset.submitting = 'true';
      button.disabled = true;
    });
  });
});
window.addEventListener('pageshow', () => {
  document.querySelectorAll('button[data-submitting]').forEach((button) => {
    button.disabled = false;
    delete button.dataset.submitting;
  });
});

// Date fields are the no-JS path; calendar clicks offer the same range selection.
const reservation = document.querySelector('[data-reservation-form]');
if (reservation) {
  const first = reservation.querySelector('[name="start_date"]');
  const last = reservation.querySelector('[name="expected_return"]');
  const feedback = document.querySelector('[data-calendar-selection]');
  let selectingEnd = Boolean(first.value && (!last.value || last.value === first.value));
  const days = [...document.querySelectorAll('[data-calendar-date]')];
  const paint = () => {
    days.forEach(day => {
      const selected = first.value && last.value && day.dataset.calendarDate >= first.value && day.dataset.calendarDate <= last.value;
      day.classList.toggle('selected-date', Boolean(selected));
    });
    last.min = first.value || first.min;
  };
  days.forEach(day => day.addEventListener('click', () => {
    const value = day.dataset.calendarDate;
    if (!selectingEnd || value < first.value) {
      first.value = value;
      last.value = value;
      selectingEnd = true;
      feedback.textContent = 'Start selected. Choose the last day, or use the date fields.';
    } else {
      const crossesUnavailable = days.some(cell => cell.dataset.calendarDate >= first.value && cell.dataset.calendarDate <= value && cell.dataset.calendarState !== 'available');
      if (crossesUnavailable) {
        feedback.textContent = 'This range crosses unavailable dates. Choose a shorter period.';
        return;
      }
      last.value = value;
      selectingEnd = false;
      feedback.textContent = `Selected ${first.value} through ${last.value}, inclusive.`;
    }
    paint();
  }));
  [first, last].forEach(input => input.addEventListener('change', () => {
    if (first.value && last.value && last.value < first.value) last.value = first.value;
    paint();
  }));
  document.querySelectorAll('.calendar-heading nav a').forEach(link => {
    link.addEventListener('click', () => {
      const url = new URL(link.href);
      if (first.value) url.searchParams.set('start_date', first.value);
      if (last.value) url.searchParams.set('expected_return', last.value);
      link.href = url.toString();
    });
  });
  paint();
}
