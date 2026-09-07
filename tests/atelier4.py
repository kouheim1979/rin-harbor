"""User-facing regression gates. Disposable browsers only, never player data."""
import hashlib, itertools, json, os, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1]
URL=os.environ.get('BASE_URL','http://127.0.0.1:8765/').rstrip('/')+'/'
OUT=Path(os.environ.get('RESULT_DIR','test-results'))/'atelier4';OUT.mkdir(parents=True,exist_ok=True)
RESULTS=[]
def check(name,ok,detail=''):
    if not ok:raise AssertionError(f'{name}: {detail}')
    RESULTS.append({'test':name,'result':'passed'})
def fetch(name):
    with urllib.request.urlopen(URL+name,timeout=45) as r:return r.read()
def visible(page,sel):
    b=page.locator(sel).bounding_box()
    return bool(b and b['width']>0 and b['height']>0 and b['x']>=-1 and b['y']>=-1 and b['x']+b['width']<=page.viewport_size['width']+1 and b['y']+b['height']<=page.viewport_size['height']+1)
def fresh(page):
    page.evaluate("closeAlbum();normalize({...freshState(),daily:S.daily,auto:false,autoStory:false});selected=null;undoState=null;setView('game')")
def total(page):return page.evaluate('S.board.filter(x=>x&&!isGen(x)).length+warehouseUsed()')
def reload(page):
    page.reload(wait_until='networkidle');page.wait_for_function("typeof S!=='undefined' && RELEASE==='20260908-atelier4'")
def suite(browser,engine):
    ctx=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,service_workers='block')
    page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        page.goto(URL,wait_until='networkidle');page.wait_for_function("typeof S!=='undefined'")
        check(engine+' release',page.evaluate("RELEASE==='20260908-atelier4'"))
        check(engine+' first visit has warehouse even when SW is blocked',page.locator('#screenWarehouse').count()==1 and page.locator('#nav [data-go="warehouse"]').count()==1)
        check(engine+' no injected legacy art or warehouse scripts',page.locator('script[src*="item-art-levels"],script[src*="warehouse.js"]').count()==0)
        page.locator('#startGame').click();page.wait_for_timeout(150)
        check(engine+' game header warehouse visible',visible(page,'#openWarehouse'))
        check(engine+' nav warehouse visible',visible(page,'#nav [data-go="warehouse"]'))
        check(engine+' unique HTML ids',page.evaluate("(()=>{let a=[...document.querySelectorAll('[id]')].map(x=>x.id);return a.length===new Set(a).size})()"))
        fresh(page);n=total(page);reward=page.evaluate('JSON.stringify([S.coins,S.xp,S.stats])')
        page.locator('.cell[data-i="7"]').tap();check(engine+' deposit enabled after selecting',page.locator('#store').is_enabled())
        page.locator('#store').click()
        check(engine+' deposit actually moves one item',page.evaluate("S.board[7]===null&&S.warehouse.drink1===1") and total(page)==n)
        check(engine+' deposit does not farm rewards',reward==page.evaluate('JSON.stringify([S.coins,S.xp,S.stats])'))
        page.locator('#openWarehouse').click();check(engine+' stored card visible',page.locator('[data-stored-item="drink1"]').is_visible())
        page.locator('#warehouseUndo').click();check(engine+' deposit undo conserves inventory',page.evaluate("S.board[7]==='drink1'&&!S.warehouse.drink1") and total(page)==n)
        page.locator('#nav [data-go="game"]').click()
        for i in (7,8):
            page.locator(f'.cell[data-i="{i}"]').tap();page.locator('#store').click()
        page.locator('#nav [data-go="warehouse"]').click()
        check(engine+' stacking two identical items',page.locator('[data-stored-item="drink1"]').count()==1 and page.evaluate('S.warehouse.drink1===2'))
        page.locator('[data-take="drink1"]').click()
        check(engine+' withdrawal conserves count',page.evaluate("S.warehouse.drink1===1&&countBoard().drink1===1") and total(page)==n)
        reload(page);check(engine+' warehouse survives actual reload',page.evaluate('S.warehouse.drink1===1') and total(page)==n)
        check(engine+' migration backup exists',page.evaluate("localStorage.getItem('rin_harbor_before_warehouse_v4')!==null"))
        # Install a once-only fixture at the NEXT document's initialization. Seeding
        # the live document's disk directly is overwritten by its pagehide autosave.
        seed=page.evaluate("({...S,warehouse:{fish6:2,toy7:1},coins:246,repair:2})")
        encoded=json.dumps(json.dumps(seed,ensure_ascii=False),ensure_ascii=False)
        page.add_init_script("if(!sessionStorage.getItem('atelier4-migration-seeded')){localStorage.setItem('rin_harbor_save_v10',"+encoded+");sessionStorage.setItem('atelier4-migration-seeded','1');}")
        reload(page)
        check(engine+' existing inventory preserved before first autosave',page.evaluate('S.warehouse.fish6===2&&S.warehouse.toy7===1&&S.coins===246'))
        check(engine+' persisted inventory still present',page.evaluate("JSON.parse(localStorage.getItem(SAVE_KEY)).warehouse.fish6===2"))
        fresh(page);page.evaluate("S.warehouse={drink1:12};selected=7;renderGame()");before=page.evaluate('JSON.stringify(S)')
        check(engine+' full warehouse rejects deposit',page.locator('#store').is_disabled() and not page.evaluate('storeSelected()') and before==page.evaluate('JSON.stringify(S)'))
        check(engine+' initial capacity 12',page.evaluate('warehouseCapacity()===12'))
        page.evaluate('S.repair=1;S.level=4');check(engine+' earned capacity 18',page.evaluate('warehouseCapacity()===18'))
        fresh(page);page.evaluate("S.board=S.board.map((x,i)=>i===0?'gen_cafe':i===5?'gen_sea':'drink2');S.warehouse={fish6:1};setView('warehouse')");before=page.evaluate('JSON.stringify(S)')
        check(engine+' full board rejects withdrawal without loss',page.locator('[data-take="fish6"]').is_disabled() and not page.evaluate("takeFromWarehouse('fish6')") and before==page.evaluate('JSON.stringify(S)'))
        fresh(page);page.evaluate('selected=0');before=page.evaluate('JSON.stringify(S)')
        check(engine+' generators cannot be deposited',not page.evaluate('storeSelected()') and before==page.evaluate('JSON.stringify(S)'))
        fresh(page);page.evaluate("S.auto=true;S.autoStory=false;S.warehouse={fish6:1};S.orders=[{title:'保管チェック',wants:[{id:'fish6',n:1}],coin:1,star:1,xp:1}];autoDeliver()")
        check(engine+' warehouse excluded from automatic orders',page.evaluate('S.warehouse.fish6===1&&S.stats.delivered===0'))
        page.evaluate("takeFromWarehouse('fish6')");check(engine+' newly withdrawn item not instantly consumed',page.evaluate('countBoard().fish6===1&&S.stats.delivered===0'))
        page.evaluate('undo()');check(engine+' withdrawal undo',page.evaluate('S.warehouse.fish6===1&&!countBoard().fish6'))
        before=page.evaluate('JSON.stringify(S)');check(engine+' invalid item id safe',not page.evaluate("takeFromWarehouse('__proto__')") and before==page.evaluate('JSON.stringify(S)'))
        page.evaluate("normalize(JSON.parse(JSON.stringify(S)))");check(engine+' backup roundtrip preserves inventory',page.evaluate('S.warehouse.fish6===1'))
        page.evaluate("normalize({...freshState(),daily:S.daily,warehouse:{drink1:19}})")
        check(engine+' overcapacity save is not truncated',page.evaluate('S.warehouse.drink1===19'))
        page.evaluate("takeFromWarehouse('drink1')");check(engine+' overcapacity save can withdraw',page.evaluate('S.warehouse.drink1===18'))
        masks=page.evaluate('''async()=>{const out={};for(const id of Object.keys(ITEM_SHAPES)){
          const svg=new DOMParser().parseFromString(itemArt(id),'image/svg+xml').documentElement;
          svg.setAttribute('xmlns','http://www.w3.org/2000/svg');svg.removeAttribute('data-art');
          svg.querySelectorAll('*').forEach(el=>{for(const attr of ['fill','stroke']){let v=el.getAttribute(attr);if(v&&v!=='none')el.setAttribute(attr,'#000')}});
          const im=new Image();im.src='data:image/svg+xml;base64,'+btoa(new XMLSerializer().serializeToString(svg));await im.decode();
          const cv=document.createElement('canvas');cv.width=cv.height=48;const cx=cv.getContext('2d');cx.drawImage(im,0,0,48,48);
          out[id]=Array.from(cx.getImageData(0,0,48,48).data).filter((v,i)=>i%4===3).map(v=>v>128?'1':'0').join('');
        }return out}''')
        check(engine+' all 53 actual silhouettes distinct',len(masks)==53 and len(set(masks.values()))==53)
        for kind in ['drink','dessert','shell','fish','toy']:
            worst=(1,'','')
            for i,j in itertools.combinations(range(1,11),2):
                a,b=masks[kind+str(i)],masks[kind+str(j)]
                distance=sum(x!=y for x,y in zip(a,b))/sum(x=='1' or y=='1' for x,y in zip(a,b))
                worst=min(worst,(distance,kind+str(i),kind+str(j)))
            check(engine+' '+kind+' shape difference >=10% without colour/labels',worst[0]>=.10,worst)
        fresh(page)
        for w,h in [(320,568),(375,667),(390,844),(430,932),(844,390),(1280,800)]:
            page.set_viewport_size({'width':w,'height':h})
            for view in ('game','warehouse'):
                page.evaluate('(v)=>setView(v)',view);page.wait_for_timeout(160)
                check(f'{engine} {w}x{h} {view} no overflow',page.evaluate("document.documentElement.scrollWidth<=innerWidth+1&&document.querySelector('.screen.on').scrollWidth<=document.querySelector('.screen.on').clientWidth+1"))
                check(f'{engine} {w}x{h} warehouse nav in viewport',visible(page,'#nav [data-go="warehouse"]'))
                if view=='game':check(f'{engine} {w}x{h} warehouse header in viewport',visible(page,'#openWarehouse'))
        page.set_viewport_size({'width':390,'height':844});fresh(page)
        page.evaluate("['drink2','drink3','drink4','drink5','dessert3','dessert6','dessert9','fish2','fish3','fish4','fish5','fish6','fish7','fish8','fish9','fish10','shell5','shell6','shell9','toy7','toy8','toy10'].forEach((id,i)=>S.board[i+6]=id);renderGame()")
        page.wait_for_timeout(1900);page.screenshot(path=str(OUT/(engine+'-board.png')))
        page.evaluate("S.warehouse={fish5:2,fish6:1,dessert6:3,toy7:1};setView('warehouse')")
        page.screenshot(path=str(OUT/(engine+'-warehouse.png')))
        check(engine+' no JavaScript errors',not errors,errors)
    finally:ctx.close()
if __name__=='__main__':
    try:
        html=fetch('index.html').decode();check('warehouse is in origin HTML, not SW injection','id="screenWarehouse"' in html and 'id="openWarehouse"' in html)
        for name in ['index.html','game.js','item-art.js','youth.css','sw.js']:
            check('published bytes match '+name,hashlib.sha256(fetch(name+'?v=atelier4')).digest()==hashlib.sha256((R/name).read_bytes()).digest())
        with sync_playwright() as p:
            for engine in os.environ.get('BROWSERS','chromium,webkit').split(','):
                opts={'headless':True}
                if engine=='chromium' and os.environ.get('SYSTEM_CHROMIUM')=='1':opts.update(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
                b=getattr(p,engine).launch(**opts)
                try:suite(b,engine)
                finally:b.close()
    except Exception as exc:
        RESULTS.append({'test':'atelier4 suite','result':'failed','error':str(exc)});raise
    finally:
        (OUT/'report.json').write_text(json.dumps({'url':URL,'release':'20260908-atelier4','checks':RESULTS},ensure_ascii=False,indent=2))
        print('Atelier4:',sum(x['result']=='passed' for x in RESULTS),'passed;',sum(x['result']=='failed' for x in RESULTS),'failed')
