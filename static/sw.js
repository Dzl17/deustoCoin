var cacheName = 'DeustoCoin';
var filesToCache = [
  '/',
  './templates/accion.html',
  './templates/accionalumnos.html',
  './templates/adminacciones.html',
  './templates/admincampanyas.html',
  './templates/adminofertas.html',
  './templates/base.html',
  './templates/campanyas.html',
  './templates/editoraccion.html',
  './templates/editorcamp.html',
  './templates/editoroferta.html',
  './templates/empresas.html',
  './templates/error.html',
  './templates/historialtrans.html',
  './templates/index.html',
  './templates/ofertas.html',
  './templates/pago.html',
  './templates/recompensa.html',
  './templates/register.html',
  './templates/sobre.html',
  './templates/subirimagen.html',
  './templates/tab1cartera.html',
  '/css/main.css',
  '/css/floating-labels.css',
  '/css/sidebar.css',
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