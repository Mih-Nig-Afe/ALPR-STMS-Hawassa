const CACHE_NAME = "alpr-stms-shell-v2";
const SHELL_FILES = [
  "/static/css/app.css",
  "/static/js/app.js",
  "/static/js/violation-form.js",
  "/manifest.webmanifest",
  "/static/images/icon.svg",
  "/static/images/icon-180.png",
  "/static/images/icon-192.png",
  "/static/images/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_FILES)));
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(event.request);
    }),
  );
});

