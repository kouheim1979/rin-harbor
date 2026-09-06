function loadRaw(){
  const keys=[SAVE_KEY,...OLD_KEYS];
  for(const key of keys){
    try{
      const raw=localStorage.getItem(key);
      if(raw)return JSON.parse(raw);
    }catch(_e){}
  }
  return null;
}
function normalize(raw){
  const base=freshState();
  const src=raw&&typeof raw==='object'?raw:{};
  S={...base,...src};
  S.board=Array.isArray(src.board)&&src.board.length===GRID?src.board.map(id=>ITEMS[id]?id:null):base.board;
  S.coins=Number.isFinite(+src.coins)?Math.max(0,+src.coins):base.coins;
  S.stars=Number.isFinite(+src.stars)?Math.max(0,+src.stars):0;
  S.level=Math.max(1,Math.floor(+src.level||1));
  S.xp=Math.max(0,+src.xp||0);
  S.story=clamp(Math.floor(+src.story||0),0,STORIES.length-1);
  S.repair=clamp(Math.floor(+src.repair||0),0,5);
  S.auto=src.auto!==false;
  S.autoStory=src.autoStory!==false;
  S.sound=src.sound===true;
  S.haptics=src.haptics!==false;
  S.book=src.book&&typeof src.book==='object'?{...src.book}:{...base.book};
  S.board.forEach(id=>{if(id)S.book[id]=1});
  S.orders=Array.isArray(src.orders)?src.orders.filter(validOrder).map(sanitizeOrder):[];
  S.stats={...base.stats,...(src.stats&&typeof src.stats==='object'?src.stats:{})};
  for(const k of Object.keys(base.stats))S.stats[k]=Math.max(0,Math.floor(+S.stats[k]||0));
  S.stats.bestLevel=Math.max(S.stats.bestLevel,highestDiscoveredLevel());
  S.daily={...base.daily,...(src.daily&&typeof src.daily==='object'?src.daily:{})};
  if(!Array.isArray(S.daily.missions))S.daily.missions=[];
  ensureOrders();
  ensureDaily();
}
function validOrder(o){
  return !!(o&&Array.isArray(o.wants)&&o.wants.length&&o.wants.every(w=>w&&ITEMS[w.id]&&!isGen(w.id)&&Number.isFinite(+w.n)&&+w.n>0));
}
function sanitizeOrder(o){
  return {
    title:String(o.title||'港のお客さんのお願い').slice(0,40),
    wants:o.wants.map(w=>({id:w.id,n:clamp(Math.floor(+w.n||1),1,4)})),
    coin:clamp(Math.floor(+o.coin||10),1,999999),
    star:clamp(Math.floor(+o.star||1),1,99),
    xp:clamp(Math.floor(+o.xp||10),1,999999)
  };
}
function load(){normalize(loadRaw());saveNow()}
function saveNow(){try{localStorage.setItem(SAVE_KEY,JSON.stringify(S))}catch(_e){toast('セーブ容量が足りません')}}
function saveSoon(){clearTimeout(saveTimer);saveTimer=setTimeout(saveNow,120)}
function makeUndo(label){undoState=JSON.stringify(S);undoLabel=label||'直前の操作';updateUndoButton()}
function undo(){
  if(!undoState){say('戻せる操作がないよ。');return}
  try{
    const previous=JSON.parse(undoState);undoState=null;undoLabel='';normalize(previous);selected=null;hintPair=[];combo=0;renderAll();saveNow();say('↩️ 直前の操作を戻したよ。');
  }catch(_e){undoState=null;undoLabel='';updateUndoButton();say('戻せませんでした。')}
}
function updateUndoButton(){const b=$('undo');if(!b)return;b.disabled=!undoState;b.textContent=undoState?'↩️ '+undoLabel:'↩️ 戻す'}
function localDateString(d=new Date()){const y=d.getFullYear(),m=String(d.getMonth()+1).padStart(2,'0'),day=String(d.getDate()).padStart(2,'0');return `${y}-${m}-${day}`}
function yesterdayString(){const d=new Date();d.setDate(d.getDate()-1);return localDateString(d)}
function buildDailyMissions(date){
  const seed=[...date].reduce((a,c)=>(a*31+c.charCodeAt(0))>>>0,7),plus=seed%4;
  return [
    {type:'generate',title:'材料を出そう',icon:'🏪',goal:16+plus,rewardCoin:30,rewardStar:1,progress:0,claimed:false},
    {type:'merge',title:'合成しよう',icon:'✨',goal:9+(seed%3),rewardCoin:45,rewardStar:1,progress:0,claimed:false},
    {type:'deliver',title:'注文を届けよう',icon:'🚢',goal:2+(seed%2),rewardCoin:60,rewardStar:2,progress:0,claimed:false}
  ];
}
function ensureDaily(){
  const today=localDateString();
  if(S.daily.date!==today){
    const last=S.daily.lastVisit||S.daily.date;
    S.daily.streak=last===yesterdayString()?Math.max(1,+S.daily.streak||0)+1:1;
    S.daily.date=today;S.daily.lastVisit=today;S.daily.missions=buildDailyMissions(today);S.daily.allClearClaimed=false;S.coins+=30;
    setTimeout(()=>toast('☀️ 今日のボーナス +30コイン'),60);
  }else{
    S.daily.lastVisit=today;S.daily.streak=Math.max(1,+S.daily.streak||1);
    if(!Array.isArray(S.daily.missions)||S.daily.missions.length!==3)S.daily.missions=buildDailyMissions(today);
  }
}
function updateMission(type,amount=1){const m=S.daily.missions.find(x=>x.type===type);if(!m||m.claimed)return;const before=m.progress;m.progress=clamp((+m.progress||0)+amount,0,m.goal);if(before<m.goal&&m.progress>=m.goal)toast('✅ デイリーミッション達成！')}
function claimMission(i){
  const m=S.daily.missions[i];if(!m||m.claimed||m.progress<m.goal)return;
  m.claimed=true;S.coins+=m.rewardCoin;S.stars+=m.rewardStar;toast(`🎁 ${m.title}：🪙${m.rewardCoin} ⭐${m.rewardStar}`);sound('reward');celebrate(10);haptic([20,35,20]);
  if(S.daily.missions.every(x=>x.claimed)&&!S.daily.allClearClaimed){S.daily.allClearClaimed=true;S.stars+=3;setTimeout(()=>{toast('🌟 今日のミッション全クリア！ ⭐3');celebrate(18)},350)}
  renderAll();saveSoon();
}
function highestDiscoveredLevel(){let n=1;for(const id of Object.keys(S?.book||{}))if(S.book[id]&&ITEMS[id])n=Math.max(n,levelOf(id));return n}
function xpThreshold(){return 40+S.level*20}
function addXp(x){S.xp+=x;let leveled=0;while(S.xp>=xpThreshold()){S.xp-=xpThreshold();S.level++;S.coins+=20;leveled++}if(leveled){toast(`🎉 Lv${S.level}！ +20コイン`);celebrate(12);sound('level')}}
function emptyCells(){const a=[];for(let i=0;i<S.board.length;i++)if(!S.board[i])a.push(i);return a}
function addItem(id){const e=emptyCells();if(!e.length)return false;const pos=e[Math.floor(Math.random()*e.length)];S.board[pos]=id;S.book[id]=1;S.stats.bestLevel=Math.max(S.stats.bestLevel,levelOf(id));return true}
function weightedPick(a){let total=a.reduce((s,x)=>s+x[1],0),r=Math.random()*total;for(const x of a){r-=x[1];if(r<=0)return x[0]}return a[0][0]}
function countBoard(){const c={};for(const id of S.board)if(id&&!isGen(id))c[id]=(c[id]||0)+1;return c}
function orderCan(o){const c=countBoard();return o.wants.every(w=>(c[w.id]||0)>=w.n)}
function firstReadyOrder(){return S.orders.findIndex(orderCan)}
function maxOrderLevel(){return Math.min(MAX_ITEM_LEVEL,Math.max(2,Math.floor(S.level/2)+2))}
function createOrder(){
  const kinds=new Set(['drink','dessert','shell','fish']);if(S.board.includes('gen_gift'))kinds.add('toy');
  const max=maxOrderLevel(),ids=Object.keys(ITEMS).filter(id=>!isGen(id)&&kinds.has(ITEMS[id].k)&&levelOf(id)>=2&&levelOf(id)<=max),wantCount=Math.random()<.82?1:2,wants=[];
  for(let i=0;i<wantCount;i++){const id=ids[Math.floor(Math.random()*ids.length)]||'drink2',found=wants.find(x=>x.id===id);found?found.n++:wants.push({id,n:1})}
  const score=wants.reduce((s,w)=>s+levelOf(w.id)*levelOf(w.id)*w.n,0);
  return {title:CUSTOMERS[Math.floor(Math.random()*CUSTOMERS.length)]+'のお願い',wants,coin:10+score*4,star:score>=9?2:1,xp:10+score*3};
}
function ensureOrders(){while(S.orders.length<ORDER_TARGET)S.orders.push(createOrder())}
function consumeOrder(o){for(const w of o.wants){let n=w.n;for(let j=0;j<S.board.length&&n>0;j++)if(S.board[j]===w.id){S.board[j]=null;n--}}}
function completeOrder(i,auto=false){
  const o=S.orders[i];if(!o||!orderCan(o))return false;consumeOrder(o);S.coins+=o.coin;S.stars+=o.star;addXp(o.xp);S.stats.delivered++;updateMission('deliver',1);S.orders.splice(i,1,createOrder());ensureOrders();selected=null;
  if(!auto){say(`🚢 ${o.title}を納品！ 🪙${o.coin} ⭐${o.star}`);toast('🚢 注文を届けたよ！');celebrate(8);sound('deliver');haptic([20,30,30]);if(S.autoStory)autoOpenStory()}
  return true;
}
function autoDeliver(){let done=0;for(let guard=0;guard<12;guard++){const i=firstReadyOrder();if(i<0)break;completeOrder(i,true);done++}if(done){toast(`🤖 自動納品 ${done}件！`);celebrate(Math.min(14,done*4));sound('deliver');if(S.autoStory)autoOpenStory()}return done}
function quickDeliver(){const i=firstReadyOrder();if(i>=0){completeOrder(i,false);renderAll();saveSoon()}else say('今は納品できる注文がないよ。')}
function generatorTap(i){const id=S.board[i];if(!isGen(id))return;if(!emptyCells().length){say('ボードがいっぱいだよ。合成か売却をしてね。');haptic(40);return}makeUndo('材料');const made=weightedPick(ITEMS[id].p);addItem(made);S.stats.generated++;updateMission('generate',1);say(`${nameOf(made)} が出たよ。`);sound('pop');finishBoardAction()}
function cellTap(i){const id=S.board[i];if(selected===null){if(!id){say('空きマスだよ。');return}if(isGen(id)){generatorTap(i);return}selected=i;say(`${nameOf(id)} を選んだよ。もう1つ同じアイテムをタップしても合成できるよ。`);renderGame();return}if(selected===i){selected=null;say('選択解除。');renderGame();return}moveOrMerge(selected,i)}
function moveOrMerge(a,b){
  const x=S.board[a],y=S.board[b];if(!x)return;if(isGen(x)){selected=null;say('屋台は固定だよ。');renderGame();return}if(a===b){selected=null;renderGame();return}
  if(!y){makeUndo('移動');S.board[b]=x;S.board[a]=null;selected=b;hintPair=[];renderGame();saveSoon();return}
  if(isGen(y)){say('屋台とは合成できないよ。');return}
  if(x===y&&ITEMS[x].next){
    makeUndo('合成');const z=ITEMS[x].next;S.board[a]=null;S.board[b]=z;S.book[z]=1;S.stats.merges++;S.stats.bestLevel=Math.max(S.stats.bestLevel,levelOf(z));updateMission('merge',1);
    const now=Date.now();combo=now-lastMergeAt<3500?combo+1:1;lastMergeAt=now;const comboBonus=combo>=3?combo-2:0;S.coins+=Math.max(1,levelOf(z))+comboBonus;addXp(3+levelOf(z));selected=null;hintPair=[];
    say(`✨ ${nameOf(z)} ができたよ！${comboBonus?` コンボ+${comboBonus}コイン`:''}`);sound('merge');haptic(18);celebrate(combo>=5?8:3);finishBoardAction();return;
  }
  say(x===y?'Lv10の最高レベルだよ。':'同じアイテムを重ねてね。');haptic(30);
}
function finishBoardAction(){ensureOrders();if(S.auto)autoDeliver();if(S.autoStory)autoOpenStory();renderAll();saveSoon()}
function sortBoard(){makeUndo('整列');const gens=S.board.filter(id=>id&&isGen(id)),items=S.board.filter(id=>id&&!isGen(id)).sort((a,b)=>ITEMS[a].k.localeCompare(ITEMS[b].k)||levelOf(a)-levelOf(b)),arr=[...gens,...items];S.board=[...arr,...Array(GRID-arr.length).fill(null)];selected=null;hintPair=[];say('🧺 アイテムを整列したよ。');renderGame();saveSoon()}
function sellSelected(){if(selected===null){say('売るアイテムを選んでね。');return}const id=S.board[selected];if(!id||isGen(id)){say('これは売れないよ。');return}const value=Math.max(1,Math.floor((ITEMS[id].price||1)/2));if(levelOf(id)>=7&&!confirm(`${nameOf(id)} はLv${levelOf(id)}です。本当に ${value}コインで売りますか？`))return;makeUndo('売却');S.board[selected]=null;S.coins+=value;S.stats.sold++;selected=null;say(`🪙 ${nameOf(id)} を ${value}コインで売ったよ。`);sound('sell');renderAll();saveSoon()}
function findMergePair(){const map={};for(let i=0;i<S.board.length;i++){const id=S.board[i];if(!id||isGen(id)||!ITEMS[id].next)continue;if(map[id]!==undefined)return [map[id],i];map[id]=i}return null}
function showHint(){
  const p=findMergePair();if(p){hintPair=p;renderGame();say(`💡 ${nameOf(S.board[p[0]])} が2つあるよ。光っている2つを重ねよう。`);setTimeout(()=>{hintPair=[];if(view==='game')renderGame()},2200);return}
  if(emptyCells().length){hintPair=S.board.map((id,i)=>isGen(id)?i:null).filter(i=>i!==null).slice(0,2);renderGame();say('💡 合成できる組み合わせがないよ。光っている屋台をタップして材料を増やそう。');setTimeout(()=>{hintPair=[];if(view==='game')renderGame()},2200)}else say('💡 ボードがいっぱい。不要な低レベルアイテムを売るか、注文を確認しよう。')
}
