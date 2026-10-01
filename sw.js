self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const shelfId = event.notification.data && event.notification.data.shelfId;
  event.waitUntil((async () => {
    const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    const client = all[0];
    if (client) {
      await client.focus();
      if (shelfId) client.postMessage({ shelfId });
    } else {
      await self.clients.openWindow('./');
    }
  })());
});
