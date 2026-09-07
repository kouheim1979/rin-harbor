'use strict';
/* Strong level differentiation for every merge item. Keeps the original illustration,
   then adds a different frame, palette cue and silhouette marker for each level. */
(()=>{
  const original=itemArt;
  const levelColors=['#80b8a9','#6fa9c8','#d5a35c','#c88776','#8f9ec9','#a889c3','#d4879d','#e1b650','#72a9a2','#e0a83e'];
  const accents=['#e8f5ec','#e6f1f8','#fff1d1','#fde4dc','#e8eaf8','#efe5f7','#f9e1ea','#fff1bd','#dff1ed','#fff0b2'];
  function deco(n,color,accent){
    const common=`fill="${accent}" stroke="${color}" stroke-width="1.8"`;
    switch(n){
      case 1:return `<path d="M8 14h10" stroke="${color}" stroke-width="3" stroke-linecap="round" opacity=".65"/>`;
      case 2:return `<circle cx="10" cy="12" r="4" ${common}/><circle cx="58" cy="12" r="4" ${common}/>`;
      case 3:return `<path d="M7 16 16 7l5 5-9 9Z" ${common}/><path d="m61 16-9-9-5 5 9 9Z" ${common}/>`;
      case 4:return `<path d="M8 11h14l-5 6 5 6H8Z" ${common}/><path d="M60 11H46l5 6-5 6h14Z" ${common}/>`;
      case 5:return `<path d="m10 15 5-8 5 8-5 8Z" ${common}/><path d="m58 15-5-8-5 8 5 8Z" ${common}/>`;
      case 6:return `<path d="M7 19 10 7l7 6 7-7 4 13Z" ${common}/><path d="M61 19 58 7l-7 6-7-7-4 13Z" ${common}/>`;
      case 7:return `<g fill="${color}"><path d="m11 7 2 4 4 2-4 2-2 4-2-4-4-2 4-2Z"/><path d="m57 7 2 4 4 2-4 2-2 4-2-4-4-2 4-2Z"/><circle cx="20" cy="7" r="2"/><circle cx="48" cy="7" r="2"/></g>`;
      case 8:return `<path d="M7 24Q5 9 20 5M61 24Q63 9 48 5" fill="none" stroke="${color}" stroke-width="3"/><g fill="${accent}" stroke="${color}"><circle cx="10" cy="14" r="3"/><circle cx="15" cy="9" r="3"/><circle cx="58" cy="14" r="3"/><circle cx="53" cy="9" r="3"/></g>`;
      case 9:return `<path d="m13 4 3 7 7 3-7 3-3 7-3-7-7-3 7-3Zm42 0 3 7 7 3-7 3-3 7-3-7-7-3 7-3Z" ${common}/>`;
      default:return `<circle cx="34" cy="34" r="31" fill="none" stroke="#e3b13f" stroke-width="3" stroke-dasharray="5 4"/><path d="m10 13 4-9 4 9 9 4-9 4-4 9-4-9-9-4Zm48 0 4-9 4 9 9 4-9 4-4 9-4-9-9-4Z" fill="#f4c95d" stroke="#b88628" stroke-width="1"/>`;
    }
  }
  itemArt=function(id){
    const base=original(id);
    const n=Number(id.match(/\d+$/)?.[0]||0);
    if(!n||isGen(id))return base;
    const color=levelColors[n-1],accent=accents[n-1];
    const marker=`<g class="levelArt levelArt${n}" opacity=".98">${deco(n,color,accent)}</g>`;
    return base.replace(/(<svg[^>]*>)/,`$1${marker}`);
  };
})();
