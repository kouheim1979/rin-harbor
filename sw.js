'use strict';
const VERSION='20260908-atelier4';
const PREFIX='rin-harbor-';
const CACHE=PREFIX+VERSION;
const ROOT=new URL('./',self.location.href);
const url=p=>new URL(p,ROOT).href;
const CORE=['index.html','youth.css?v=atelier4','item-art.js?v=atelier4','game.js?v=atelier4','manifest.webmanifest','assets/art-hd/hero.webp',...Array.from({length:6},(_,i)=>`assets/art-hd/repair-${i}.webp`),...Array.from({length:6},(_,i)=>`assets/art-hd/thumb-${i}.webp`),'assets/art-v1/icon-180.png','assets/art-v1/icon-192.png','assets/art-v1/icon-512.png'];
self.addEventListener('install',e=>e.waitUntil((async()=>{const c=await caches.open(CACHE);await c.addAll(CORE.map(p=>new Request(url(p),{cache:'reload'})));await self.skipWaiting()})()));
self.addEventListener('activate',e=>e.waitUntil((async()=>{for(const n of await caches.keys())if(n.startsWith(PREFIX)&&n!==CACHE)await caches.delete(n);await self.clients.claim()})()));
self.addEventListener('message',e=>{if(e.data?.type==='READY')e.ports[0]?.postMessage({version:VERSION})});
self.addEventListener('fetch',e=>{
 const q=e.request,u=new URL(q.url);
 if(q.method!=='GET'||u.origin!==ROOT.origin||!u.pathname.startsWith(ROOT.pathname))return;
 e.respondWith((async()=>{
  const c=await caches.open(CACHE);
  if(q.mode==='navigate'){
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),3500);
   try{const r=await fetch(q,{cache:'no-cache',signal:controller.signal});if(r.ok&&r.headers.get('content-type')?.includes('text/html')){if(u.pathname===ROOT.pathname||u.pathname===new URL('index.html',ROOT).pathname)await c.put(url('index.html'),r.clone());return r}return await c.match(url('index.html'))||r}
   catch(_e){return await c.match(url('index.html'))||Response.error()}finally{clearTimeout(timer)}
  }
  const hit=await c.match(q);if(hit)return hit;
  try{const r=await fetch(q);if(r.ok&&r.type==='basic')await c.put(q,r.clone());return r}catch(_e){return Response.error()}
 })());
});
