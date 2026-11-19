const toast = document.querySelector("#toast");
let toastTimer;
function notify(message) {
  toast.textContent = message;
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.hidden = true; }, 4000);
}

async function copy(value) {
  try {
    await navigator.clipboard.writeText(value);
    notify("Copied. Ready to pass along.");
  } catch {
    notify("Clipboard unavailable. Select the share URL or content and copy it manually.");
  }
}
document.querySelectorAll("[data-copy]").forEach(button => {
  button.addEventListener("click", () => copy(button.dataset.copy));
});
document.querySelector("#copy-content")?.addEventListener("click", () => {
  copy(document.querySelector("#resource-content").textContent);
});
document.querySelectorAll("[data-revoke]").forEach(form => {
  form.addEventListener("submit", event => {
    if (!window.confirm("Revoke this share? Its link and downloads will stop working immediately.")) {
      event.preventDefault();
    }
  });
});

const form = document.querySelector("#create-form");
if (form) {
  const content = document.querySelector("#content");
  const file = document.querySelector("#file");
  function updateType() {
    const kind = form.elements.kind.value;
    document.querySelector("#content-field").hidden = kind === "document";
    document.querySelector("#file-field").hidden = kind !== "document";
    document.querySelector("#language-field").hidden = kind !== "code";
    content.required = kind !== "document";
    content.disabled = kind === "document";
    file.required = kind === "document";
    file.disabled = kind !== "document";
    content.placeholder = kind === "link" ? "https://example.com/something-useful" : "Paste something worth passing along…";
  }
  form.querySelectorAll('[name="kind"]').forEach(radio => radio.addEventListener("change", updateType));
  updateType();
  form.addEventListener("submit", () => {
    form.querySelector('[type="submit"]').disabled = true;
    form.querySelector('[type="submit"]').textContent = "Creating share…";
  });
  document.querySelector("#form-error")?.focus();
}
