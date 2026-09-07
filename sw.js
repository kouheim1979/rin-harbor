'use strict';
// Versioned app shell + artwork. Only this game's caches and URLs are touched.
const VERSION='20260907-sea3warehouse';
const PREFIX='rin-harbor-';
const CACHE=PREFIX+VERSION;
const ROOT=new URL('./',self.location.href);
const url=path=>new URL(path,ROOT).href;
const CORE=['index.html','youth.css?v=sea2paint','item-art.js?v=sea2paint','game.js?v=sea2paint','item-art-levels.js','warehouse.js','manifest.webmanifest','assets/art-hd/hero.webp',...Array.from({length:6},(_,i)=>`assets/art-hd/repair-${i}.webp`),...Array.from({length:6},(_,i)=>`assets/art-hd/thumb-${i}.webp`),'assets/art-v1/icon-180.png','assets/art-v1/icon-192.png','assets/art-v1/icon-512.png'];
const decorate=async response=>{
  if(!response)return response;
  const type=response.headers.get('content-type')||'';
  if(!type.includes('text/html'))return response;
  let html=await response.text();
  if(!html.includes('item-art-levels.js'))html=html.replace('</body>','<script src="./item-art-levels.js?v=sea3warehouse"></script><script src="./warehouse.js?v=sea3warehouse"></script></body>');
  const headers=new Headers(response.headers);headers.set('content-type','text/html; charset=utf-8');
  return new Response(html,{status:response.status,statusText:response.statusText,headers});
};
self.addEventListener('install',event=>{
  event.waitUntil((async()=>{const cache=await caches.open(CACHE);await cache.addAll(CORE.map(path=>new Request(url(path),{cache:'reload'})));await self.skipWaiting()})());
});
self.addEventListener('activate',event=>{
  event.waitUntil((async()=>{for(const name of await caches.keys())if(name.startsWith(PREFIX)&&name!==CACHE)await caches.delete(name);await self.clients.claim()})());
});
self.addEventListener('message',event=>{if(event.data?.type==='READY')event.ports[0]?.postMessage({version:VERSION})});
self.addEventListener('fetch',event=>{
  const request=event.request,requested=new URL(request.url);
  if(request.method!=='GET'||requested.origin!==ROOT.origin||!requested.pathname.startsWith(ROOT.pathname))return;
  if(request.mode==='navigate'){
    event.respondWith((async()=>{
      const cache=await caches.open(CACHE),controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),3500);
      try{
        const response=await fetch(request,{signal:controller.signal,cache:'no-cache'});
        if(response.ok&&response.headers.get('content-type')?.includes('text/html')){
          if(requested.pathname===ROOT.pathname||requested.pathname===new URL('index.html',ROOT).pathname)await cache.put(url('index.html'),response.clone());
          return await decorate(response);
        }
        const fallback=await cache.match(url('index.html'));return fallback?await decorate(fallback):response;
      }catch(_e){const fallback=await cache.match(url('index.html'));return fallback?await decorate(fallback):Response.error()}
      finally{clearTimeout(timeout)}
    })());return;
  }
  event.respondWith((async()=>{const cache=await caches.open(CACHE),hit=await cache.match(request);if(hit)return hit;try{const response=await fetch(request);if(response.ok&&response.type==='basic')await cache.put(request,response.clone());return response}catch(_e){return Response.error()}})());
});
