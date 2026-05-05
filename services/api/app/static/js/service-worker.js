const CACHE_NAME = "alpr-stms-shell-v3";
const OFFLINE_URL = "/static/offline.html";
const SHELL_FILES = [
  "/static/css/app.css",
  "/static/js/app.js",
  "/static/js/violation-form.js",
  "/manifest.webmanifest",
  "/static/images/icon.svg",
  "/static/images/icon-180.png",
  "/static/images/icon-192.png",
  "/static/images/icon-512.png",
  OFFLINE_URL,
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_FILES)));
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }
  const request = event.request;
  if (request.mode === "navigate" || (request.headers.get("accept") || "").includes("text/html")) {
    event.respondWith(fetch(request).catch(() => caches.match(OFFLINE_URL)));
    return;
  }
  event.respondWith(caches.match(request).then((cached) => cached || fetch(request)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))),
  );
});

