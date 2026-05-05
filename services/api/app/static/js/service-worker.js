const CACHE_NAME = "alpr-stms-shell-v5";
const OFFLINE_URL = "/static/offline.html";
const SHELL_FILES = [
  "/static/css/app.css",
  "/static/js/app.js",
  "/static/js/violation-form.js",
  "/static/js/pwa-install.js",
  "/manifest.webmanifest",
  "/static/images/icon.svg",
  "/static/images/icon-192.png",
  "/static/images/icon-512.png",
  "/static/vendor/bootstrap/bootstrap.min.css",
  "/static/vendor/bootstrap/bootstrap.bundle.min.js",
  "/static/vendor/leaflet/leaflet.css",
  "/static/vendor/leaflet/leaflet.js",
  OFFLINE_URL,
];

/* Install — pre-cache app shell */
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(SHELL_FILES))
      .catch((err) => {
        console.error("[SW] Pre-cache failed:", err);
      }),
  );
  self.skipWaiting();
});

/* Activate — clean old caches */
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)),
        ),
      )
      .catch((err) => {
        console.error("[SW] Cache cleanup failed:", err);
      }),
  );
  self.clients.claim();
});

/* Fetch — strategy dispatcher */
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  const request = event.request;
  const url = new URL(request.url);

  /* Navigation (HTML pages) — network-first, offline fallback via .catch() */
  if (request.mode === "navigate" || (request.headers.get("accept") || "").includes("text/html")) {
    event.respondWith(
      fetch(request)
        .then((response) => response)
        .catch(() => {
          console.log("[SW] Navigation failed, serving offline page");
          return caches.match(OFFLINE_URL);
        }),
    );
    return;
  }

  /* API / JSON requests — network-only with .catch() error fallback */
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/health/")) {
    event.respondWith(
      fetch(request).catch(() => {
        console.log("[SW] API request failed:", url.pathname);
        return new Response(
          JSON.stringify({ error: "offline", detail: "You are currently offline" }),
          { status: 503, headers: { "Content-Type": "application/json" } },
        );
      }),
    );
    return;
  }

  /* Static assets — stale-while-revalidate with .catch() fallback */
  event.respondWith(
    caches
      .match(request)
      .then((cached) => {
        const networkFetch = fetch(request)
          .then((response) => {
            if (response.ok && url.pathname.startsWith("/static/")) {
              const clone = response.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
            }
            return response;
          })
          .catch(() => {
            console.log("[SW] Static asset unavailable offline:", url.pathname);
            if (cached) {
              return cached;
            }
            return new Response("", { status: 408 });
          });
        return cached || networkFetch;
      }),
  );
});
