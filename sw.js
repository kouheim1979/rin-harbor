'use strict';
const CACHE='rin-harbor-premium-v3-art';
const CORE=[
  './','./index.html','./base.css','./premium.css',
  './game-data.js','./game-engine-a.js','./game-engine-b.js','./game-engine-c.js',
  './manifest.webmanifest','./apple-touch-icon.png',
  './assets/icon.png','./assets/icon-192.png','./assets/icon-512.png',
  './assets/hero-opening.webp','./assets/repair-stage-0.jpg',
  './assets/repair-stage-1.webp','./assets/repair-stage-2.webp','./assets/repair-stage-3.webp',
  './assets/repair-stage-4.webp','./assets/repair-stage-5.webp'
];
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(async cache=>{
    await Promise.all(CORE.map(async url=>{
      try{const response=await fetch(url,{cache:'reload'});if(response&&response.ok)await cache.put(url,response)}catch(_e){}
    }));
  }).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET')return;
  const url=new URL(event.request.url);
  if(url.origin!==self.location.origin)return;
  const fresh=event.request.mode==='navigate'||event.request.destination==='document'||event.request.destination==='image';
  if(fresh){
    event.respondWith(fetch(new Request(event.request,{cache:'reload'})).then(response=>{
      if(response&&response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy))}
      return response;
    }).catch(()=>caches.match(event.request).then(hit=>hit||caches.match('./index.html'))));
    return;
  }
  event.respondWith(caches.match(event.request).then(hit=>hit||fetch(event.request).then(response=>{
    if(response&&response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy))}
    return response;
  })));
});
