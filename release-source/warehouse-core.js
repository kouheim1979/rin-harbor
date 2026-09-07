/* Integrated before load(): inventory is normalized before the first autosave. */
function cleanWarehouse(raw, strict=false){
  if(raw===undefined)return {};
  if(!raw||typeof raw!=='object'||Array.isArray(raw)){
    if(strict)throw new Error('Invalid warehouse');
    return {};
  }
  const result={};
  for(const [id,n] of Object.entries(raw)){
    if(!hasItem(id)||isGen(id)||!Number.isSafeInteger(n)||n<0){
      if(strict)throw new Error('Invalid warehouse item');
      continue;
    }
    if(n>0)result[id]=n;
  }
  return result;
}
function warehouseUsed(){return Object.values(S.warehouse).reduce((n,x)=>n+x,0)}
function warehouseCapacity(){return 12+S.repair*4+Math.floor(Math.max(0,S.level-1)/3)*2}
function warehouseEntries(){
  const kinds=Object.keys(CHAIN_DATA);
  return Object.entries(S.warehouse).sort(([a],[b])=>kinds.indexOf(ITEMS[a].k)-kinds.indexOf(ITEMS[b].k)||levelOf(a)-levelOf(b));
}
let warehouseFilter='all';
function storeSelected(){
  const id=selected===null?null:S.board[selected];
  if(!hasItem(id)||isGen(id)){say('預けるアイテムを盤面で選んでね。屋台は預けられません。');return false}
  if(warehouseUsed()>=warehouseCapacity()){toast('倉庫が満杯です。取り出してから預けてね。');return false}
  makeUndo('倉庫へ預ける');
  S.board[selected]=null;S.warehouse[id]=(S.warehouse[id]||0)+1;
  selected=null;hintPair=[];cancelDrag();
  renderAll();saveNow();sound('pop');say(`${nameOf(id)}（Lv${levelOf(id)}）を倉庫に預けたよ。`);
  toast('倉庫に預けました');return true;
}
function takeFromWarehouse(id){
  if(!hasItem(id)||isGen(id)||!S.warehouse[id])return false;
  const pos=S.board.indexOf(null);
  if(pos<0){toast('盤面がいっぱいです。先に合成するか、別のアイテムを預けてね。');return false}
  makeUndo('倉庫から取り出す');
  S.board[pos]=id;S.book[id]=1;S.warehouse[id]--;
  if(S.warehouse[id]===0)delete S.warehouse[id];
  selected=null;hintPair=[];
  // Never auto-deliver a freshly withdrawn item. The player controls its next use.
  renderAll();saveNow();sound('pop');toast(`${nameOf(id)}を盤面に戻しました`);return true;
}
function renderWarehouseLinks(){
  const count=`${warehouseUsed()}/${warehouseCapacity()}`;
  document.querySelectorAll('[data-warehouse-count]').forEach(el=>el.textContent=count);
  const store=$('store');
  if(store)store.disabled=selected===null||!S.board[selected]||isGen(S.board[selected])||warehouseUsed()>=warehouseCapacity();
}
function renderWarehouse(){
  const used=warehouseUsed(),cap=warehouseCapacity(),space=emptyCells().length;
  $('warehouseCount').textContent=`${used} / ${cap}`;
  $('warehouseMeter').style.width=Math.min(100,used/cap*100)+'%';
  $('warehouseBoardSpace').textContent=space?`盤面に ${space} マスの空きがあります`:'盤面が満杯です。取り出すには空きマスを作ってね。';
  $('warehouseUndo').disabled=!undoState;
  $('warehouseFilters').innerHTML=[['all','すべて'],...Object.entries(CHAIN_DATA).map(([k,v])=>[k,v.label])].map(([k,label])=>`<button data-warehouse-filter="${k}" aria-pressed="${warehouseFilter===k}" class="${warehouseFilter===k?'active':''}">${esc(label)}</button>`).join('');
  const rows=warehouseEntries().filter(([id])=>warehouseFilter==='all'||ITEMS[id].k===warehouseFilter);
  $('warehouseList').innerHTML=rows.length?rows.map(([id,n])=>`<article class="warehouseItem" data-stored-item="${id}"><div class="warehouseArt">${itemArt(id)}</div><div class="warehouseInfo"><small>${esc(CHAIN_DATA[ITEMS[id].k].label)} ・ Lv${levelOf(id)}</small><b>${esc(nameOf(id))}</b><span>${n}こ保管中</span></div><button class="good" data-take="${id}" ${space?'':'disabled'} aria-label="${esc(nameOf(id))} レベル${levelOf(id)}を1こ取り出す">取り出す</button></article>`).join(''):`<div class="warehouseEmpty">${gameIcon('warehouse')}<h3>${used?'この種類はまだありません':'倉庫はまだ空っぽです'}</h3><p>ゲームでアイテムを1回タップして選び、<br><b>「預ける」</b>を押すとここに入ります。</p><button data-go="game" class="primary">ゲームで預ける</button></div>`;
  renderWarehouseLinks();
}
