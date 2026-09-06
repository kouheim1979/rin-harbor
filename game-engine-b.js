function autoOpenStory(){
  let opened=0;
  for(let guard=0;guard<STORIES.length;guard++){
    const next=S.story+1,s=STORIES[next];
    if(!s||S.stars<s.cost)break;
    if(s.item&&!emptyCells().length)break;
    S.stars-=s.cost;S.story=next;
    if(s.coins)S.coins+=s.coins;
    if(s.item)addItem(s.item);
    opened++;
  }
  if(opened){toast(`📖 物語が ${opened}話 進んだよ！`);celebrate(10);sound('story')}
}
function openStory(i){
  const s=STORIES[i];
  if(!s||i!==S.story+1||S.stars<s.cost)return;
  if(s.item&&!emptyCells().length){toast('ボードに空きを1つ作ってね');return}
  S.stars-=s.cost;S.story=i;if(s.coins)S.coins+=s.coins;if(s.item)addItem(s.item);
  toast(`📖 ${s.t} を開放！`);celebrate(12);sound('story');renderAll();saveSoon();
}
function repairShip(){
  const r=S.repair;
  if(r>=5){toast('🚢 リン号は完成しているよ！');return}
  const cost=REPAIR_COSTS[r];
  if(S.coins<cost){toast(`🪙 あと ${cost-S.coins}コイン 必要だよ`);haptic(40);return}
  S.coins-=cost;S.repair++;
  toast(`🔧 ${REPAIR_MESSAGES[S.repair]}`);say(REPAIR_MESSAGES[S.repair]);celebrate(14);sound('repair');haptic([20,40,20]);
  renderAll();saveSoon();
}
function setView(v){
  if(!['opening','home','game','orders','story','book'].includes(v))v='home';
  view=v;selected=null;hintPair=[];
  document.querySelectorAll('.screen').forEach(x=>x.classList.remove('on'));
  $('screen'+v[0].toUpperCase()+v.slice(1)).classList.add('on');
  $('nav').classList.toggle('hidden',v==='opening');
  document.querySelectorAll('#nav button').forEach(b=>b.classList.toggle('active',b.dataset.go===v));
  renderAll();
  const screen=$('screen'+v[0].toUpperCase()+v.slice(1));if(screen)screen.scrollTop=0;
}
function statsHtml(){
  const discovered=Object.keys(ITEMS).filter(id=>S.book[id]).length;
  return `<div class="stat"><small>コイン</small><b>🪙${S.coins}</b></div><div class="stat"><small>星</small><b>⭐${S.stars}</b></div><div class="stat"><small>レベル</small><b>Lv${S.level}</b></div><div class="stat"><small>修理</small><b>🔧${S.repair}/5</b></div><div class="stat"><small>図鑑</small><b>${discovered}</b></div>`;
}
function miniStatsHtml(){
  return `<span>🪙${S.coins}</span><span>⭐${S.stars}</span><span>Lv${S.level}</span><span>🔧${S.repair}/5</span><span>${S.auto?'🤖ON':'手動'}</span>${combo>1?`<span class="combo">🔥${combo}コンボ</span>`:''}`;
}
function renderHome(){
  $('statsHome').innerHTML=statsHtml();
  $('streakBadge').textContent=`🔥 ${S.daily.streak}日`;
  const r=S.repair,cost=r<5?REPAIR_COSTS[r]:0;
  $('repairTitle').textContent=REPAIR_TITLES[r];
  $('repairSub').textContent=r>=5?'完成！ 新しい冒険へ':`必要 🪙${cost} / 所持 🪙${S.coins}`;
  $('repairBar').style.width=(r/5*100)+'%';
  $('repairBtn').disabled=r>=5;
  $('repairBtn').textContent=r>=5?'🚢 完成':'🔧 '+cost;
  $('homeShipFallback').textContent=REPAIR_SHIPS[r];
  setStageImage($('homeShipImage'),r);
  const ready=S.orders.filter(orderCan).length;
  $('homeOrderTitle').textContent=ready?`納品OK ${ready}件`:`注文 ${S.orders.length}件`;
  $('homeOrderSub').textContent=ready?(S.auto?'自動納品ON':'注文画面から届けよう'):'材料を合成してそろえよう';
  const discovered=Object.keys(ITEMS).filter(id=>S.book[id]).length;
  $('homeBookSub').textContent=`${discovered}/${Object.keys(ITEMS).length} 発見`;
  renderDaily();
}
function renderDaily(){
  $('dailyDate').textContent=S.daily.date.replaceAll('-',' / ');
  const list=$('dailyList');list.innerHTML='';
  S.daily.missions.forEach((m,i)=>{
    const done=m.progress>=m.goal,pct=Math.min(100,m.progress/m.goal*100);
    const el=document.createElement('div');el.className='mission';
    el.innerHTML=`<div class="missionRow"><div class="missionTitle">${m.icon} ${esc(m.title)}</div><div class="missionReward">🪙${m.rewardCoin} ⭐${m.rewardStar}</div></div>
      <div class="progress"><i style="width:${pct}%"></i></div>
      <div class="missionFoot"><span>${m.progress}/${m.goal}</span>${m.claimed?'<span>✅ 受取済み</span>':done?`<button class="primary" data-claim="${i}">🎁 受け取る</button>`:'<span>進行中</span>'}</div>`;
    list.appendChild(el);
  });
  $('dailyClear').textContent=S.daily.allClearClaimed?'🌟 全クリア済み':'3つクリアで⭐3';
}
function renderGame(){
  ensureOrders();
  $('miniStats').innerHTML=miniStatsHtml();
  $('board').innerHTML=S.board.map((id,i)=>{
    const cls=['cell',!id?'empty':'',id&&isGen(id)?'gen':'',selected===i?'sel':'',hintPair.includes(i)?'hint':''].filter(Boolean).join(' ');
    return `<button class="${cls}" data-i="${i}" aria-label="${id?esc(nameOf(id)):'空きマス'}">${id?`<div class="em">${emojiOf(id)}</div><div class="nm">${esc(nameOf(id))}</div>${isGen(id)?'<div class="tap">TAP</div>':`<div class="lv">Lv${levelOf(id)}</div>`}`:''}</button>`;
  }).join('');
  renderNextOrder();
  $('sell').disabled=selected===null||!S.board[selected]||isGen(S.board[selected]);
  $('autoGame').textContent=S.auto?'🤖 ON':'🤖 OFF';$('autoGame').className=S.auto?'good':'off';
  updateUndoButton();
}
function renderNextOrder(){
  const f=firstReadyOrder(),o=f>=0?S.orders[f]:S.orders[0],c=countBoard();
  $('quickTop').disabled=f<0;
  $('nextOrderTitle').textContent=f>=0?'🚢 納品できます':o?o.title:'注文なし';
  $('nextOrderSub').textContent=f>=0?(S.auto?'自動納品ONです':'ボタンで届けよう'):'必要なアイテムを合成しよう';
  $('nextWants').innerHTML=o?o.wants.map(w=>`<span class="${(c[w.id]||0)>=w.n?'ok':''}">${emojiOf(w.id)} ${esc(nameOf(w.id))} ${c[w.id]||0}/${w.n}</span>`).join(''):'';
}
function renderOrders(){
  $('statsOrders').innerHTML=statsHtml();
  const c=countBoard();
  $('orders').innerHTML=S.orders.map((o,i)=>`<div class="order"><div class="ot"><span>${esc(o.title)}</span><span>🪙${o.coin} ⭐${o.star}</span></div>${o.wants.map(w=>`<div class="want ${(c[w.id]||0)>=w.n?'ok':'ng'}"><span>${emojiOf(w.id)} ${esc(nameOf(w.id))}</span><span>${c[w.id]||0}/${w.n}</span></div>`).join('')}<button class="${orderCan(o)?'primary':''}" data-order="${i}" ${orderCan(o)?'':'disabled'}>${orderCan(o)?'🚢 納品する':'まだ足りない'}</button></div>`).join('');
}
function renderStory(){
  $('statsStory').innerHTML=statsHtml();
  $('storyList').innerHTML=STORIES.map((s,i)=>{
    const open=i<=S.story,canOpen=i===S.story+1&&S.stars>=s.cost;
    return `<div class="storyCard ${open?'':'locked'}"><div class="ot"><span>${open?'📖':'🔒'} ${esc(s.t)}</span><span>⭐${s.cost}</span></div><div>${open||canOpen?esc(s.x):'まだ開放されていません。'}</div><div class="storyMeta">${s.coins?`<span class="pill">報酬 🪙${s.coins}</span>`:''}${s.item?'<span class="pill">新しい屋台 🏵️</span>':''}</div>${canOpen?`<button class="primary" data-story="${i}">⭐ ${s.cost}で開放</button>`:''}</div>`;
  }).join('');
  renderAlbumStrip();
}
function renderAlbumStrip(){
  const unlocked=ALBUM.slice(0,S.repair+1);
  $('albumStrip').innerHTML=unlocked.map((a,i)=>`<button class="albumThumb" data-album="${i}"><img src="${bestStagePath(i)}" alt="${esc(a.title)}" onerror="this.style.display='none'"><span>${esc(a.title)}</span></button>`).join('');
}
function renderBook(){
  $('statsBook').innerHTML=statsHtml();
  const discovered=Object.keys(ITEMS).filter(id=>S.book[id]).length,total=Object.keys(ITEMS).length;
  $('bookProgressText').textContent=`${discovered}/${total} 発見`;
  const blocks=[];
  for(const [kind,data] of Object.entries(CHAIN_DATA)){
    const ids=Array.from({length:MAX_ITEM_LEVEL},(_,i)=>kind+(i+1));
    const found=ids.filter(id=>S.book[id]).length;
    blocks.push(`<div class="chain"><div class="chainHead"><span>${data.icon} ${esc(data.label)}</span><span>${found}/10</span></div><div class="chainGrid">${ids.map(id=>{const open=!!S.book[id];return `<div class="bookItem ${open?'':'locked'}"><div class="bookEmoji">${open?emojiOf(id):'❓'}</div><div class="bookName">${open?esc(nameOf(id)):'???'}</div><div class="bookLv">Lv${levelOf(id)}</div></div>`}).join('')}</div></div>`);
  }
  $('bookChains').innerHTML=blocks.join('');
  setToggle($('autoSetting'),S.auto,'ON','OFF');
  setToggle($('autoStorySetting'),S.autoStory,'ON','OFF');
  setToggle($('soundSetting'),S.sound,'ON','OFF');
  setToggle($('hapticSetting'),S.haptics,'ON','OFF');
}
function setToggle(btn,on,onText,offText){btn.textContent=on?onText:offText;btn.className='toggle '+(on?'good':'off')}
function renderAll(){ensureOrders();ensureDaily();if(view==='home')renderHome();if(view==='game')renderGame();if(view==='orders')renderOrders();if(view==='story')renderStory();if(view==='book')renderBook();saveSoon()}
function say(t){if($('msg'))$('msg').textContent=t}
function toast(t){const el=$('toast');el.textContent=t;el.classList.add('on');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('on'),1800)}
function celebrate(n=8){const box=$('celebrate'),icons=['✨','⭐','💖','🎀','🌸','🫧'];for(let i=0;i<n;i++){const x=document.createElement('div');x.className='confetti';x.textContent=icons[Math.floor(Math.random()*icons.length)];x.style.left=Math.random()*100+'vw';x.style.setProperty('--x',(Math.random()*160-80)+'px');x.style.animationDelay=(Math.random()*.18)+'s';box.appendChild(x);setTimeout(()=>x.remove(),1500)}}
function haptic(pattern){if(!S.haptics||!navigator.vibrate)return;try{navigator.vibrate(pattern)}catch(_e){}}
function sound(type){
  if(!S.sound)return;
  try{audioCtx=audioCtx||new (window.AudioContext||window.webkitAudioContext)();if(audioCtx.state==='suspended')audioCtx.resume();const map={pop:[420,.05],merge:[620,.08],deliver:[760,.12],reward:[880,.12],level:[980,.15],story:[700,.14],repair:[520,.14],sell:[330,.06]};const [freq,dur]=map[type]||[500,.06];const o=audioCtx.createOscillator(),g=audioCtx.createGain();o.type='sine';o.frequency.value=freq;g.gain.setValueAtTime(.0001,audioCtx.currentTime);g.gain.exponentialRampToValueAtTime(.08,audioCtx.currentTime+.01);g.gain.exponentialRampToValueAtTime(.0001,audioCtx.currentTime+dur);o.connect(g).connect(audioCtx.destination);o.start();o.stop(audioCtx.currentTime+dur+.02)}catch(_e){}
}
function bestStagePath(stage){return stage===0?'assets/repair-stage-0.jpg':`assets/repair-stage-${stage}.webp`}
function setStageImage(img,stage){const desired=bestStagePath(stage);if(img.dataset.src===desired)return;img.dataset.src=desired;img.style.display='none';img.src=desired;img.onload=()=>{img.style.display='block'};img.onerror=()=>{img.style.display='none'}}
function openAlbum(index=0){
  const unlocked=ALBUM.slice(0,S.repair+1),viewer=$('viewer'),title=$('viewerTitle'),img=$('viewerImg'),text=$('viewerText'),thumbs=$('viewerThumbs');
  const render=i=>{const item=unlocked[i]||unlocked[0];if(!item)return;title.textContent=item.title;text.textContent=item.text;img.src=bestStagePath(i);img.alt=item.title;thumbs.innerHTML=unlocked.map((it,j)=>`<button class="viewerThumb ${j===i?'primary':''}" data-view-stage="${j}"><img src="${bestStagePath(j)}" alt="${esc(it.title)}"><div>${esc(it.title)}</div></button>`).join('')};
  viewer.classList.add('on');render(index);
}
function exportSave(){try{const json=JSON.stringify(S),code='RH10-'+btoa(unescape(encodeURIComponent(json)));if(navigator.clipboard?.writeText){navigator.clipboard.writeText(code).then(()=>toast('📋 バックアップコードをコピーしたよ')).catch(()=>prompt('このコードを保存してください',code))}else prompt('このコードを保存してください',code)}catch(_e){toast('バックアップを作れませんでした')}}
function importSave(){const code=prompt('RH10- から始まるバックアップコードを貼り付けてください');if(!code)return;try{const raw=code.trim().replace(/^RH10-/,''),json=decodeURIComponent(escape(atob(raw))),data=JSON.parse(json);if(!data||!Array.isArray(data.board)||data.board.length!==GRID)throw new Error('invalid');if(!confirm('現在のセーブをバックアップ内容で置き換えますか？'))return;normalize(data);undoState=null;selected=null;saveNow();renderAll();toast('✅ 復元しました')}catch(_e){alert('バックアップコードが正しくありません。')}}
function resetGame(){if(!confirm('リンハーバーを最初からやり直しますか？ この端末の進行状況が消えます。'))return;try{localStorage.removeItem(SAVE_KEY);OLD_KEYS.forEach(k=>localStorage.removeItem(k))}catch(_e){}S=freshState();ensureDaily();ensureOrders();undoState=null;selected=null;saveNow();setView('opening');toast('最初の状態に戻しました')}
