function startDrag(i,e){
  const id=S.board[i];if(!id)return;
  if(isGen(id)){generatorTap(i);return}
  drag={from:i,startX:e.clientX,startY:e.clientY,target:null,ghost:document.createElement('div')};
  drag.ghost.className='dragGhost';drag.ghost.textContent=emojiOf(id);document.body.appendChild(drag.ghost);
  moveGhost(e.clientX,e.clientY);markDrag();
}
function moveGhost(x,y){
  if(!drag)return;
  const size=window.innerWidth<=560?29:32;
  drag.ghost.style.transform=`translate(${x-size}px,${y-size}px)`;
}
function markDrag(){
  document.querySelectorAll('.cell').forEach(c=>c.classList.remove('dragSource','dropTarget'));
  if(!drag)return;
  document.querySelector(`.cell[data-i="${drag.from}"]`)?.classList.add('dragSource');
  if(drag.target!==null&&drag.target!==drag.from)document.querySelector(`.cell[data-i="${drag.target}"]`)?.classList.add('dropTarget');
}
function targetFromPoint(x,y){
  const el=document.elementFromPoint(x,y),cell=el?.closest?.('.cell');
  return cell?+cell.dataset.i:null;
}
function endDrag(e){
  if(!drag)return;
  const dx=e.clientX-drag.startX,dy=e.clientY-drag.startY,moved=Math.hypot(dx,dy)>10,target=targetFromPoint(e.clientX,e.clientY),from=drag.from;
  drag.ghost.remove();drag=null;document.querySelectorAll('.cell').forEach(c=>c.classList.remove('dragSource','dropTarget'));
  if(moved&&target!==null)moveOrMerge(from,target);else cellTap(from);
}

$('board').addEventListener('pointerdown',e=>{
  const b=e.target.closest('.cell');if(!b)return;e.preventDefault();
  try{$('board').setPointerCapture(e.pointerId)}catch(_e){}
  startDrag(+b.dataset.i,e);
},{passive:false});
$('board').addEventListener('pointermove',e=>{
  if(!drag)return;e.preventDefault();drag.target=targetFromPoint(e.clientX,e.clientY);moveGhost(e.clientX,e.clientY);markDrag();
},{passive:false});
$('board').addEventListener('pointerup',e=>{if(!drag)return;e.preventDefault();endDrag(e)},{passive:false});
$('board').addEventListener('pointercancel',()=>{if(!drag)return;drag.ghost.remove();drag=null;renderGame()},{passive:false});

document.body.addEventListener('click',e=>{
  const go=e.target.closest('[data-go]');if(go){setView(go.dataset.go);return}
  const claim=e.target.closest('[data-claim]');if(claim){claimMission(+claim.dataset.claim);return}
  const order=e.target.closest('[data-order]');if(order){completeOrder(+order.dataset.order,false);renderAll();saveSoon();return}
  const story=e.target.closest('[data-story]');if(story){openStory(+story.dataset.story);return}
  const album=e.target.closest('[data-album]');if(album){openAlbum(+album.dataset.album);return}
  const viewStage=e.target.closest('[data-view-stage]');if(viewStage){openAlbum(+viewStage.dataset.viewStage);return}
});

$('startHome').addEventListener('click',()=>setView('home'));
$('startGame').addEventListener('click',()=>setView('game'));
$('quickTop').addEventListener('click',quickDeliver);
$('quickOrders').addEventListener('click',()=>{const n=S.orders.filter(orderCan).length;n?toast(`🚢 今 ${n}件 納品できます`):toast('まだ完成した注文はないよ')});
$('autoGame').addEventListener('click',()=>{S.auto=!S.auto;if(S.auto)autoDeliver();renderAll();saveSoon()});
$('hint').addEventListener('click',showHint);
$('undo').addEventListener('click',undo);
$('sort').addEventListener('click',sortBoard);
$('sell').addEventListener('click',sellSelected);
$('clear').addEventListener('click',()=>{selected=null;hintPair=[];renderGame();say('選択解除。')});
$('repairBtn').addEventListener('click',repairShip);
$('openAlbum').addEventListener('click',()=>openAlbum(0));
$('viewerClose').addEventListener('click',()=>$('viewer').classList.remove('on'));
$('viewer').addEventListener('click',e=>{if(e.target===$('viewer'))$('viewer').classList.remove('on')});
$('autoSetting').addEventListener('click',()=>{S.auto=!S.auto;if(S.auto)autoDeliver();renderAll();saveSoon()});
$('autoStorySetting').addEventListener('click',()=>{S.autoStory=!S.autoStory;if(S.autoStory)autoOpenStory();renderAll();saveSoon()});
$('soundSetting').addEventListener('click',()=>{S.sound=!S.sound;if(S.sound)sound('reward');renderBook();saveSoon()});
$('hapticSetting').addEventListener('click',()=>{S.haptics=!S.haptics;if(S.haptics)haptic(20);renderBook();saveSoon()});
$('exportSave').addEventListener('click',exportSave);
$('importSave').addEventListener('click',importSave);
$('reset').addEventListener('click',resetGame);
$('openingImage').addEventListener('load',()=>$('openingFallback').style.display='none');
$('openingImage').addEventListener('error',()=>{$('openingImage').style.display='none';$('openingFallback').style.display='flex'});

window.addEventListener('pagehide',saveNow);
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')saveNow()});

load();
renderAll();

if('serviceWorker' in navigator){
  window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(()=>{}));
}
