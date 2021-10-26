var cacheName = 'DeustoCoin';
var filesToCache = [
  './static/css/main.css',
  './static/css/floating-labels.css',
  './static/css/sidebar.css',
  './static/js/sidebar.js',
  './static/css/style.css'
];

self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(cacheName).then(function(cache) {
      return cache.addAll(filesToCache);
    })
  );
});

self.addEventListener('fetch', function(e) {
  e.respondWith(
    caches.match(e.request).then(function(response) {
      return response || fetch(e.request);
    })
  );
});