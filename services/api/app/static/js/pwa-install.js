let deferredPrompt = null;
let installBanner = null;

const logEvidence = (event, details = {}) => {
  console.info(`[PWA] ${event}`, details);
};

const hideInstallBanner = () => {
  if (installBanner) {
    installBanner.remove();
    installBanner = null;
  }
};

const showInstallBanner = () => {
  if (installBanner) {
    return;
  }
  const host = document.querySelector("#main-content") || document.body;
  const banner = document.createElement("div");
  banner.className = "alert alert-info d-flex justify-content-between align-items-center gap-2 mb-3";
  banner.setAttribute("role", "status");
  banner.innerHTML = `
    <span>Install ALPR STMS for faster field access.</span>
    <span class="d-flex gap-2">
      <button type="button" class="btn btn-sm btn-primary" data-pwa-install>Install</button>
      <button type="button" class="btn btn-sm btn-outline-secondary" data-pwa-dismiss>Later</button>
    </span>
  `;
  host.prepend(banner);
  installBanner = banner;

  const installBtn = banner.querySelector("[data-pwa-install]");
  const dismissBtn = banner.querySelector("[data-pwa-dismiss]");
  if (installBtn instanceof HTMLButtonElement) {
    installBtn.addEventListener("click", async () => {
      if (!deferredPrompt) {
        logEvidence("install-click-without-prompt");
        return;
      }
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      logEvidence("install-choice", { outcome });
      deferredPrompt = null;
      hideInstallBanner();
    });
  }
  if (dismissBtn instanceof HTMLButtonElement) {
    dismissBtn.addEventListener("click", () => {
      logEvidence("install-banner-dismissed");
      hideInstallBanner();
    });
  }
};

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredPrompt = event;
  logEvidence("beforeinstallprompt-captured");
  showInstallBanner();
});

window.addEventListener("appinstalled", () => {
  logEvidence("appinstalled");
  deferredPrompt = null;
  hideInstallBanner();
});
