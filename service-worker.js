const CACHE_NAME = 'cv-optimizer-v2';
const urlsToCache = [
    '/',
    '/static/css/custom.css',
    '/static/css/modern-premium.css',
    '/static/js/main.js'
];

self.addEventListener('install', function(event) {
    console.log('SW installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('SW caching files');
                return cache.addAll(urlsToCache);
            })
            .catch(function(error) {
                console.log('SW install failed:', error);
            })
    );
});

self.addEventListener('fetch', function(event) {
    // Only handle GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            })
            .catch(function(error) {
                console.log('SW fetch failed:', error);
                return fetch(event.request);
            })
    );
});

self.addEventListener('activate', function(event) {
    console.log('SW activated');
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheName !== CACHE_NAME) {
                        console.log('SW deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});