"""Rin Harbor browser regression suite. Run against localhost or an explicit Pages URL.
Dependencies: playwright==1.57.0, Pillow. Never uses a player's real save data.
"""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import time
import urllib.request
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('RESULT_DIR', 'test-results'))
OUT.mkdir(parents=True, exist_ok=True)
URL = os.environ.get('BASE_URL', 'http://127.0.0.1:8765/')
INLINE = os.environ.get('INLINE_TEST') == '1'
RESULTS = []

def check(name, value, detail=''):
    if not value:
        raise AssertionError(f'{name}: {detail}')
    RESULTS.append({'test': name, 'result': 'passed'})

def embedded_html():
    def data(path):
        p=ROOT/path
        return 'data:'+('image/jpeg' if p.suffix=='.jpg' else 'image/png')+';base64,'+base64.b64encode(p.read_bytes()).decode()
    html=(ROOT/'index.html').read_text()
    html=re.sub(r'<link[^>]*rel="(?:apple-touch-icon|icon|manifest|preload)"[^>]*>','',html)
    for name in ['base','premium','art']:
        html=re.sub(r'<link rel="stylesheet" href="'+name+r'.css[^>]*>',lambda _,n=name:'<style>'+(ROOT/(n+'.css')).read_text()+'</style>',html)
    for path in ['assets/art-v1/hero.jpg','assets/art-v1/icon-180.png']:
        html=html.replace('src="'+path+'"','src="'+data(path)+'"')
    code=(ROOT/'game.js').read_text().replace('return `assets/art-v1/repair-${int(stage,0,5)}.jpg`','return LOCAL_ART[int(stage,0,5)]')
    code='const LOCAL_ART='+json.dumps([data(f'assets/art-v1/repair-{i}.jpg') for i in range(6)])+';\n'+code
    return re.sub(r'<script src="game.js[^>]*></script>',lambda _:'<script>'+code+'</script>',html)

HTML=embedded_html() if INLINE else ''

def open_game(page, seed=None):
    init="""() => {
      const seeded=SEED;
      if (INLINE) Object.defineProperty(window,'localStorage',{value:{store:{},getItem(k){return this.store[k]??null},setItem(k,v){this.store[k]=String(v)},removeItem(k){delete this.store[k]},clear(){this.store={}}}});
      if(seeded && !sessionStorage.getItem('seeded')) {localStorage.clear(); for(const [k,v] of Object.entries(seeded))localStorage.setItem(k,v);sessionStorage.setItem('seeded','1');}
    }""".replace('SEED',json.dumps(seed)).replace('INLINE',str(INLINE).lower())
    if INLINE:
        # Screenshot/unit harness only: HTTP, persistence and service workers tested separately in CI.
        init=init.replace(" && !sessionStorage.getItem('seeded')",'').replace("sessionStorage.setItem('seeded','1');",'')
        page.evaluate(init)
        page.set_content(HTML, wait_until='load')
    else:
        page.add_init_script('('+init+')()')
        page.goto(URL,wait_until='networkidle')
    page.wait_for_function("typeof S!=='undefined' && S!==null && typeof RELEASE!=='undefined'")
    check('correct release',page.evaluate('RELEASE')=='20260907-sea2paint')
    page.wait_for_timeout(180)

def reload_page(page):
    """Use the browser's normal reload, not WebKit's automation reload path.

    https://github.com/microsoft/playwright/issues/42273
    A new document is mandatory: the previous JS state must not satisfy checks.
    No navigation errors or failed offline assertions are suppressed.
    """
    page.evaluate("window.__rinReloadSentinel=true")
    with page.expect_navigation(wait_until='load', timeout=45000):
        page.evaluate("setTimeout(()=>location.reload(),0)")
    page.wait_for_function("window.__rinReloadSentinel===undefined && typeof S!=='undefined' && S!==null")

def fresh(page):
    page.evaluate("closeAlbum();normalize({...freshState(),auto:false,autoStory:false,daily:S.daily});selected=null;undoState=null;combo=0;lastMergeAt=0;clearTimeout(comboTimer);clearTimeout(hintTimer);setView('game');")
    page.wait_for_timeout(60)

def tap(page, i):
    box=page.locator(f'.cell[data-i="{i}"]').bounding_box()
    page.touchscreen.tap(box['x']+box['width']/2,box['y']+box['height']/2)

def state(page):
    return page.evaluate('JSON.stringify(S)')

def run_suite(browser, engine):
    context=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    open_game(page)
    check(engine+' initial board/orders',page.evaluate('S.board.length===36 && S.orders.length===8'))
    check(engine+' title art decoded',page.locator('#openingImage').evaluate('(e)=>e.complete&&e.naturalWidth>=1000'))
    page.wait_for_timeout(1900);page.screenshot(path=str(OUT/(engine+'-title.png')))
    page.locator('#startHome').click();page.wait_for_function("document.getElementById('homeShipImage').naturalWidth>0")
    check(engine+' home art decoded',page.locator('#homeShipImage').evaluate('(e)=>e.naturalWidth>=1000'))
    page.locator('#homeShipImage').evaluate("async e=>{await e.decode();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}");page.wait_for_timeout(150);page.screenshot(path=str(OUT/(engine+'-harbor.png')))
    page.locator('#nav [data-go="game"]').click()
    page.screenshot(path=str(OUT/(engine+'-board.png')))

    fresh(page);tap(page,7);tap(page,8)
    check(engine+' touch merge',page.evaluate("S.board[7]===null&&S.board[8]==='drink2'&&S.stats.merges===1"))
    page.locator('#undo').click()
    check(engine+' undo merge',page.evaluate("S.board[7]==='drink1'&&S.board[8]==='drink1'&&S.stats.merges===0"))
    tap(page,7);tap(page,9)
    check(engine+' move to empty tile',page.evaluate("S.board[7]===null&&S.board[9]==='drink1'"))
    tap(page,8);tap(page,0)
    check(engine+' generator while selected',page.evaluate("S.stats.generated===1&&selected===null"))
    page.locator('#hint').click();check(engine+' hint highlights pair',page.locator('.cell.hint').count()==2)
    positions=page.evaluate("S.board.map((v,i)=>isGen(v)?i:null).filter(i=>i!==null)")
    page.locator('#sort').click()
    check(engine+' sort keeps generators',positions==page.evaluate("S.board.map((v,i)=>isGen(v)?i:null).filter(i=>i!==null)"))

    fresh(page)
    a=page.locator('.cell[data-i="7"]').bounding_box();b=page.locator('.cell[data-i="8"]').bounding_box()
    page.mouse.move(a['x']+a['width']/2,a['y']+a['height']/2);page.mouse.down()
    page.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2,steps=6);page.mouse.up()
    check(engine+' drag merge',page.evaluate("S.board[8]==='drink2'&&S.board[7]===null"))
    fresh(page);before=state(page)
    page.locator('.cell[data-i="7"]').dispatch_event('pointerdown',{'pointerId':33,'pointerType':'touch','isPrimary':True,'button':0,'clientX':10,'clientY':10})
    page.locator('#board').dispatch_event('pointercancel',{'pointerId':33})
    check(engine+' cancellation unchanged',before==state(page))
    a=page.locator('.cell[data-i="7"]').bounding_box()
    page.mouse.move(a['x']+20,a['y']+20);page.mouse.down();page.mouse.move(1,1,steps=5);page.mouse.up()
    check(engine+' drag outside unchanged',before==state(page))
    page.locator('.cell[data-i="7"]').focus();page.keyboard.press('Enter');page.locator('.cell[data-i="8"]').focus();page.keyboard.press('Enter')
    check(engine+' keyboard merge',page.evaluate("S.board[8]==='drink2'&&S.board[7]===null"))

    fresh(page)
    page.evaluate("S.board=S.board.map(v=>v||'shell10');renderGame()")
    before=state(page);tap(page,0)
    check(engine+' full board no loss',before==state(page))
    page.evaluate("moveOrMerge(1,2)")
    check(engine+' highest level does not vanish',before==state(page))

    fresh(page)
    page.evaluate("S.orders[0]={title:'テスト',wants:[{id:'drink1',n:1},{id:'drink1',n:2}],coin:26,star:1,xp:1}")
    check(engine+' aggregated requirements',not page.evaluate('orderCan(S.orders[0])'))
    page.evaluate("S.orders[0]={title:'テスト',wants:[{id:'drink1',n:2}],coin:26,star:1,xp:1};renderGame()")
    before=state(page);page.locator('#quickTop').click()
    check(engine+' manual delivery consumes both',page.evaluate("!S.board.includes('drink1')&&S.stats.delivered===1&&S.coins===76&&S.stars===1"))
    page.locator('#undo').click();check(engine+' undo delivery',state(page)==before)

    fresh(page)
    page.evaluate("S.orders=S.orders.map(()=>({title:'自動',wants:[{id:'drink2',n:1}],coin:26,star:1,xp:1}));S.auto=true;renderGame()")
    before=state(page);tap(page,7);tap(page,8)
    check(engine+' auto delivery on merge',page.evaluate("S.stats.delivered===1&&!S.board.includes('drink2')"))
    page.locator('#undo').click();check(engine+' undo auto transaction',before==state(page))

    fresh(page);page.evaluate("S.coins=1550;setView('home')")
    for stage in range(1,6):
        page.locator('#repairBtn').click();page.wait_for_function("document.getElementById('viewerImg').complete&&document.getElementById('viewerImg').naturalWidth>0")
        check(engine+f' repair stage {stage}',page.evaluate('S.repair')==stage)
        check(engine+f' album unlock {stage}',page.locator('.viewerThumb').count()==stage+1)
        page.keyboard.press('Escape')
    check(engine+' ship complete',page.evaluate('S.coins===0&&S.repair===5') and page.locator('#repairBtn').is_disabled())
    page.locator('#nav [data-go="story"]').click();page.locator('#openAlbum').click()
    page.screenshot(path=str(OUT/(engine+'-album.png')));page.keyboard.press('Escape')

    fresh(page);page.evaluate("S.stars=200;S.board=S.board.map(v=>v||'shell10');S.story=1")
    before=state(page);page.evaluate('openStory(2)')
    check(engine+' full board story reward protected',state(page)==before)
    page.evaluate("S.board[1]=null;openStory(2)")
    check(engine+' gift generator awarded',page.evaluate("S.story===2&&S.board.includes('gen_gift')"))
    page.evaluate('autoOpenStory()')
    check(engine+' story completion',page.evaluate('S.story===7'))

    fresh(page)
    page.evaluate("S.daily.missions.forEach(m=>m.progress=m.goal);S.autoStory=false;S.coins=0;S.stars=0;claimMission(0);claimMission(1);claimMission(2)")
    check(engine+' daily rewards exactly once',page.evaluate('S.coins===135&&S.stars===7&&S.daily.allClearClaimed'))
    before=state(page);page.evaluate('claimMission(0);claimMission(1);claimMission(2);ensureDaily();ensureDaily()')
    check(engine+' no repeat daily reward',before==state(page))

    # Invalid import is rejected without touching progress; valid Unicode JSON round-trips.
    page.evaluate("setView('book')")
    before=state(page);seen=[]
    def invalid_dialog(dialog):
        seen.append(dialog.type)
        if dialog.type=='prompt':dialog.accept('not-a-backup')
        else:dialog.accept()
    page.on('dialog',invalid_dialog);page.locator('#importSave').click();page.remove_listener('dialog',invalid_dialog)
    check(engine+' invalid backup keeps save',state(page)==before and seen==['prompt','alert'])
    value=json.loads(before);value['coins']=888;value['repair']=2
    def valid_dialog(dialog):
        if dialog.type=='prompt':dialog.accept(json.dumps(value,ensure_ascii=False))
        else:dialog.accept()
    page.on('dialog',valid_dialog);page.locator('#importSave').click();page.remove_listener('dialog',valid_dialog)
    check(engine+' backup restore',page.evaluate('S.coins===888&&S.repair===2'))
    page.evaluate('undo()');check(engine+' backup restoration can be undone',state(page)==before)
    if not INLINE:
        page.evaluate("setView('book')")
        with page.expect_download() as download:
            page.locator('#downloadSave').click()
        download_path=OUT/(engine+'-save.json');download.value.save_as(str(download_path))
        check(engine+' JSON backup export',json.loads(download_path.read_text())==json.loads(state(page)))
        download_path.unlink()

    page.evaluate("normalize({board:initialBoard(),level:Infinity,xp:Infinity,story:99,repair:-9,coins:-1,stars:NaN,book:{'__proto__':1},orders:[],daily:{date:'bad',missions:[null]}})")
    check(engine+' invalid state safely normalized',page.evaluate('S.level===1&&S.xp===0&&S.repair===0&&S.coins>=0&&S.orders.length===8&&S.daily.date===localDateString()'))
    page.evaluate('saveNow()');check(engine+' save written',page.evaluate('JSON.parse(localStorage.getItem(SAVE_KEY)).board.length===36'))

    for w,h in [(320,568),(375,667),(390,844),(430,932),(844,390),(1280,800)]:
        page.set_viewport_size({'width':w,'height':h});page.evaluate("setView('game')");page.wait_for_timeout(140)
        boxes={s:page.locator(s).bounding_box() for s in ['#board','.boardBox','.controls','#msg','#nav']}
        board,nav,box=boxes['#board'],boxes['#nav'],boxes['.boardBox']
        check(engine+f' layout {w}x{h}',board['width']>100 and board['x']>=0 and board['y']>=0 and board['x']+board['width']<=w+1 and (board['y']+board['height']<=nav['y']+1 or board['x']+board['width']<=nav['x']+1) and (boxes['#msg']['y']+boxes['#msg']['height']<=nav['y']+1 or boxes['#msg']['x']+boxes['#msg']['width']<=nav['x']+1),str(boxes))
        page.screenshot(path=str(OUT/(engine+f'-{w}x{h}.png')))
    check(engine+' no JS exceptions',not errors,errors)
    context.close()

    # Migration gets a genuinely fresh browser context and a v8-only save.
    context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    page=context.new_page()
    board=[None]*36;board[0]='gen_cafe';board[5]='gen_sea';board[7]='drink8'
    old={'board':board,'coins':1234,'stars':55,'level':18,'xp':12,'story':4,'repair':3,'book':{'drink8':1},'orders':[],'auto':False}
    open_game(page,{'rin_harbor_save_v8':json.dumps(old),'rin_harbor_save_v10':'{broken'})
    check(engine+' legacy progress migration',page.evaluate("S.repair===3&&S.story===4&&S.coins===1264&&S.board[7]==='drink8'&&S.auto===false&&S.book.drink8===1"))
    check(engine+' original save backup',page.evaluate("JSON.parse(localStorage.getItem(BACKUP_KEY)).coins===1234"))
    if not INLINE:
        page.wait_for_timeout(300);reload_page(page)
        check(engine+' persisted reload',page.evaluate("S.repair===3&&S.coins===1264&&S.board[7]==='drink8'"))
    context.close()

    # WebKit: stop a real TCP origin instead of using the broken offline simulator.
    if not INLINE and engine=='webkit':
        from origin_offline import test_origin_offline
        test_origin_offline(browser,ROOT,check,reload_page)

    # Chromium: also test simulated airplane mode against BASE_URL itself.
    if not INLINE and engine=='chromium':
        context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        page=context.new_page();page.goto(URL,wait_until='networkidle')
        page.wait_for_function("document.getElementById('offlineStatus').textContent.includes('保存済み')||document.getElementById('offlineStatus').textContent.includes('新しい')",timeout=90000)
        page.wait_for_function('navigator.serviceWorker.controller!==null',timeout=30000)
        page.evaluate("S.auto=false;S.autoStory=false;S.coins=2345;S.repair=5;saveNow()")
        await_cache=page.evaluate("async()=>{const c=await caches.open('rin-harbor-20260907-sea2paint');const all=await c.keys();return all.length}")
        check(engine+' offline assets installed',await_cache>=16)
        await_none=page.evaluate("async()=>{await caches.open('unrelated-app-sentinel');return true}")
        context.set_offline(True)
        check(engine+' uncached network request fails',page.evaluate("fetch('./__offline_probe__?t='+Date.now(),{cache:'no-store'}).then(()=>false,()=>true)"))
        reload_page(page)
        check(engine+' offline reload with progress',page.evaluate('S.coins===2345&&S.repair===5'))
        page.evaluate("setView('home')");page.wait_for_function('document.getElementById("homeShipImage").naturalWidth>1000')
        check(engine+' offline repair artwork',page.locator('#homeShipImage').evaluate('(e)=>e.naturalWidth>1000'))
        page.evaluate('openAlbum(0)');page.wait_for_function('document.getElementById("viewerImg").naturalWidth>1000')
        check(engine+' offline album',page.locator('.viewerThumb').count()==6)
        check(engine+' unrelated cache preserved',page.evaluate("caches.has('unrelated-app-sentinel')"))
        context.set_offline(False);context.close()

def asset_checks():
    manifest=json.loads((ROOT/'assets/art-v1/manifest.json').read_text())
    hashes=[]
    for row in manifest:
        if INLINE:raw=(ROOT/row['path']).read_bytes()
        else:
            with urllib.request.urlopen(URL+row['path'],timeout=30) as response:raw=response.read()
        check('checksum '+row['path'],hashlib.sha256(raw).hexdigest()==row['sha256'])
        im=Image.open(io.BytesIO(raw));im.load()
        check('decodable '+row['path'],min(im.size)>=180)
        if 'repair-' in row['path']:hashes.append(hashlib.sha256(raw).hexdigest())
    check('six distinct repair scenes',len(set(hashes))==6)

if __name__=='__main__':
    try:
        asset_checks()
        with sync_playwright() as p:
            for engine in os.environ.get('BROWSERS','chromium,webkit').split(','):
                options={'headless':True}
                if INLINE or os.environ.get('SYSTEM_CHROMIUM')=='1':options.update(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
                browser=getattr(p,engine).launch(**options)
                try:run_suite(browser,engine)
                finally:browser.close()
        print(f'PASS: {len(RESULTS)} checks')
    except Exception as exc:
        RESULTS.append({'test':'suite','result':'failed','error':str(exc)})
        raise
    finally:
        (OUT/'report.json').write_text(json.dumps({'base_url':URL,'inline_harness':INLINE,'checks':RESULTS},ensure_ascii=False,indent=2))
