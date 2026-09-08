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
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

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
    check('correct release',page.evaluate('RELEASE')=='20260908-guide1')
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
    page.evaluate("S.orders[0]={title:'ヒント確認',wants:[{id:'drink2',n:1}],coin:26,star:1,xp:1};guidedOrder=S.orders[0];renderGame()")
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
        page.locator('#repairBtn').click();page.wait_for_selector('#movieViewer.on')
        check(engine+f' repair stage {stage}',page.evaluate('S.repair')==stage)
        check(engine+f' repair movie {stage}',page.evaluate(f"repairMovie.currentSrc.includes('repair-{stage}.mp4')"))
        # On a fast/public load the four-second reward may naturally finish before
        # automation reaches the skip button. Both paths are valid and must end at
        # the repair album, so only treat a short skip timeout as natural completion.
        try:
            page.locator('#movieSkip').click(timeout=1200)
        except PlaywrightTimeoutError:
            pass
        page.wait_for_selector('#viewer.on',timeout=10000)
        page.wait_for_function("document.getElementById('viewerImg').complete&&document.getElementById('viewerImg').naturalWidth>0")
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

    # Reset is two-stage confirmation, cancellation must not modify state.
    before=state(page);dialogs=[]
    def reset_cancel(dialog):
        dialogs.append(dialog.type)
        dialog.dismiss()
    page.on('dialog',reset_cancel);page.locator('#reset').click();page.remove_listener('dialog',reset_cancel)
    check(engine+' reset cancellation safe',state(page)==before and dialogs==['confirm'])

    # Settings persist through regular localStorage save and real reload.
    page.evaluate("S.auto=false;S.autoStory=false;S.sound=true;S.haptics=false;saveNow()")
    if not INLINE:
        reload_page(page)
        check(engine+' settings persist',page.evaluate('!S.auto&&!S.autoStory&&S.sound&&!S.haptics'))

    # Restore test baseline after reload before the offline phase.
    page.evaluate("normalize({...freshState(),auto:false,autoStory:false,daily:S.daily});saveNow();setView('game')")
    page.wait_for_timeout(120)
    check(engine+' no page errors',not errors,' | '.join(errors))
    context.close()

def run_offline(browser, engine):
    if INLINE:return
    context=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True,service_workers='allow')
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    open_game(page);page.wait_for_function("navigator.serviceWorker.controller!==null",timeout=30000)
    page.evaluate("S.coins=4321;S.book.fish3=1;saveNow()")
    if engine=='chromium':
        context.set_offline(True);reload_page(page);page.wait_for_function('S.coins===4321')
    else:
        # WebKit route interception is not a true transport outage. A killed local origin is
        # exercised by tests/origin_offline.py against the same release instead.
        check(engine+' offline shell cached',page.evaluate("caches.keys().then(k=>k.some(x=>x.includes(RELEASE)))"))
    check(engine+' save survives offline phase',page.evaluate("S.coins===4321&&S.book.fish3===1"))
    context.close()

def main():
    with sync_playwright() as p:
        for engine,browser_type in [('chromium',p.chromium),('webkit',p.webkit)]:
            browser=browser_type.launch();run_suite(browser,engine);run_offline(browser,engine);browser.close()
    if not INLINE:
        # Public/local HTTP release assets and endpoint health.
        for path in ['index.html','game.js','item-art.js','youth.css','sw.js','assets/art-hd/hero.webp','assets/video/title-loop.mp4','assets/video/repair-5.mp4']:
            with urllib.request.urlopen(URL.rstrip('/')+'/'+path,timeout=20) as response:
                check('http '+path,response.status==200)
    (OUT/'smoke-report.json').write_text(json.dumps({'url':URL,'checks':RESULTS},ensure_ascii=False,indent=2))
    print('PASS:',len(RESULTS),'checks')

if __name__=='__main__':
    main()
