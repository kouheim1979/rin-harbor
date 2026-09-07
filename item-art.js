/* Resolution-independent, original nautical item artwork. No fonts or emoji needed. */
'use strict';
function gameIcon(name){
 const paths={anchor:'<circle cx="12" cy="5" r="2"/><path d="M12 7v14M7 11h10M3 15c0 8 18 8 18 0M3 15l-2 3m2-3 3 1m15-1 2 3m-2-3-3 1"/>',star:'<path d="m12 2 3.1 6.3 7 .9-5.1 5 1.2 7-6.2-3.3-6.2 3.3 1.2-7L2 9.2l6.9-.9Z"/>',compass:'<circle cx="12" cy="12" r="9"/><path d="m16 8-2 6-6 2 2-6Z"/>',ship:'<path d="M3 15h18l-3 5H6zM8 15V9h8v6M12 9V3l6 5h-6M2 22q3-2 5 0 3-2 5 0 3-2 5 0 3-2 5 0"/>',book:'<path d="M3 4q5-1 9 2 4-3 9-2v16q-5-1-9 2-4-3-9-2ZM12 6v16"/>',grid:'<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><path d="M17.5 14v7M14 17.5h7"/>',gem:'<path d="m2 9 5-6h10l5 6-10 13ZM2 9h20M7 3l5 19 5-19"/>',arrow:'<path d="M4 12h16m-6-6 6 6-6 6"/>',coin:'<circle cx="12" cy="12" r="9"/><path d="M14.5 8.5a4 4 0 1 0 0 7"/>',check:'<path d="m4 12 5 5L20 6"/>',lock:'<rect x="5" y="10" width="14" height="11" rx="3"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 4v3"/>'};
 return `<svg class="uiIcon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name]||paths.compass}</svg>`;
}
function itemArt(id){
 const kind=id.replace(/\d+$/,''),n=Number(id.match(/\d+$/)?.[0]||1);
 const p=(d,fill,extra='')=>`<path d="${d}" fill="${fill}" ${extra}/>`;
 const c=(x,y,r,fill)=>`<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}"/>`;
 const r=(x,y,w,h,rad,fill)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rad}" fill="${fill}"/>`;
 let a='',base='#f6bf65',detail='#de7253';
 if(kind.startsWith('gen_')){
  const t=kind==='gen_cafe'?'#f18d75':kind==='gen_sea'?'#57b8b3':'#a291c7';
  a=r(14,30,40,28,4,'#fae6bc')+r(12,28,44,7,2,'#866957')+r(18,10,4,47,1,'#876957')+r(46,10,4,47,1,'#876957')+p('M10 13h48l5 15H5Z',t)+p('M17 13h8l-2 15H13Zm18 0h8l4 15H37Z','#fff5db')+r(18,39,11,13,3,t)+r(35,39,15,13,3,'#73998d')+p('M10 60h48','#9c7757','stroke="#9c7757" stroke-width="3"');
 }else if(kind==='drink'){
  if(n===1)a=p('M31 19C8 8 10 45 25 47c17 2 23-22 6-28Z','#9f6045')+p('M31 19Q18 28 25 47','none','stroke="#efd0a2" stroke-width="3"')+p('M49 31c-16-7-24 15-12 24s32-11 12-24Z','#bc8258')+p('M49 31q-15 7-12 24','none','stroke="#f7d8a8" stroke-width="3"');
  else if(n<5||n===10){base=n===3?'#fae3bd':n===4?'#64aaa1':n===10?'#829fba':'#f7f1dc';a=p('M47 29c21-4 20 24-1 20','none','stroke="#4f9295" stroke-width="6"')+p('M15 27h33v17Q48 58 32 58T15 44Z',base)+p('M15 28q17 8 33 0','#996c4b')+p('M24 15q-6 5 0 9m10-14q-7 8 0 13','none','stroke="#adc5bd" stroke-width="3"')+p('M10 59h44','none','stroke="#bbd2c7" stroke-width="4"');}
  else {base=['#dbab7c','#eab798','#eae297','#ffc766','#dc9fbe'][n-5];a=p('M18 23h32l-4 36H22Z',base)+p('M20 28h28l-1 10H21Z','#fff4df')+p('M33 39V9h13','none','stroke="#4eaaa9" stroke-width="4"');if(n===5)for(let x=27;x<46;x+=6)a+=c(x,50+(x%3),2,'#705f64');if(n===6||n===9)a+=c(31,22,12,'#fff5df')+c(37,10,4,'#d86976');if(n>=7)a+=c(49,26,10,'#ffce68')+c(49,26,7,'#ffedb4');}
 }else if(kind==='dessert'){
  if(n===1){a=c(33,34,23,'#e7b170')+c(33,32,20,'#f3c987');for(const [x,y] of [[24,22],[39,21],[31,34],[45,38],[22,44]])a+=c(x,y,3,'#8d654e');}
  else if(n===2){a=c(33,35,24,'#d9a269')+p('M10 30C10 7 54 4 57 29q-3 13-9 5-7 12-13 4-8 9-11-3-13 3-14-5Z','#eea2b4')+c(33,30,8,'#ffefd0')+p('m17 25 5-2m18-8 2 4m7 5 5 1','none','stroke="#fff5d3" stroke-width="3"');}
  else if(n===3||n===6||n===9){a=p('M11 36 37 20l22 15v22H11Z','#f2ce92')+p('M11 43h48v7H11Z','#ed9da7')+p('M11 30 39 15l20 16v8H11Z','#fff0dd')+c(40,16,6,'#e57881')+p('m39 10 5-4','none','stroke="#6fa28d" stroke-width="3"');}
  else if(n===5){a=p('M21 20h24l8 33q-20 12-40 0Z','#f4d491')+p('M21 20q12-10 24 0v9q-12 8-24 0Z','#bb7d53')+p('M10 57h45','none','stroke="#9cc7bc" stroke-width="4"');}
  else {a=p('M17 37h34L36 60h-5Z','#e6b783')+c(25,29,11,'#f0c0ca')+c(43,29,11,'#c6ddd0')+c(33,17,12,'#fff1d5')+c(36,6,4,'#e17377');}
 }else if(kind==='shell'){
  if(n===1||n===2){a=p('M33 54C1 40 5 17 17 18q6-16 16-7 14-9 18 8 19 0 6 22L40 54Z',n===1?'#f1baac':'#d4bce1')+p('M33 49 18 23m17 26V16m4 32 12-25','none','stroke="#fff0d9" stroke-width="3"')+(n===2?c(34,39,10,'#fffdf0'):'');}
  else if(n===3||n===5||n===9){a=p('M13 23 24 10h22l13 15L34 59Z','#6bccc5')+p('M24 10 21 25l13 34 11-34 1-15','#b8eee0')+p('M13 23h46M24 10l21 15','none','stroke="#3eaaa9" stroke-width="2"');}
  else if(n===4||n===10){a=r(9,25,49,32,5,'#c48c5b')+p('M9 28v-6q0-16 24-16t25 16v6Z','#edc584')+r(18,11,6,44,1,'#efcf84')+r(44,11,6,44,1,'#efcf84')+r(30,27,10,14,2,'#f5e0a0')+c(35,33,2,'#8d6b55');}
  else if(n===8){a=p('M13 49 7 19l17 12 10-23 12 23 14-13-6 32Z','#eccb7d')+r(13,48,41,9,2,'#d5a55b')+c(33,38,5,'#76b6c4')+c(8,18,3,'#caa678')+c(34,8,3,'#caa678')+c(60,18,3,'#caa678');}
  else {a=p('M15 22q-1 30 19 32 20-2 18-32','none','stroke="#eac58d" stroke-width="7"')+p('m34 40 11 10-11 14-11-14Z','#86bbc6')+c(13,20,4,'#edd7ac')+c(53,20,4,'#edd7ac');}
 }else if(kind==='fish'){
  if(n===1){a=p('M17 34C26 6 52 12 58 33 48 56 26 59 17 36L6 47V23Z','#75b7c7')+p('m30 21 3-13 13 11','#529aaf')+c(48,30,3,'#325a6b')+c(49,29,1,'#fff');}
  else {a=p('M4 43q29 32 59 0Z','#bedacf')+p('M4 43q28-15 59 0-28 15-59 0Z','#f7f0d8')+p('M15 38q16-22 38 0Z',n===5||n===6?'#ee9c85':'#d8b377')+p('m22 35 6-7m3 10 7-10m4 12 5-9','none','stroke="#aa7354" stroke-width="2"')+p('M40 42q13-18 16 1Z','#82b79e');}
 }else if(kind==='toy'){
  if(n===1){a=p('M29 31C8 3 1 26 10 48l20-9Zm9 0C58 3 67 26 58 48l-20-9Z','#ed9aa8')+p('m29 34-8 25 13-8 13 8-10-25','#d7748a')+r(27,27,14,16,6,'#f4b9be');}
  else if(n===2){a=c(19,16,9,'#c7a17b')+c(48,16,9,'#c7a17b')+r(18,37,31,23,11,'#dbb48a')+c(33,28,22,'#dfbd94')+c(25,26,2,'#685951')+c(43,26,2,'#685951')+c(34,35,9,'#f7e4c4')+c(34,32,3,'#695851')+p('M25 47h17','none','stroke="#cf8e9c" stroke-width="6"');}
  else if(n===3){a=r(17,15,33,33,7,'#648d9c')+r(17,35,33,9,1,'#e9bb81')+p('M6 48h56','none','stroke="#507384" stroke-width="9"');}
  else if(n===5){a=r(10,27,48,30,6,'#d4a4af')+p('M23 27V19q10-14 20 0v8','none','stroke="#80677a" stroke-width="5"')+r(28,26,12,12,3,'#f5ddaa');}
  else if(n===6){a=p('M22 8 33 16 44 8l7 15-11 5 17 32H10l17-32-11-5Z','#a2bbcf')+p('M26 30h15','none','stroke="#fff4de" stroke-width="5"');}
  else if(n===9){a=r(9,29,49,29,4,'#c6b4d5')+r(6,22,55,12,3,'#dacae2')+r(29,23,9,35,0,'#f4d499')+p('M32 23q-26 0-19-11 7-8 19 11Zm2 0q25-1 18-12-7-7-18 12Z','#f0bcb8');}
  else {a=p('m33 5 8 16 19 3-14 14 3 20-16-9-17 9 3-20L5 24l19-3Z','#f0cf82')+p('m33 13 6 13 14 1-20 20Z','#fff0b7');if(n===7)a=p('m22 51-7 12','none','stroke="#8aabb5" stroke-width="5"')+a;}
 }
 return `<svg class="itemArt" data-art="${id}" viewBox="0 0 68 68" aria-hidden="true"><ellipse cx="34" cy="61" rx="22" ry="3" fill="#255968" opacity=".12"/><g stroke="#4c666b" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round">${a}</g>${n>=7?p('m58 4 1.5 4.5L64 10l-4.5 1.5L58 16l-1.5-4.5L52 10l4.5-1.5Z','#e5b860'):''}</svg>`;
}
