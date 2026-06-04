// Self-destructing service worker.
// On activation: delete ALL caches and unregister itself.
// This guarantees the browser will fetch fresh files from the server.

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.map(k => caches.delete(k))))
      .then(() => self.registration.unregister())
      .then(() => self.clients.matchAll())
      .then(clients => clients.forEach(c => c.navigate(c.url)))
  );
});

// Pass everything straight to network — no caching at all
self.addEventListener('fetch', () => {});
