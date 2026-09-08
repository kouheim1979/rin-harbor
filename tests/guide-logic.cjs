'use strict';
// Deterministic planning and cached-video contracts, without browser dependencies.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const root=path.join(__dirname,'..');
const code=fs.readFileSync(path.join(root,'game.js'),'utf8');
const ctx=vm.createContext({setTimeout:()=>0,clearTimeout:()=>{}});
vm.runInContext(code.slice(0,code.indexOf('/* Pointer, keyboard')),ctx);
const run=s=>vm.runInContext(s,ctx);
const read=s=>JSON.parse(run('JSON.stringify('+s+')'));
let checks=0;
function check(name,actual,expected){assert.deepEqual(actual,expected,name);checks++;}
function fixture(items,wants,warehouse={}){
  run(`S=freshState();S.board=Array(36).fill(null);S.board[0]='gen_cafe';S.board[5]='gen_sea';
    ${JSON.stringify(items)}.forEach((id,i)=>S.board[i+6]=id);
    S.warehouse=${JSON.stringify(warehouse)};S.orders=[{title:'test',wants:${JSON.stringify(wants)},coin:20,star:1,xp:1}];guidedOrder=null;`);
}
fixture(['fish1','fish1','shell1','shell1'],[{id:'shell2',n:1}]);
check('Prefer an order ingredient over the first unrelated pair',read('orderGuidePlan(S.orders[0]).pairs'),[[8,9]]);
check('Count the actual next merge',read('orderGuidePlan(S.orders[0]).merges'),1);
check('Recognize all base material already on board',read('orderGuidePlan(S.orders[0]).missingBase'),0);
fixture(['drink2','drink2','drink1','drink1'],[{id:'drink2',n:1},{id:'drink3',n:1}]);
check('Protect the lower-level exact requirement',read('orderGuidePlan(S.orders[0]).pairs'),[[8,9]]);
check('Plan two remaining merges without inventing material',read('orderGuidePlan(S.orders[0]).merges'),2);
const before=run('JSON.stringify(S)');
run('orderGuidePlan(S.orders[0]);nextGuideOrder()');
check('Planning never changes a save',run('JSON.stringify(S)'),before);
fixture(['drink2','drink2'],[{id:'drink2',n:1},{id:'drink2',n:2}]);
check('Aggregate duplicate import requirements',read('orderGuidePlan(S.orders[0]).needs'),{drink2:3});
check('Never merge two already needed finished items',read('orderGuidePlan(S.orders[0]).pairs'),[]);
fixture([], [{id:'shell3',n:1}], {shell3:1,shell2:2,drink10:1});
check('Suggest only useful warehouse items, highest first',read('orderGuidePlan(S.orders[0]).stored'),['shell3','shell2']);
check('Warehouse is never counted as board inventory',read('orderGuidePlan(S.orders[0]).missingBase'),4);
check('Suggest the correct available generator',read('orderGuidePlan(S.orders[0]).sources'),[5]);
fixture([], [{id:'toy2',n:1}]);
check('Do not suggest a locked generator',read('orderGuidePlan(S.orders[0]).sources'),[]);
fixture([], [{id:'drink1',n:2}]);
check('Level-one requirements terminate correctly',read('orderGuidePlan(S.orders[0]).missingBase'),2);
fixture([], [{id:'drink10',n:4}]);
check('Level-ten quantities stay exact',read('orderGuidePlan(S.orders[0]).missingBase'),2048);
check('Level-ten merge count stays exact',read('orderGuidePlan(S.orders[0]).merges'),2044);
fixture(['drink2','drink2'],[{id:'shell2',n:1}]);
run("S.orders.push({title:'near',wants:[{id:'drink3',n:1}],coin:40,star:1,xp:1})");
check('Nearest order uses intermediate items',run('nextGuideOrder().title'),'near');
run('guidedOrder=S.orders[0]');
check('Chosen order stays selected',run('nextGuideOrder().title'),'test');
run('S.orders.shift()');
check('Replaced or delivered order releases its guide',run('nextGuideOrder().title'),'near');
check('No stale reference remains',run('guidedOrder===null'),true);
check('Existing save key stays unchanged',run('SAVE_KEY'),'rin_harbor_save_v10');
check('All original item IDs remain',run('Object.keys(ITEMS).length'),53);

async function videoRanges(){
  const sw=vm.createContext({URL,Response,Headers,Request,AbortController,setTimeout,clearTimeout,self:{location:{href:'https://example.test/rin-harbor/sw.js'},addEventListener(){}}});
  vm.runInContext(fs.readFileSync(path.join(root,'sw.js'),'utf8'),sw);
  const bytes=fs.readFileSync(path.join(root,'assets/video/repair-1.mp4'));
  const cache={match:async()=>new Response(bytes,{headers:{'Content-Type':'video/mp4'}})};
  const url='https://example.test/rin-harbor/assets/video/repair-1.mp4';
  for(const [range,start,end] of [['bytes=0-1023',0,1023],['bytes=1024-',1024,bytes.length-1],['bytes=-128',bytes.length-128,bytes.length-1],['bytes=0-9999999',0,bytes.length-1]]){
    const response=await sw.cachedRangeResponse(cache,new Request(url,{headers:{Range:range}}));
    check(range+' is 206',response.status,206);
    check(range+' exact byte slice',Buffer.from(await response.arrayBuffer()),bytes.subarray(start,end+1));
    check(range+' content range',response.headers.get('content-range'),`bytes ${start}-${end}/${bytes.length}`);
    check(range+' content length',response.headers.get('content-length'),String(end-start+1));
    check(range+' accepts bytes',response.headers.get('accept-ranges'),'bytes');
    check(range+' mp4 mime type',response.headers.get('content-type'),'video/mp4');
  }
  const invalid=await sw.cachedRangeResponse(cache,new Request(url,{headers:{Range:'bytes=99999999-'}}));
  check('Unsatisfiable byte range is 416',invalid.status,416);
  check('416 includes full size',invalid.headers.get('content-range'),`bytes */${bytes.length}`);
}
videoRanges().then(()=>console.log(`GUIDE LOGIC PASS: ${checks} checks`)).catch(error=>{console.error(error);process.exitCode=1});
