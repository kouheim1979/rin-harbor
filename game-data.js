'use strict';

const $=id=>document.getElementById(id);
const GRID=36, MAX_ITEM_LEVEL=10, ORDER_TARGET=8, SAVE_KEY='rin_harbor_save_v10';
const OLD_KEYS=['rin_harbor_save_v9','rin_harbor_save_v8','rin_harbor_save_v7','rin_harbor_save_v6','rin_harbor_save_v5'];
let S=null, selected=null, view='opening', saveTimer=null, drag=null, undoState=null, undoLabel='', hintPair=[], combo=0, lastMergeAt=0, toastTimer=null, audioCtx=null;

window.addEventListener('gesturestart',e=>e.preventDefault());

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

const isGen=id=>!!(ITEMS[id]&&ITEMS[id].k==='gen');
const nameOf=id=>ITEMS[id]?.n||'不明';
const emojiOf=id=>ITEMS[id]?.e||'❓';
const levelOf=id=>ITEMS[id]?.l||0;
const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

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
