'use strict';
const VERSION='20260908-video1';
const PREFIX='rin-harbor-';
const CACHE=PREFIX+VERSION;
const ROOT=new URL('./',self.location.href);
const url=p=>new URL(p,ROOT).href;
const CORE=['index.html','youth.css?v=video1','item-art.js?v=video1','game.js?v=video1','manifest.webmanifest','assets/art-hd/hero.webp',...Array.from({length:6},(_,i)=>`assets/art-hd/repair-${i}.webp`),...Array.from({length:6},(_,i)=>`assets/art-hd/thumb-${i}.webp`),'assets/art-v1/icon-180.png','assets/art-v1/icon-192.png','assets/art-v1/icon-512.png','assets/video/title-loop.mp4',...Array.from({length:5},(_,i)=>`assets/video/repair-${i+1}.mp4`)];

async function cachedRangeResponse(cache,request){
 const range=request.headers.get('range');
 if(!range)return null;
 const full=await cache.match(request.url);
 if(!full)return null;
 const buffer=await full.arrayBuffer(),size=buffer.byteLength;
 const match=/^bytes=(\d*)-(\d*)$/i.exec(range.trim());
 if(!match)return null;
 let start,end;
 if(match[1]){
  start=Number(match[1]);
  end=match[2]?Number(match[2]):size-1;
 }else if(match[2]){
  const suffix=Number(match[2]);
  start=Math.max(0,size-suffix);end=size-1;
 }else return null;
 if(!Number.isFinite(start)||!Number.isFinite(end)||start<0||start>=size||end<start){
  return new Response(null,{status:416,headers:{'Content-Range':`bytes */${size}`,'Accept-Ranges':'bytes'}});
 }
 end=Math.min(end,size-1);
 const headers=new Headers(full.headers);
 headers.set('Content-Range',`bytes ${start}-${end}/${size}`);
 headers.set('Accept-Ranges','bytes');
 headers.set('Content-Length',String(end-start+1));
 return new Response(buffer.slice(start,end+1),{status:206,statusText:'Partial Content',headers});
}

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
  // HTMLMediaElement asks MP4 files for byte ranges. Returning a cached full 200
  // response to that request breaks playback once this service worker controls
  // the page. Slice the cached file and answer with a standards-compliant 206.
  if(q.headers.has('range')&&u.pathname.toLowerCase().endsWith('.mp4')){
   const partial=await cachedRangeResponse(c,q);if(partial)return partial;
   try{return await fetch(q)}catch(_e){return Response.error()}
  }
  const hit=await c.match(q);if(hit)return hit;
  try{const r=await fetch(q);if(r.ok&&r.type==='basic')await c.put(q,r.clone());return r}catch(_e){return Response.error()}
 })());
});
