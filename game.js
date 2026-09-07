'use strict';

const $=id=>document.getElementById(id);
const GRID=36, MAX_ITEM_LEVEL=10, ORDER_TARGET=8, SAVE_KEY='rin_harbor_save_v10';
const OLD_KEYS=['rin_harbor_save_v9','rin_harbor_save_v8','rin_harbor_save_v7','rin_harbor_save_v6','rin_harbor_save_v5'];
let S=null, selected=null, view='opening', saveTimer=null, drag=null, undoState=null, undoLabel='', hintPair=[], combo=0, lastMergeAt=0, toastTimer=null, audioCtx=null;



const CHAIN_DATA={
  drink:{label:'ドリンク',icon:'🥤',names:['コーヒー豆','カップコーヒー','ミルクラテ','スペシャルラテ','キャラメルドリンク','ソーダフロート','レモンドリンク','トロピカルジュース','きらきらジュース','リン特製ドリンク'],icons:['🫘','☕','🥛','🍵','🧋','🥤','🍋','🍍','🍹','🫖']},
  dessert:{label:'スイーツ',icon:'🍰',names:['クッキー','ドーナツ','ケーキ','豪華パフェ','プリン','カップケーキ','アイスクリーム','宝石ゼリー','パンケーキ','リン特製スイーツ'],icons:['🍪','🍩','🍰','🍨','🍮','🧁','🍦','🍧','🥞','🍬']},
  shell:{label:'海の宝物',icon:'🐚',names:['小さな貝','真珠貝','宝石の貝','海の宝箱','さんごの飾り','金の巻き貝','人魚の首飾り','海の王冠','伝説の宝','リンの海の宝物'],icons:['🐚','🦪','💎','🧰','🪸','📯','📿','👑','🔱','⚜️']},
  fish:{label:'港ごはん',icon:'🐟',names:['小魚','焼き魚','海鮮プレート','豪華おすし','えびプレート','かにプレート','船長ランチ','お祭り海鮮','港のフルコース','リン特製ごちそう'],icons:['🐟','🍢','🍣','🍱','🦐','🦀','🍽️','🥘','🍲','🍛']},
  toy:{label:'リンの宝物',icon:'🎀',names:['リボン','ぬいぐるみ','小さな帽子','リンの宝物','きらきらバッグ','プリンセスドレス','魔法のステッキ','星のティアラ','夢の宝石箱','リンの最高の宝物'],icons:['🎀','🧸','🎩','🌟','👜','👗','🪄','💫','🎁','🏅']}
};
const ITEMS={
  gen_cafe:{n:'リンカフェ屋台',e:'🏪',k:'gen',p:[['drink1',65],['dessert1',35]]},
  gen_sea:{n:'海辺のかご',e:'🧺',k:'gen',p:[['shell1',55],['fish1',45]]},
  gen_gift:{n:'リボン屋台',e:'🏵️',k:'gen',p:[['toy1',70],['dessert1',30]]}
};
for(const [kind,data] of Object.entries(CHAIN_DATA)){
  for(let i=1;i<=MAX_ITEM_LEVEL;i++){
    ITEMS[kind+i]={n:data.names[i-1],e:data.icons[i-1],k:kind,l:i,next:i<MAX_ITEM_LEVEL?kind+(i+1):null,price:Math.max(1,Math.round(Math.pow(2,i-1)*(kind==='toy'?2:1)))};
  }
}
const CUSTOMERS=['ねこ船長','ペンギン店長','うさぎ観光客','カモメ配達員','イルカ先生','くまパティシエ','りす親子','ハムスター駅長','ラッコ案内人','カニ職人'];
const STORIES=[
  {t:'第1話：リンハーバーへようこそ',x:'リンちゃんは古くなった港をかわいく直すことにしました。',cost:0},
  {t:'第2話：桟橋を修理',x:'桟橋がピカピカになって、お客さんが集まってきます。',cost:3,coins:30},
  {t:'第3話：リボン屋台',x:'かわいいリボン屋台ができました。宝物アイテムが作れます。',cost:6,item:'gen_gift'},
  {t:'第4話：灯台にあかり',x:'夜でも船が安心して帰ってこられます。',cost:9,coins:50},
  {t:'第5話：港まつり',x:'港まつりの準備が始まりました。注文を届けてもっとにぎやかにしましょう。',cost:14,coins:80},
  {t:'第6話：リンハーバー完成',x:'みんなが集まる、明るくてかわいい港になりました。',cost:20,coins:100},
  {t:'第7話：きらきら市場',x:'Lv10の宝物を目指して、港の市場が大きくなりました。',cost:28,coins:120},
  {t:'第8話：リンの大航海',x:'リンちゃんの港から、大きな船が出発します。',cost:38,coins:150}
];
const REPAIR_COSTS=[50,100,200,400,800];
const REPAIR_TITLES=['壊れたリン号','穴をふさぐ','船体を補強する','マストを直す','客室をきれいにする','リン号完成'];
const REPAIR_MESSAGES=['嵐でボロボロになったリン号。','船の穴をふさいだ！','船体が丈夫になった！','マストが直った！','客室がきれいになった！','リン号が完全に復活した！ 新しい冒険に出発だ！'];
const REPAIR_SHIPS=['⛵','⛵','⛵','⛵','🛥️','🚢'];
const ALBUM=REPAIR_TITLES.map((title,i)=>({title,text:REPAIR_MESSAGES[i],base:'assets/repair-stage-'+i}));

const hasItem=id=>typeof id==='string'&&Object.hasOwn(ITEMS,id);
const isGen=id=>!!(ITEMS[id]&&ITEMS[id].k==='gen');
const nameOf=id=>ITEMS[id]?.n||'不明';
const emojiOf=id=>ITEMS[id]?.e||'❓';
const levelOf=id=>ITEMS[id]?.l||0;
const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));


const RELEASE='20260906-r1';
const BACKUP_KEY='rin_harbor_before_art_v1';
const int=(v,lo=0,hi=1e9,fallback=0)=>Number.isFinite(Number(v))?Math.max(lo,Math.min(hi,Math.floor(Number(v)))):fallback;
let hintTimer=null, comboTimer=null, albumIndex=0, albumReturnFocus=null, diskAvailable=true;
const reducedMotion=()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches;


function initialBoard(){
  const b=Array(GRID).fill(null);
  b[0]='gen_cafe';b[5]='gen_sea';b[7]='drink1';b[8]='drink1';b[13]='dessert1';b[14]='shell1';
  return b;
}

function freshState(){
  return {
    board:initialBoard(),coins:50,stars:0,level:1,xp:0,story:0,repair:0,orders:[],
    book:{gen_cafe:1,gen_sea:1,drink1:1,dessert1:1,shell1:1},
    auto:true,autoStory:true,sound:false,haptics:true,
    stats:{merges:0,delivered:0,generated:0,sold:0,bestLevel:1},
    daily:{date:'',lastVisit:'',streak:0,missions:[],allClearClaimed:false}
  };
}

function loadRaw(){
  for(const key of [SAVE_KEY,...OLD_KEYS]){
    try{
      const raw=localStorage.getItem(key); if(!raw)continue;
      const value=JSON.parse(raw);
      if(!value||!Array.isArray(value.board)||value.board.length!==GRID)continue;
      try{if(!localStorage.getItem(BACKUP_KEY))localStorage.setItem(BACKUP_KEY,raw)}catch(_e){}
      return value;
    }catch(_e){}
  }
  return null;
}

function normalize(raw){
  const base=freshState(),src=raw&&typeof raw==='object'?raw:{};
  S={...base};
  S.board=Array.isArray(src.board)&&src.board.length===GRID?src.board.map(id=>hasItem(id)?id:null):base.board;
  S.coins=int(src.coins,0,1e12,base.coins);S.stars=int(src.stars,0,1e9,0);
  S.level=int(src.level,1,100000,1);S.xp=int(src.xp,0,10000000,0);
  S.story=int(src.story,0,STORIES.length-1);S.repair=int(src.repair,0,5);
  for(const k of ['auto','autoStory','haptics'])S[k]=src[k]!==false;
  S.sound=src.sound===true;
  S.book={};for(const id of Object.keys(ITEMS))if(src.book?.[id])S.book[id]=1;
  S.board.forEach(id=>{if(id)S.book[id]=1});
  S.orders=Array.isArray(src.orders)?src.orders.filter(validOrder).slice(0,ORDER_TARGET).map(sanitizeOrder):[];
  S.stats={...base.stats};for(const k of Object.keys(S.stats))S.stats[k]=int(src.stats?.[k]);
  S.stats.bestLevel=Math.max(S.stats.bestLevel,highestDiscoveredLevel());
  const d=src.daily&&typeof src.daily==='object'?src.daily:{};
  S.daily={date:/^\d{4}-\d{2}-\d{2}$/.test(d.date||'')?d.date:'',lastVisit:/^\d{4}-\d{2}-\d{2}$/.test(d.lastVisit||'')?d.lastVisit:'',streak:int(d.streak,0,100000),missions:[],allClearClaimed:d.allClearClaimed===true};
  const templates=buildDailyMissions(S.daily.date||localDateString());
  S.daily.missions=templates.map(m=>{const old=Array.isArray(d.missions)?d.missions.find(x=>x&&x.type===m.type):null;return {...m,progress:int(old?.progress,0,m.goal),claimed:old?.claimed===true&&int(old?.progress,0,m.goal)>=m.goal}});
  if(!S.daily.missions.every(m=>m.claimed))S.daily.allClearClaimed=false;
  restoreGenerators();ensureOrders();ensureDaily();
}

function validOrder(o){return !!(o&&Array.isArray(o.wants)&&o.wants.length>0&&o.wants.length<=4&&o.wants.every(w=>w&&hasItem(w.id)&&!isGen(w.id)&&Number.isFinite(+w.n)&&+w.n>0))}

function sanitizeOrder(o){
  const wants={};for(const w of o.wants)wants[w.id]=Math.min(4,(wants[w.id]||0)+int(w.n,1,4,1));
  return {title:String(o.title||'港のお客さんのお願い').slice(0,40),wants:Object.entries(wants).map(([id,n])=>({id,n})),coin:int(o.coin,1,999999,10),star:int(o.star,1,99,1),xp:int(o.xp,1,999999,10)};
}

function load(){normalize(loadRaw());saveNow()}

function saveNow(){
  if(!S)return false;clearTimeout(saveTimer);
  try{localStorage.setItem(SAVE_KEY,JSON.stringify(S));diskAvailable=true;return true}
  catch(_e){diskAvailable=false;const e=$('storageStatus');if(e)e.textContent='このブラウザでは保存できません。バックアップを保存してください。';return false}
}

function saveSoon(){clearTimeout(saveTimer);saveTimer=setTimeout(saveNow,120)}

function makeUndo(label){ensureDaily();undoState=JSON.stringify(S);undoLabel=label||'操作';updateUndoButton()}

function undo(){
  if(!undoState)return;
  try{const previous=JSON.parse(undoState);undoState=null;undoLabel='';normalize(previous);selected=null;hintPair=[];combo=0;lastMergeAt=0;clearTimeout(comboTimer);closeAlbum();renderAll();saveNow();say('直前の操作を戻したよ。');}
  catch(_e){undoState=null;updateUndoButton();toast('この操作は戻せませんでした。');}
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
  // A backward clock change must not award the same day's gift again.
  if(S.daily.date&&S.daily.date>=today)return;
  const last=S.daily.lastVisit||S.daily.date;
  S.daily.streak=last===yesterdayString()?int(S.daily.streak,0,100000)+1:1;
  S.daily.date=today;S.daily.lastVisit=today;S.daily.missions=buildDailyMissions(today);S.daily.allClearClaimed=false;S.coins+=30;
  undoState=null;undoLabel='';
  setTimeout(()=>toast('今日の贈りもの：30コイン'),60);
}

function updateMission(type,amount=1){ensureDaily();const m=S.daily.missions.find(x=>x.type===type);if(!m||m.claimed)return;const before=m.progress;m.progress=Math.min(m.goal,m.progress+amount);if(before<m.goal&&m.progress>=m.goal)toast('ミッション達成！ 港で報酬を受け取ろう。')}

function claimMission(i){
  ensureDaily();const m=S.daily.missions[i];if(!m||m.claimed||m.progress<m.goal)return;
  makeUndo('受取');m.claimed=true;S.coins+=m.rewardCoin;S.stars+=m.rewardStar;
  if(S.daily.missions.every(x=>x.claimed)&&!S.daily.allClearClaimed){S.daily.allClearClaimed=true;S.stars+=3;toast('今日のミッション全達成！ 追加で星3つ！')}else toast(`${m.title}：${m.rewardCoin}コイン ＋ 星${m.rewardStar}`);
  if(S.autoStory)autoOpenStory();sound('reward');celebrate(10);haptic(20);renderAll();saveNow();
}

function highestDiscoveredLevel(){let n=1;for(const id of Object.keys(S?.book||{}))if(S.book[id]&&ITEMS[id])n=Math.max(n,levelOf(id));return n}

function xpThreshold(){return 40+S.level*20}

function addXp(x){S.xp+=int(x,0,1000000);let levels=0;while(S.xp>=xpThreshold()&&levels<1000){S.xp-=xpThreshold();S.level++;S.coins+=20;levels++}if(levels){toast(`レベル${S.level}！ ${levels*20}コイン獲得`);celebrate(10);sound('level')}}

function emptyCells(){const a=[];for(let i=0;i<S.board.length;i++)if(!S.board[i])a.push(i);return a}

function addItem(id){const e=emptyCells();if(!e.length)return false;const pos=e[Math.floor(Math.random()*e.length)];S.board[pos]=id;S.book[id]=1;S.stats.bestLevel=Math.max(S.stats.bestLevel,levelOf(id));return true}

function weightedPick(a){let total=a.reduce((s,x)=>s+x[1],0),r=Math.random()*total;for(const x of a){r-=x[1];if(r<=0)return x[0]}return a[0][0]}

function countBoard(){const c={};for(const id of S.board)if(id&&!isGen(id))c[id]=(c[id]||0)+1;return c}

function orderCan(o){if(!validOrder(o))return false;const c=countBoard(),need={};for(const w of o.wants)need[w.id]=(need[w.id]||0)+w.n;return Object.entries(need).every(([id,n])=>(c[id]||0)>=n)}

function firstReadyOrder(){return S.orders.findIndex(orderCan)}

function maxOrderLevel(){return Math.min(MAX_ITEM_LEVEL,Math.max(2,highestDiscoveredLevel()+1),Math.max(2,Math.floor(S.level/2)+2))}

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
  const o=S.orders[i];if(!o||!orderCan(o))return false;if(!auto)makeUndo('納品');consumeOrder(o);S.coins+=o.coin;S.stars+=o.star;addXp(o.xp);S.stats.delivered++;updateMission('deliver',1);S.orders.splice(i,1,createOrder());ensureOrders();selected=null;
  if(!auto){say(`🚢 ${o.title}を納品！ 🪙${o.coin} ⭐${o.star}`);toast('🚢 注文を届けたよ！');celebrate(8);sound('deliver');haptic([20,30,30]);if(S.autoStory)autoOpenStory()}
  return true;
}

function autoDeliver(){let done=0;for(let guard=0;guard<12;guard++){const i=firstReadyOrder();if(i<0)break;completeOrder(i,true);done++}if(done){toast(`🤖 自動納品 ${done}件！`);celebrate(Math.min(14,done*4));sound('deliver');if(S.autoStory)autoOpenStory()}return done}

function quickDeliver(){const i=firstReadyOrder();if(i>=0){completeOrder(i,false);renderAll();saveSoon()}else say('今は納品できる注文がないよ。')}

function generatorTap(i){const id=S.board[i];if(!isGen(id))return;if(!emptyCells().length){say('ボードがいっぱいだよ。合成か売却をしてね。');haptic(40);return}makeUndo('材料');selected=null;hintPair=[];const made=weightedPick(ITEMS[id].p);addItem(made);S.stats.generated++;updateMission('generate',1);say(`${nameOf(made)} が出たよ。`);sound('pop');finishBoardAction()}

function cellTap(i){
  if(!Number.isInteger(i)||i<0||i>=GRID)return;
  const id=S.board[i];
  if(isGen(id)){generatorTap(i);return}
  if(selected!==null&&!S.board[selected])selected=null;
  if(selected===i){selected=null;say('同じものを2つ重ねると、ひとつ先のアイテムになるよ。');renderGame();return}
  if(selected!==null&&(!id||id===S.board[selected])){moveOrMerge(selected,i);return}
  if(!id){say('カフェか海辺のかごをタップして、材料を出してね。');return}
  selected=i;say(`${nameOf(id)} ・ Lv${levelOf(id)}${ITEMS[id].next?' → '+nameOf(ITEMS[id].next):' ・ 最高レベル'}`);renderGame();
}

function moveOrMerge(a,b){
  if(!Number.isInteger(a)||!Number.isInteger(b)||a<0||b<0||a>=GRID||b>=GRID)return;
  const x=S.board[a],y=S.board[b];if(!x)return;if(isGen(x)){selected=null;say('屋台は固定だよ。');renderGame();return}if(a===b){selected=null;renderGame();return}
  if(!y){makeUndo('移動');S.board[b]=x;S.board[a]=null;selected=b;hintPair=[];renderGame();saveSoon();return}
  if(isGen(y)){say('屋台とは合成できないよ。');return}
  if(x===y&&ITEMS[x].next){
    makeUndo('合成');const z=ITEMS[x].next;S.board[a]=null;S.board[b]=z;S.book[z]=1;S.stats.merges++;S.stats.bestLevel=Math.max(S.stats.bestLevel,levelOf(z));updateMission('merge',1);
    const now=Date.now();combo=now-lastMergeAt<3500?combo+1:1;lastMergeAt=now;const comboBonus=combo>=3?Math.min(10,combo-2):0;S.coins+=Math.max(1,levelOf(z))+comboBonus;addXp(3+levelOf(z));selected=null;hintPair=[];
    say(`✨ ${nameOf(z)} ができたよ！${comboBonus?` コンボ+${comboBonus}コイン`:''}`);sound('merge');haptic(18);celebrate(combo>=5?8:3);finishBoardAction();mergeEffect(b);clearTimeout(comboTimer);comboTimer=setTimeout(()=>{combo=0;if(view==='game')renderGame()},3600);return;
  }
  say(x===y?'Lv10の最高レベルだよ。':'同じアイテムを重ねてね。');haptic(30);
}

function finishBoardAction(){restoreGenerators();ensureOrders();if(S.auto)autoDeliver();if(S.autoStory)autoOpenStory();renderAll();saveSoon()}

function sortBoard(){
  makeUndo('整列');const items=S.board.filter(id=>id&&!isGen(id)).sort((x,y)=>ITEMS[x].k.localeCompare(ITEMS[y].k)||levelOf(x)-levelOf(y));
  S.board=S.board.map(id=>isGen(id)?id:null);let j=0;for(let i=0;i<GRID;i++)if(!S.board[i]&&j<items.length)S.board[i]=items[j++];
  selected=null;hintPair=[];renderGame();saveSoon();say('同じ仲間どうしに整列したよ。');
}

function sellSelected(){if(selected===null){say('売るアイテムを選んでね。');return}const id=S.board[selected];if(!id||isGen(id)){say('これは売れないよ。');return}const value=Math.max(1,Math.floor((ITEMS[id].price||1)/2));if(levelOf(id)>=7&&!confirm(`${nameOf(id)} はLv${levelOf(id)}です。本当に ${value}コインで売りますか？`))return;makeUndo('売却');S.board[selected]=null;S.coins+=value;S.stats.sold++;selected=null;say(`🪙 ${nameOf(id)} を ${value}コインで売ったよ。`);sound('sell');restoreGenerators();renderAll();saveSoon()}

function findMergePair(){const map={};for(let i=0;i<S.board.length;i++){const id=S.board[i];if(!id||isGen(id)||!ITEMS[id].next)continue;if(map[id]!==undefined)return [map[id],i];map[id]=i}return null}

function showHint(){
  clearTimeout(hintTimer);const pair=findMergePair();
  hintPair=pair||S.board.map((id,i)=>isGen(id)?i:null).filter(i=>i!==null);
  say(pair?`${nameOf(S.board[pair[0]])}が2つ！ 光っているマスを重ねてね。`:emptyCells().length?'カフェか海辺のかごから材料を出してね。':'空きマスがないよ。注文を届けるか、いらない材料を売ってね。');
  renderGame();hintTimer=setTimeout(()=>{hintPair=[];if(view==='game')renderGame()},2500);
}

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
  makeUndo('物語');S.stars-=s.cost;S.story=i;if(s.coins)S.coins+=s.coins;if(s.item)addItem(s.item);
  toast(`📖 ${s.t} を開放！`);celebrate(12);sound('story');renderAll();saveSoon();
}

function repairShip(){
  const r=S.repair;
  if(r>=5){toast('🚢 リン号は完成しているよ！');return}
  const cost=REPAIR_COSTS[r];
  if(S.coins<cost){toast(`🪙 あと ${cost-S.coins}コイン 必要だよ`);haptic(40);return}
  makeUndo('修理');S.coins-=cost;S.repair++;
  toast(`🔧 ${REPAIR_MESSAGES[S.repair]}`);say(REPAIR_MESSAGES[S.repair]);celebrate(14);sound('repair');haptic([20,40,20]);
  renderAll();saveNow();openAlbum(S.repair);
}

function setView(v){
  if(!['opening','home','game','orders','story','book'].includes(v))v='home';
  cancelDrag();view=v;document.body.dataset.view=v;selected=null;hintPair=[];
  document.querySelectorAll('.screen').forEach(x=>x.classList.remove('on'));
  $('screen'+v[0].toUpperCase()+v.slice(1)).classList.add('on');
  $('nav').classList.toggle('hidden',v==='opening');
  document.querySelectorAll('#nav button').forEach(b=>(b.classList.toggle('active',b.dataset.go===v),b.setAttribute('aria-current',b.dataset.go===v?'page':'false')));
  renderAll();
  const screen=$('screen'+v[0].toUpperCase()+v.slice(1));if(screen)screen.scrollTop=0;requestAnimationFrame(fitBoard);
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
  $('repairTitle').textContent=r<5?REPAIR_TITLES[r+1]:'リン号、出航の準備完了！';
  $('repairSub').textContent=r>=5?'港のみんなと、ここまで来たね。':(S.coins>=cost?`修理 ${r}/5 ・ 修理を進められるよ`:`修理 ${r}/5 ・ あと ${cost-S.coins}コイン`);
  $('repairBar').style.width=(r/5*100)+'%';
  $('repairBtn').disabled=r>=5||S.coins<cost;
  $('repairBtn').textContent=r>=5?'🚢 完成':'🔧 '+cost;
  $('homeShipFallback').textContent='';
  setStageImage($('homeShipImage'),r);
  const ready=S.orders.filter(orderCan).length;
  $('homeOrderTitle').textContent=ready?`納品OK ${ready}件`:`注文 ${S.orders.length}件`;
  $('homeOrderSub').textContent=ready?(S.auto?'自動納品ON':'注文画面から届けよう'):'材料を合成してそろえよう';
  const discovered=Object.keys(ITEMS).filter(id=>S.book[id]).length;
  $('homeBookSub').textContent=`${discovered}/${Object.keys(ITEMS).length} 発見`;
  $('homeGuide').textContent=r<5?'リン号を直す材料、いっしょに集めよう！':'リン号がぴかぴか！ つぎは図鑑を完成させよう。';renderDaily();
}

function renderDaily(){
  $('dailyDate').textContent=S.daily.date.replaceAll('-',' / ');
  const list=$('dailyList');list.innerHTML='';
  S.daily.missions.forEach((m,i)=>{
    const done=m.progress>=m.goal,pct=Math.min(100,m.progress/m.goal*100);
    const el=document.createElement('div');el.className='mission'+(done?' ready':'');
    el.innerHTML=`<div class="missionRow"><div class="missionTitle">${m.icon} ${esc(m.title)}</div><div class="missionReward">🪙${m.rewardCoin} ⭐${m.rewardStar}</div></div>
      <div class="progress"><i style="width:${pct}%"></i></div>
      <div class="missionFoot"><span>${m.progress}/${m.goal}</span>${m.claimed?'<span>✅ 受取済み</span>':done?`<button class="primary" data-claim="${i}">🎁 受け取る</button>`:'<span>進行中</span>'}</div>`;
    list.appendChild(el);
  });
  $('dailyClear').textContent=S.daily.allClearClaimed?'🌟 全クリア済み':'3つクリアで⭐3';
}

function renderGame(){
  ensureOrders();const focused=document.activeElement?.closest?.('.cell')?.dataset.i;
  $('miniStats').innerHTML=miniStatsHtml();
  $('board').innerHTML=S.board.map((id,i)=>{
    const cls=['cell',!id?'empty':'',id&&isGen(id)?'gen':'',selected===i?'sel':'',hintPair.includes(i)?'hint':''].filter(Boolean).join(' ');
    return `<button class="${cls}" data-i="${i}" aria-label="${id?esc(nameOf(id))+' レベル'+levelOf(id):'空きマス '+(i+1)}">${id?`<div class="em">${emojiOf(id)}</div><div class="nm">${esc(nameOf(id))}</div>${isGen(id)?'<div class="tap">TAP</div>':`<div class="lv">Lv${levelOf(id)}</div>`}`:''}</button>`;
  }).join('');
  renderNextOrder();
  $('sell').disabled=selected===null||!S.board[selected]||isGen(S.board[selected]);
  $('autoGame').textContent=S.auto?'🤖 ON':'🤖 OFF';$('autoGame').className=S.auto?'good':'off';
  updateUndoButton();if(focused!==undefined)$('board').querySelector(`[data-i="${focused}"]`)?.focus({preventScroll:true});requestAnimationFrame(fitBoard);
}

function renderNextOrder(){
  const f=firstReadyOrder(),c=countBoard();
  const score=o=>o.wants.reduce((a,w)=>a+Math.max(0,w.n-(c[w.id]||0))*Math.pow(2,levelOf(w.id)-1),0);
  const o=f>=0?S.orders[f]:S.orders.reduce((best,x)=>!best||score(x)<score(best)?x:best,null);
  $('quickTop').disabled=f<0;
  $('nextOrderTitle').textContent=f>=0?'お届けの準備ができたよ':o?.title||'港の注文';
  $('nextOrderSub').textContent=o?`報酬：${o.coin}コイン ＋ 星${o.star}`:'材料を合成しよう';
  $('nextWants').innerHTML=o?o.wants.map(w=>`<span class="${(c[w.id]||0)>=w.n?'ok':''}">${emojiOf(w.id)} ${esc(nameOf(w.id))} ${c[w.id]||0}/${w.n}</span>`).join(''):'';
}

function renderOrders(){
  $('statsOrders').innerHTML=statsHtml();
  const c=countBoard();
  $('orders').innerHTML=S.orders.map((o,i)=>`<div class="order ${orderCan(o)?'ready':''}"><div class="ot"><span>${esc(o.title)}</span><span>🪙${o.coin} ⭐${o.star}</span></div>${o.wants.map(w=>`<div class="want ${(c[w.id]||0)>=w.n?'ok':'ng'}"><span>${emojiOf(w.id)} ${esc(nameOf(w.id))}</span><span>${c[w.id]||0}/${w.n}</span></div>`).join('')}<button class="${orderCan(o)?'primary':''}" data-order="${i}" ${orderCan(o)?'':'disabled'}>${orderCan(o)?'🚢 納品する':'まだ足りない'}</button></div>`).join('');
}

function renderStory(){
  $('statsStory').innerHTML=statsHtml();
  $('storyList').innerHTML=STORIES.map((s,i)=>{
    const open=i<=S.story,canOpen=i===S.story+1&&S.stars>=s.cost;
    return `<div class="storyCard ${open?'':'locked'}"><div class="ot"><span>${open?'📖':'🔒'} ${esc(s.t)}</span><span>⭐${s.cost}</span></div><div>${open?esc(s.x):'まだ開放されていません。'}</div><div class="storyMeta">${s.coins?`<span class="pill">報酬 🪙${s.coins}</span>`:''}${s.item?'<span class="pill">新しい屋台 🏵️</span>':''}</div>${canOpen?`<button class="primary" data-story="${i}">⭐ ${s.cost}で開放</button>`:''}</div>`;
  }).join('');
  renderAlbumStrip();
}

function renderAlbumStrip(){
  $('albumStrip').innerHTML=ALBUM.slice(0,S.repair+1).map((a,i)=>`<button class="albumThumb" data-album="${i}" aria-label="${esc(a.title)}を大きく見る"><img loading="lazy" decoding="async" src="${bestStagePath(i)}" alt="${esc(a.title)}"><span>${esc(a.title)}</span></button>`).join('');
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
  setToggle($('hapticSetting'),S.haptics,'ON','OFF');$('storageStatus').textContent=diskAvailable?'この端末に自動保存しています。':'保存できません。バックアップを保存してください。';
}

function setToggle(btn,on,onText,offText){btn.textContent=on?onText:offText;btn.className='toggle '+(on?'good':'off')}

function renderAll(){ensureDaily();ensureOrders();if(view==='home')renderHome();if(view==='game')renderGame();if(view==='orders')renderOrders();if(view==='story')renderStory();if(view==='book')renderBook();saveSoon()}

function say(t){if($('msg'))$('msg').textContent=t}

function toast(t){const el=$('toast');el.textContent=t;el.classList.add('on');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('on'),1800)}

function celebrate(n=8){
  if(reducedMotion())return;const box=$('celebrate'),icons=['✦','✧','✦','✧'];
  for(let i=0;i<Math.min(n,14);i++){const x=document.createElement('div');x.className='confetti';x.textContent=icons[i%4];x.style.left=Math.random()*100+'vw';x.style.setProperty('--x',(Math.random()*160-80)+'px');x.style.animationDelay=(Math.random()*.18)+'s';box.appendChild(x);setTimeout(()=>x.remove(),1500)}
}

function haptic(pattern){if(!S.haptics||!navigator.vibrate)return;try{navigator.vibrate(pattern)}catch(_e){}}

function sound(type){
  if(!S.sound)return;
  try{audioCtx=audioCtx||new (window.AudioContext||window.webkitAudioContext)();if(audioCtx.state==='suspended')audioCtx.resume().catch(()=>{});const map={pop:[420,.05],merge:[620,.08],deliver:[760,.12],reward:[880,.12],level:[980,.15],story:[700,.14],repair:[520,.14],sell:[330,.06]};const [freq,dur]=map[type]||[500,.06];const o=audioCtx.createOscillator(),g=audioCtx.createGain();o.type='sine';o.frequency.value=freq;g.gain.setValueAtTime(.0001,audioCtx.currentTime);g.gain.exponentialRampToValueAtTime(.08,audioCtx.currentTime+.01);g.gain.exponentialRampToValueAtTime(.0001,audioCtx.currentTime+dur);o.connect(g).connect(audioCtx.destination);o.start();o.stop(audioCtx.currentTime+dur+.02)}catch(_e){}
}

function bestStagePath(stage){return `assets/art-v1/repair-${int(stage,0,5)}.jpg`}

function setStageImage(img,stage){
  const path=bestStagePath(stage);if(img.dataset.src===path&&img.complete&&img.naturalWidth>0)return;
  img.dataset.src=path;img.alt=REPAIR_TITLES[int(stage,0,5)];
  img.onload=()=>{img.style.display='block';if(img.id==='homeShipImage')$('homeShipFallback').hidden=true};
  img.onerror=()=>{img.style.display='none';img.dataset.src='';if(img.id==='homeShipImage'){$('homeShipFallback').hidden=false;$('homeShipFallback').textContent='画像を読み込めません。港を開き直してください。'}};
  img.src=path;if(img.complete&&img.naturalWidth>0)img.onload();
}

function openAlbum(index=0){
  const viewer=$('viewer');albumIndex=int(index,0,S.repair);const item=ALBUM[albumIndex];
  if(!viewer.classList.contains('on'))albumReturnFocus=document.activeElement;
  $('viewerTitle').textContent=item.title;$('viewerText').textContent=item.text;
  const img=$('viewerImg');img.style.display='block';img.alt=item.title;img.onload=()=>img.style.display='block';img.onerror=()=>{$('viewerText').textContent='画像を読み込めませんでした。閉じて、もう一度開いてください。';img.style.display='none'};img.src=bestStagePath(albumIndex);
  $('viewerThumbs').innerHTML=ALBUM.slice(0,S.repair+1).map((it,i)=>`<button class="viewerThumb ${i===albumIndex?'primary':''}" data-view-stage="${i}" aria-label="${esc(it.title)}"><img loading="lazy" src="${bestStagePath(i)}" alt=""><div>${esc(it.title)}</div></button>`).join('');
  viewer.classList.add('on');viewer.setAttribute('aria-hidden','false');document.querySelector('.app').inert=true;$('nav').inert=true;$('viewerClose').focus({preventScroll:true});
}

function exportSave(){
  saveNow();const bytes=new TextEncoder().encode(JSON.stringify(S));let binary='';for(const n of bytes)binary+=String.fromCharCode(n);const code='RH10-'+btoa(binary);
  if(navigator.clipboard?.writeText)navigator.clipboard.writeText(code).then(()=>toast('バックアップコードをコピーしました')).catch(()=>prompt('このコードを保存してください',code));else prompt('このコードを保存してください',code);
}

function importSave(){
  const code=prompt('バックアップコード、または保存したJSONを貼り付けてください');if(!code)return;
  try{
    if(code.length>2000000)throw Error('too large');
    const text=code.trim().startsWith('{')?code:new TextDecoder('utf-8',{fatal:true}).decode(Uint8Array.from(atob(code.trim().replace(/^RH10-/,'')),c=>c.charCodeAt(0)));
    const value=JSON.parse(text);if(!value||!Array.isArray(value.board)||value.board.length!==GRID||value.board.some(id=>id!==null&&!hasItem(id)))throw Error('invalid');
    if(!confirm('現在の進行状況を、このバックアップで置き換えますか？'))return;
    const old=JSON.stringify(S);normalize(value);undoState=old;undoLabel='復元';selected=null;renderAll();saveNow();toast('バックアップを復元しました');
  }catch(_e){alert('バックアップを読み込めませんでした。進行状況は変更していません。')}
}

function resetGame(){
  if(!confirm('進行状況を最初に戻しますか？ 必要な場合は先にバックアップを保存してください。'))return;
  if(!confirm('本当に最初から始めますか？'))return;
  cancelDrag();closeAlbum();clearTimeout(saveTimer);clearTimeout(hintTimer);clearTimeout(comboTimer);
  S=freshState();ensureDaily();ensureOrders();undoState=null;selected=null;combo=0;lastMergeAt=0;saveNow();setView('opening');toast('新しい冒険を始めよう');
}

function restoreGenerators(){
  const required=['gen_cafe','gen_sea',...(S.story>=2?['gen_gift']:[])];
  for(const id of required)if(!S.board.includes(id)){const empty=S.board.indexOf(null);if(empty>=0){S.board[empty]=id;S.book[id]=1}}
}
function mergeEffect(i){
  if(reducedMotion())return;const cell=$('board').querySelector(`[data-i="${i}"]`);if(!cell)return;
  cell.classList.add('merge-hit');setTimeout(()=>cell.classList.remove('merge-hit'),380);
}
function fitBoard(){
  if(view!=='game')return;const box=document.querySelector('.boardBox');
  const size=Math.max(1,Math.floor(Math.min(box.clientWidth,box.clientHeight,540)));
  $('board').style.width=size+'px';$('board').style.height=size+'px';$('board').style.setProperty('--piece-size',Math.max(14,Math.min(39,size*.085))+'px');
}
function closeAlbum(){
  const viewer=$('viewer');if(!viewer)return;viewer.classList.remove('on');viewer.setAttribute('aria-hidden','true');document.querySelector('.app').inert=false;$('nav').inert=false;
  if(albumReturnFocus?.isConnected)albumReturnFocus.focus({preventScroll:true});albumReturnFocus=null;
}
function downloadSave(){
  saveNow();const url=URL.createObjectURL(new Blob([JSON.stringify(S,null,2)],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download='rin-harbor-save-'+localDateString()+'.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);
}


/* Pointer, keyboard and screen-reader input share the same game actions. */
function cancelDrag(){
  if(drag?.ghost)drag.ghost.remove();drag=null;
  document.querySelectorAll('.dragSource,.dropTarget').forEach(e=>e.classList.remove('dragSource','dropTarget'));
}
function targetFromPoint(x,y){const c=document.elementFromPoint(x,y)?.closest?.('.cell');return c&&$('board').contains(c)?Number(c.dataset.i):null}
function markDrag(){
  document.querySelectorAll('.dragSource,.dropTarget').forEach(e=>e.classList.remove('dragSource','dropTarget'));
  if(!drag?.active)return;
  $('board').querySelector(`[data-i="${drag.from}"]`)?.classList.add('dragSource');
  const to=drag.target,source=S.board[drag.from],dest=to===null?null:S.board[to];
  if(to!==null&&to!==drag.from&&(!dest||(dest===source&&ITEMS[source]?.next)))$('board').querySelector(`[data-i="${to}"]`)?.classList.add('dropTarget');
}
$('board').addEventListener('pointerdown',e=>{
  const cell=e.target.closest('.cell');if(!cell||e.isPrimary===false||e.button!==0||drag)return;
  e.preventDefault();drag={from:Number(cell.dataset.i),pointerId:e.pointerId,x:e.clientX,y:e.clientY,active:false,target:null,ghost:null};
  try{$('board').setPointerCapture(e.pointerId)}catch(_e){}
},{passive:false});
$('board').addEventListener('pointermove',e=>{
  if(!drag||drag.pointerId!==e.pointerId)return;e.preventDefault();
  const id=S.board[drag.from];
  if(!drag.active&&id&&!isGen(id)&&Math.hypot(e.clientX-drag.x,e.clientY-drag.y)>9){
    drag.active=true;drag.ghost=document.createElement('div');drag.ghost.className='dragGhost';drag.ghost.textContent=emojiOf(id);document.body.append(drag.ghost);
  }
  if(drag.active){drag.target=targetFromPoint(e.clientX,e.clientY);drag.ghost.style.transform=`translate(${e.clientX-29}px,${e.clientY-29}px)`;markDrag()}
},{passive:false});
$('board').addEventListener('pointerup',e=>{
  if(!drag||drag.pointerId!==e.pointerId)return;e.preventDefault();
  const state=drag,target=targetFromPoint(e.clientX,e.clientY),moved=Math.hypot(e.clientX-state.x,e.clientY-state.y)>9;cancelDrag();
  if(state.active){if(target!==null&&target!==state.from)moveOrMerge(state.from,target)}
  else if(!moved&&target===state.from)cellTap(state.from);
},{passive:false});
$('board').addEventListener('pointercancel',cancelDrag);
$('board').addEventListener('lostpointercapture',cancelDrag);
$('board').addEventListener('click',e=>{const cell=e.target.closest('.cell');if(cell&&e.detail===0&&!e.pointerType)cellTap(Number(cell.dataset.i))});
$('board').addEventListener('keydown',e=>{
  const cell=e.target.closest('.cell');if(!cell)return;const offsets={ArrowLeft:-1,ArrowRight:1,ArrowUp:-6,ArrowDown:6};
  if(e.key in offsets){e.preventDefault();const n=Math.max(0,Math.min(35,Number(cell.dataset.i)+offsets[e.key]));$('board').querySelector(`[data-i="${n}"]`)?.focus()}
  if(e.key==='Escape'){selected=null;renderGame()}
});

document.body.addEventListener('click',e=>{
  const button=e.target.closest('button');if(button?.disabled)return;
  const go=e.target.closest('[data-go]');if(go){setView(go.dataset.go);return}
  const claim=e.target.closest('[data-claim]');if(claim){claimMission(Number(claim.dataset.claim));return}
  const order=e.target.closest('[data-order]');if(order){completeOrder(Number(order.dataset.order),false);renderAll();saveSoon();return}
  const story=e.target.closest('[data-story]');if(story){openStory(Number(story.dataset.story));return}
  const album=e.target.closest('[data-album]');if(album){openAlbum(Number(album.dataset.album));return}
  const stage=e.target.closest('[data-view-stage]');if(stage)openAlbum(Number(stage.dataset.viewStage));
});
function bind(id,fn){$(id).addEventListener('click',fn)}
bind('startHome',()=>setView('home'));bind('startGame',()=>setView('game'));
bind('quickTop',quickDeliver);
bind('quickOrders',()=>{const n=S.orders.filter(orderCan).length;toast(n?`今、${n}件の注文を届けられるよ。`:'材料を合成して、お客さんのお願いをかなえよう。')});
function toggleSetting(key){
  makeUndo('設定');S[key]=!S[key];
  if(key==='auto'&&S.auto)autoDeliver();if(key==='autoStory'&&S.autoStory)autoOpenStory();
  if(key==='sound'&&S.sound)sound('reward');if(key==='haptics'&&S.haptics)haptic(20);
  renderAll();saveSoon();
}
bind('autoGame',()=>toggleSetting('auto'));bind('autoSetting',()=>toggleSetting('auto'));
bind('autoStorySetting',()=>toggleSetting('autoStory'));bind('soundSetting',()=>toggleSetting('sound'));bind('hapticSetting',()=>toggleSetting('haptics'));
bind('hint',showHint);bind('undo',undo);bind('sort',sortBoard);bind('sell',sellSelected);
bind('clear',()=>{selected=null;hintPair=[];renderGame();say('カフェや海辺のかごから材料を出してね。')});
bind('repairBtn',repairShip);bind('openAlbum',()=>openAlbum(S.repair));bind('viewerClose',closeAlbum);
$('viewer').addEventListener('click',e=>{if(e.target===$('viewer'))closeAlbum()});
$('viewer').addEventListener('keydown',e=>{
  if(e.key==='Escape'){e.preventDefault();closeAlbum();return}
  if(e.key==='ArrowLeft'){e.preventDefault();openAlbum(Math.max(0,albumIndex-1));return}
  if(e.key==='ArrowRight'){e.preventDefault();openAlbum(Math.min(S.repair,albumIndex+1));return}
  if(e.key==='Tab'){
    const buttons=[...$('viewer').querySelectorAll('button:not(:disabled)')],first=buttons[0],last=buttons.at(-1);
    if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}
    else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}
  }
});
bind('exportSave',exportSave);bind('downloadSave',downloadSave);bind('importSave',importSave);bind('reset',resetGame);
$('openingImage').onload=()=>{$('openingFallback').hidden=true};
$('openingImage').onerror=()=>{$('openingImage').style.display='none';$('openingFallback').hidden=false;$('openingFallback').textContent='港の絵を読み込めませんでした。再読み込みしてください。'};
if($('openingImage').complete&&$('openingImage').naturalWidth>0)$('openingImage').onload();
window.addEventListener('pagehide',()=>{cancelDrag();saveNow()});
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden'){cancelDrag();saveNow()}else if(S){ensureDaily();renderAll()}});
window.addEventListener('resize',()=>requestAnimationFrame(fitBoard));
if(window.visualViewport)visualViewport.addEventListener('resize',()=>requestAnimationFrame(fitBoard));
if(window.ResizeObserver)new ResizeObserver(fitBoard).observe(document.querySelector('.boardBox'));

try{load();setView('opening');if(!diskAvailable)toast('保存できない設定です。バックアップを残してください。')}
catch(error){$('openingFallback').hidden=false;$('openingFallback').textContent='起動に失敗しました。保存データは削除せず、ページを開き直してください。';console.error('Rin Harbor startup failed',error)}

async function registerOffline(){
  const status=$('offlineStatus');
  if(!('serviceWorker' in navigator)||!/^https?:$/.test(location.protocol)){status.textContent='オフライン起動は公開ページで利用できます。';return}
  try{
    const registration=await navigator.serviceWorker.register('./sw.js',{updateViaCache:'none'});
    registration.update().catch(()=>{});
    const ready=await navigator.serviceWorker.ready;
    const channel=new MessageChannel();channel.port1.onmessage=e=>{if(e.data?.version===RELEASE)status.textContent='絵もゲームも保存済み。通信なしで遊べます。'};
    ready.active?.postMessage({type:'READY'},[channel.port2]);
    navigator.serviceWorker.addEventListener('controllerchange',()=>{status.textContent='新しいバージョンを保存しました。次回も続きから遊べます。'});
  }catch(_e){status.textContent='オフライン保存は未完了です。接続中はそのまま遊べます。'}
}
registerOffline();
