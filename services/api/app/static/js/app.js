if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {});
  });
}

document.addEventListener("submit", (event) => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement)) {
    return;
  }
  const button = form.querySelector("[data-submit-once]");
  if (button instanceof HTMLButtonElement) {
    button.disabled = true;
    button.dataset.originalText = button.textContent || "";
    button.textContent = "Saving...";
  }
});

