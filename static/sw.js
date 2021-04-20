var cacheName = 'DeustoCoin';
var filesToCache = [
  './static/templates/accion.html',
  './static/templates/accionalumnos.html',
  './static/templates/adminacciones.html',
  './static/templates/admincampanyas.html',
  './static/templates/adminofertas.html',
  './static/templates/base.html',
  './static/templates/campanyas.html',
  './static/templates/editoraccion.html',
  './static/templates/editorcamp.html',
  './static/templates/editoroferta.html',
  './static/templates/empresas.html',
  './static/templates/error.html',
  './static/templates/historialtrans.html',
  './static/templates/index.html',
  './static/templates/ofertas.html',
  './static/templates/pago.html',
  './static/templates/recompensa.html',
  './static/templates/register.html',
  './static/templates/sobre.html',
  './static/templates/subirimagen.html',
  './static/templates/tab1cartera.html',
  './static/css/main.css',
  './static/css/floating-labels.css',
  './static/css/sidebar.css',
  './static/js/sidebar.js'
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