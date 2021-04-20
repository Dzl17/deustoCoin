var cacheName = 'DeustoCoin';
var filesToCache = [
  '/',
  './templates/index.html',
  '/css/main.css',
  '/css/sidebar.css',
  '/css/bootstrap-min.css',
  '/js/iconify.min.js',
  '/js/jquery-3.5.1.slim.min.js',
  '/js/popper.min.js',
  '/js/sidebar.js'
];

/* Start the service worker and cache all of the app's content */
self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(cacheName).then(function(cache) {
      return cache.addAll(filesToCache);
    })
  );
});

/* Serve cached content when offline */
self.addEventListener('fetch', function(e) {
  e.respondWith(
    caches.match(e.request).then(function(response) {
      return response || fetch(e.request);
    })
  );
});