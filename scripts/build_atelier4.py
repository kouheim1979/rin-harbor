"""Compile inventory into the engine before startup; never decorate responses in a SW."""
from pathlib import Path
import re, hashlib
R=Path(__file__).resolve().parents[1]
RELEASE='20260908-atelier4'
SOURCE=R/'release-source'
def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('Unexpected source: '+old[:100])
    return text.replace(old,new,1)
game=(R/'game.js').read_text()
if RELEASE in game:raise SystemExit('Already built')
assert hashlib.sha1(b'blob '+str(len(game.encode())).encode()+b'\0'+game.encode()).hexdigest()=='2024dd6b437bde469faca4ecd16b5e5a489b40f8','Base engine changed; review before applying'
game=replace_once(game,"const RELEASE='20260907-sea2paint';",f"const RELEASE='{RELEASE}';")
game=replace_once(game,"    stats:{merges:0,delivered:0,generated:0,sold:0,bestLevel:1},","    warehouse:{},\n    stats:{merges:0,delivered:0,generated:0,sold:0,bestLevel:1},")
game=replace_once(game,"      return value;","      try{if(!localStorage.getItem('rin_harbor_before_warehouse_v4'))localStorage.setItem('rin_harbor_before_warehouse_v4',raw)}catch(_e){}\n      return value;")
game=replace_once(game,"  S.board.forEach(id=>{if(id)S.book[id]=1});","  S.warehouse=cleanWarehouse(src.warehouse);\n  [...S.board,...Object.keys(S.warehouse)].forEach(id=>{if(id)S.book[id]=1});")
game=replace_once(game,"['opening','home','game','orders','story','book']","['opening','home','game','orders','warehouse','story','book']")
game=replace_once(game,"hintPair.includes(i)?'hint':'']","hintPair.includes(i)?'hint':'',selected!==null&&i!==selected&&id&&id===S.board[selected]&&ITEMS[id].next?'matchable':'']")
game=replace_once(game,"  updateUndoButton();if(focused!==undefined)","  renderWarehouseLinks();updateUndoButton();if(focused!==undefined)")
game=replace_once(game,"if(view==='book')renderBook();saveSoon()}","if(view==='book')renderBook();if(view==='warehouse')renderWarehouse();renderWarehouseLinks();saveSoon()}")
game=replace_once(game,"    if(!confirm('現在の進行状況を、このバックアップで置き換えますか？'))return;","    cleanWarehouse(value.warehouse,true);\n    if(!confirm('現在の進行状況を、このバックアップで置き換えますか？'))return;")
game=replace_once(game,"  const claim=e.target.closest('[data-claim]');", "  const take=e.target.closest('[data-take]');if(take){takeFromWarehouse(take.dataset.take);return}\n  const filter=e.target.closest('[data-warehouse-filter]');if(filter){warehouseFilter=filter.dataset.warehouseFilter;renderWarehouse();return}\n  const claim=e.target.closest('[data-claim]');")
game=replace_once(game,"bind('hint',showHint);", "bind('openWarehouse',()=>setView('warehouse'));bind('store',storeSelected);bind('warehouseUndo',undo);\nbind('hint',showHint);")
game=replace_once(game,"try{load();setView('opening');",(SOURCE/'warehouse-core.js').read_text()+"\ntry{load();setView('opening');")
(R/'game.js').write_text(game)
html=(R/'index.html').read_text()
html=html.replace('sea2paint','atelier4').replace('2026.09.07 Sea Journal','2026.09.08 Atelier 4')
html=replace_once(html,'</head>','<!-- Replaces item-art-levels.js and warehouse.js. Features are integrated before startup. -->\n</head>')
icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m3 8 9-5 9 5v12H3ZM3 8h18M8 20v-8h8v8M8 16h8"/></svg>'
old=re.search(r'<button data-go="home" class="ghostBtn">.*?</button>',html).group(0)
html=replace_once(html,old,'<div class="gameHeadActions"><button id="autoGame" class="good" aria-label="自動納品の切り替え">自動 ON</button><button id="openWarehouse" aria-label="倉庫を開く">'+icon+'<b>倉庫</b><small data-warehouse-count>0/12</small></button></div>')
html=replace_once(html,'        <button id="autoGame" class="good">自動 ON</button>','        <button id="store" class="primary" disabled>預ける</button>')
html=replace_once(html,'  <section id="screenBook" class="screen">',(SOURCE/'warehouse.html').read_text()+'\n  <section id="screenBook" class="screen">')
card='<button class="menuCard" data-go="warehouse"><span class="menuIcon">'+icon+'</span><b>みなとの倉庫</b><span class="tiny"><span data-warehouse-count>0/12</span> 保管中</span></button>'
html=replace_once(html,'    <div class="homeGrid">','    <div class="homeGrid">'+card) if '    <div class="homeGrid">' in html else replace_once(html,'<div class="homeGrid">','<div class="homeGrid">'+card)
html=replace_once(html,'  <button data-go="story"><span class="navIcon">','  <button data-go="warehouse"><span class="navIcon">'+icon+'</span>倉庫</button>\n  <button data-go="story"><span class="navIcon">')
html=replace_once(html,'<h2>アイテム図鑑</h2>','<h2>アイテム図鑑</h2><p class="tiny">形とLvを見くらべよう。同じ種類・同じLvの2つが合成できます。</p>')
(R/'index.html').write_text(html)
css=(R/'youth.css').read_text()+'\n'+(SOURCE/'warehouse.css').read_text()
(R/'youth.css').write_text(css)
sw=(R/'sw.js').read_text()
start=sw.index("const CORE=")
end=sw.index('\n',start)
core=sw[start:end].replace('sea2paint','atelier4').replace(",'item-art-levels.js','warehouse.js'",'')
sw="'use strict';\nconst VERSION="+repr(RELEASE)+";\nconst PREFIX='rin-harbor-';\nconst CACHE=PREFIX+VERSION;\nconst ROOT=new URL('./',self.location.href);\nconst url=p=>new URL(p,ROOT).href;\n"+core+'''
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
'''
(R/'sw.js').write_text(sw)
for file in ['smoke.py','youth.py','origin_offline.py']:
 p=R/'tests'/file
 text=p.read_text().replace('20260907-sea2paint',RELEASE).replace('sea2paint','atelier4')
 p.write_text(text)
for name in ['warehouse.js','item-art-levels.js']:
 (R/name).write_text("/* Retired. Inventory and unique item shapes are built into game.js / item-art.js. */\n")
p=R/'tests/origin_offline.py'
s=p.read_text().replace('S.repair=5;saveNow()',"S.repair=5;S.warehouse={fish6:2};saveNow()")
s=s.replace("        check(label+'title art decoded',", "        check(label+'warehouse restored offline',page.evaluate('S.warehouse.fish6===2'))\n        check(label+'title art decoded',")
s=s.replace("closeAlbum();setView('game');S.coins=3456;saveNow()","closeAlbum();setView('warehouse');takeFromWarehouse('fish6');S.coins=3456;saveNow()")
s=s.replace("        check(label+'no JavaScript exceptions',", "        check(label+'warehouse withdrawal persists offline',page.evaluate('S.warehouse.fish6===1&&countBoard().fish6===1'))\n        check(label+'no JavaScript exceptions',")
p.write_text(s)
print('Built',RELEASE,'with static warehouse markup and normalized inventory.')
