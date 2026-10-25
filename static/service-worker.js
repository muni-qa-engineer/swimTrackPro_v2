const CACHE_NAME = 'swimtrackpro-cache-v3';
const ASSETS_TO_CACHE = [
  '/',
  '/static/css/global.css',
  '/static/css/animations.css',
  '/static/css/dashboard.css',
  '/static/common.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css'
];

// Install Event - Cache App Shell Assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Caching App Shell');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate Event - Clean Up Old Caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[Service Worker] Removing old cache', key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch Event - Network First Strategy for API / HTML, Cache First for Static Assets
self.addEventListener('fetch', (event) => {
  // Only intercept GET requests
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // If it's a static asset (CSS, JS, Image), try Cache First, then Network
  if (url.pathname.startsWith('/static/') || url.hostname === 'cdn.jsdelivr.net' || url.hostname === 'cdnjs.cloudflare.com' || url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(event.request).then((networkResponse) => {
          return caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          });
        });
      })
    );
  } else {
    // For HTML pages and APIs, try Network First, fallback to Cache
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return caches.match(event.request);
        })
    );
  }
});

// --- PWA Push & Session Completion Action Handlers ---
self.addEventListener('push', (event) => {
  let data = { title: 'SwimTrackPro Alert', body: 'New session update available.' };
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { title: 'SwimTrackPro Alert', body: event.data.text() };
    }
  }

  const options = {
    body: data.body,
    icon: data.icon || '/static/icons/icon-192.png',
    badge: data.badge || '/static/icons/icon-192.png',
    tag: data.tag || 'swimtrackpro-notice',
    data: data.data || {},
    actions: data.actions || [
      { action: 'completed', title: '✅ Yes (Completed)' },
      { action: 'missed', title: '❌ No (Make-up Credit)' }
    ],
    vibrate: [200, 100, 200]
  };

  event.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const action = event.action;
  const notifData = event.notification.data || {};
  const bookingId = notifData.booking_id;
  const sessionDate = notifData.session_date;

  if ((action === 'completed' || action === 'missed') && bookingId && sessionDate) {
    event.waitUntil(
      fetch('/api/coach/confirm_session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          booking_id: bookingId,
          session_date: sessionDate,
          status: action
        })
      })
      .then(() => clients.matchAll({ type: 'window', includeUncontrolled: true }))
      .then((clientList) => {
        for (const client of clientList) {
          if ('focus' in client) {
            client.postMessage({ type: 'SESSION_CONFIRMED', booking_id: bookingId, status: action });
            return client.focus();
          }
        }
        if (clients.openWindow) return clients.openWindow('/');
      })
      .catch((err) => console.error('Error handling notification action:', err))
    );
  } else {
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
        for (const client of clientList) {
          if ('focus' in client) return client.focus();
        }
        if (clients.openWindow) return clients.openWindow('/');
      })
    );
  }
});
