// The identity selector submits immediately; its button remains a no-JS fallback.
document.querySelectorAll('[data-member-switch]').forEach((select) => {
  select.addEventListener('change', () => select.form.requestSubmit());
});

// Prevent accidental repeated submissions while retaining native form validation.
document.querySelectorAll('form').forEach((form) => {
  form.addEventListener('submit', () => {
    form.querySelectorAll('button[type="submit"]').forEach((button) => {
      button.disabled = true;
    });
  });
});
window.addEventListener('pageshow', () => {
  document.querySelectorAll('button[disabled]').forEach((button) => {
    button.disabled = false;
  });
});
