// ទាញយកប្រព័ន្ធ Firebase សម្រាប់ Service Worker
importScripts('https://www.gstatic.com/firebasejs/10.8.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.8.1/firebase-messaging-compat.js');

// ភ្ជាប់ទៅកាន់ Firebase របស់បង
firebase.initializeApp({
    apiKey: "AIzaSyBX7ilsfHusMLi1gX3ZYcsdkuhST1p-y_k",
    authDomain: "my-telegram-bot-46df4.firebaseapp.com",
    projectId: "my-telegram-bot-46df4",
    storageBucket: "my-telegram-bot-46df4.firebasestorage.app",
    messagingSenderId: "507163040303",
    appId: "1:507163040303:web:6a45bef2be586caf3a04da"
});

const messaging = firebase.messaging();

// មុខងារចាំទទួលសារពេលបិទ App (Background)
messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] ទទួលបានសារលោត: ', payload);
    
    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: 'https://cdn-icons-png.flaticon.com/512/8767/8767355.png', // រូប Logo លោតលើសារ
        badge: 'https://cdn-icons-png.flaticon.com/512/8767/8767355.png'
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});

// មុខងារជួយឱ្យ App ដើរលឿន និងអាចប្រើពេលអត់សេវាបានខ្លះៗ (Cache)
self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open('stn-admin-v1').then((cache) => cache.addAll([
            './admin.html',
            './manifest.json'
        ]))
    );
});

self.addEventListener('fetch', (e) => {
    e.respondWith(
        caches.match(e.request).then((response) => response || fetch(e.request))
    );
});
