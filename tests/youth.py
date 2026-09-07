"""Sea Journal release gate: real HD decoding, responsive UI, vector art, screenshots.
Runs only in a disposable browser context; does not touch any player's own save.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import urllib.request
from PIL import Image,ImageStat
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
URL=os.environ.get('BASE_URL','http://127.0.0.1:8765/').rstrip('/')+'/'
OUT=Path(os.environ.get('RESULT_DIR','test-results'))/'sea-journal'
OUT.mkdir(parents=True,exist_ok=True)
RESULTS=[]
def check(name,condition,detail=''):
    if not condition:raise AssertionError(f'{name}: {detail}')
    RESULTS.append({'test':name,'result':'passed'})
def fetch(path):
    with urllib.request.urlopen(URL+path,timeout=45) as response:return response.read()
def asset_checks():
    manifest=json.loads(fetch('assets/art-hd/manifest.json'))
    check('HD manifest records neural reconstruction','FSRCNN' in manifest['method'] and len(manifest['model_sha256'])==64)
    check('HD manifest has 7 full scenes and 6 thumbnails',len(manifest['files'])==13)
    hashes=[]
    for row in manifest['files']:
        raw=fetch(row['path'])
        check('HD checksum '+row['path'],hashlib.sha256(raw).hexdigest()==row['sha256'])
        im=Image.open(io.BytesIO(raw));im.load()
        check('HD declared dimensions '+row['path'],im.size==(row['width'],row['height']))
        if row['path'].endswith('/hero.webp'):
            check('Title is 2880 by 1620',im.size==(2880,1620))
        elif '/repair-' in row['path']:
            check('Full repair scene is 2880 by 2160 '+row['path'],im.size==(2880,2160))
            hashes.append(row['sha256'])
        else:check('Thumbnail is 480 by 360 '+row['path'],im.size==(480,360))
    check('Six different full repair images',len(set(hashes))==6)
    check('Live CSS equals tested CSS',hashlib.sha256(fetch('youth.css?v=sea2paint')).digest()==hashlib.sha256((ROOT/'youth.css').read_bytes()).digest())
    check('Live vector art equals tested vector art',hashlib.sha256(fetch('item-art.js?v=sea2paint')).digest()==hashlib.sha256((ROOT/'item-art.js').read_bytes()).digest())
def visible_without_nav(page,selector):
    a=page.locator(selector).bounding_box();n=page.locator('#nav').bounding_box()
    return bool(a and n and a['x']>=-1 and a['y']>=-1 and (a['y']+a['height']<=n['y']+1 or a['x']+a['width']<=n['x']+1))

def photo_snapshot(page,engine,path):
    page.wait_for_function("document.getElementById('homeShipImage').dataset.ready==='true'")
    page.locator('#homeShipImage').evaluate("async e=>{await e.decode();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}")
    page.wait_for_timeout(150)
    raw=page.screenshot(path=str(path))
    im=Image.open(io.BytesIO(raw)).convert('RGB')
    box=page.locator('#homeShipImage').bounding_box()
    scale=im.width/page.viewport_size['width']
    area=im.crop((round((box['x']+3)*scale),round((box['y']+3)*scale),round((box['x']+box['width']-3)*scale),round((box['y']+box['height']-3)*scale)))
    check(engine+' harbor photograph is actually painted',max(ImageStat.Stat(area).stddev)>20)

def suite(browser,engine):
    context=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=3,is_mobile=True,has_touch=True)
    try:
        page=context.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(URL,wait_until='networkidle')
        page.wait_for_function("typeof RELEASE!=='undefined' && RELEASE==='20260907-sea2paint'")
        page.wait_for_function("document.getElementById('openingImage').complete&&document.getElementById('openingImage').naturalWidth===2880")
        page.wait_for_timeout(2200)
        check(engine+' one cohesive theme',page.locator('link[rel="stylesheet"]').count()==1 and 'youth.css' in page.locator('link[rel="stylesheet"]').get_attribute('href'))
        check(engine+' readable daylight background',page.evaluate("getComputedStyle(document.body).backgroundColor")=='rgb(234, 246, 241)')
        check(engine+' hero sharp, no dark filter',page.locator('#openingImage').evaluate("e=>getComputedStyle(e).filter==='none'"))
        check(engine+' original 53 item IDs preserved',page.evaluate('Object.keys(ITEMS).length===53'))
        check(engine+' every item renders a vector',page.evaluate("Object.keys(ITEMS).every(id=>{let d=new DOMParser().parseFromString(itemArt(id),'image/svg+xml');return !d.querySelector('parsererror')&&d.documentElement.tagName==='svg'&&d.documentElement.getAttribute('viewBox')==='0 0 68 68'})"))
        check(engine+' primary button contrast',page.evaluate(r"""()=>{
          const c=getComputedStyle(document.getElementById('startGame'));
          const lum=s=>{const a=s.match(/[\d.]+/g).slice(0,3).map(Number).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4});return a[0]*.2126+a[1]*.7152+a[2]*.0722};
          const a=lum(c.color),b=lum(c.backgroundColor);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)>=4.5;
        }"""))
        page.screenshot(path=str(OUT/(engine+'-title.png')))
        page.locator('#startHome').click()
        page.wait_for_function('document.getElementById("homeShipImage").naturalWidth===2880')
        check(engine+' play button visible on 390 phone',visible_without_nav(page,'.playBanner'))
        check(engine+' all five restoration checkpoints',page.locator('#repairJourney span').count()==5)
        check(engine+' menu icons use stroked art',page.locator('.menuCard[data-go="story"] svg').evaluate("e=>getComputedStyle(e).fill==='none'"))
        photo_snapshot(page,engine,OUT/(engine+'-harbor.png'))
        page.locator('.playBanner').click()
        page.wait_for_selector('.cell .itemArt')
        check(engine+' initial board items use real SVG',page.locator('.cell:not(.empty) .itemArt').count()==6)
        check(engine+' no platform emoji in board artwork',page.locator('.cell .em').evaluate_all("es=>es.every(e=>e.textContent.trim()==='')"))
        check(engine+' request above board',page.locator('.orderStrip').bounding_box()['y']<page.locator('#board').bounding_box()['y'])
        check(engine+' six tool buttons accessible',page.locator('.controls button').count()==6 and visible_without_nav(page,'.controls'))
        page.evaluate("S.auto=false;S.autoStory=false;['drink2','drink3','dessert2','shell2','fish1','toy1','dessert3','shell3','drink1','toy2','fish2','dessert1','shell4','drink5','toy3','dessert4'].forEach((id,j)=>S.board[j+12]=id);renderGame()")
        page.wait_for_timeout(100)
        page.screenshot(path=str(OUT/(engine+'-board.png')))
        for view in ['orders','story','book']:
            page.evaluate('(v)=>setView(v)',view);page.wait_for_timeout(100)
            page.screenshot(path=str(OUT/(engine+'-'+view+'.png')))
        for w,h in [(320,568),(375,667),(390,844),(430,932),(844,390),(1280,800)]:
            page.set_viewport_size({'width':w,'height':h})
            for view in ['home','game','orders','story','book']:
                page.evaluate('(v)=>{closeAlbum();setView(v)}',view);page.wait_for_timeout(150)
                check(f'{engine} {w}x{h} {view} no horizontal overflow',page.evaluate("document.documentElement.scrollWidth<=innerWidth+1 && document.querySelector('.screen.on').scrollWidth<=document.querySelector('.screen.on').clientWidth+1"))
                if view=='game':
                    check(f'{engine} {w}x{h} full board reachable',visible_without_nav(page,'#board'))
                    check(f'{engine} {w}x{h} all tools reachable',visible_without_nav(page,'.controls'))
                    check(f'{engine} {w}x{h} status readable',visible_without_nav(page,'#msg'))
                if view=='home' and (w,h) in [(375,667),(390,844),(430,932)]:
                    check(f'{engine} {w}x{h} play immediately visible',visible_without_nav(page,'.playBanner'))
        page.set_viewport_size({'width':390,'height':844})
        page.evaluate("S.repair=5;setView('story');openAlbum(5)")
        page.wait_for_function('document.getElementById("viewerImg").naturalWidth===2880')
        check(engine+' full detail album uses high-resolution scene',page.locator('#viewerImg').get_attribute('src').endswith('/repair-5.webp'))
        page.wait_for_function("Array.from(document.querySelectorAll('.viewerThumb img')).every(e=>e.complete&&e.naturalWidth===480)")
        check(engine+' lightweight thumbnail dimensions',page.locator('.viewerThumb img').evaluate_all("es=>es.every(e=>e.complete&&e.naturalWidth===480)"))
        page.screenshot(path=str(OUT/(engine+'-hd-album.png')))
        check(engine+' no JavaScript exceptions',not errors,errors)
    finally:context.close()
if __name__=='__main__':
    try:
        asset_checks()
        with sync_playwright() as p:
            for engine in os.environ.get('BROWSERS','chromium,webkit').split(','):
                options={'headless':True}
                if os.environ.get('SYSTEM_CHROMIUM')=='1' and engine=='chromium':options.update(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
                browser=getattr(p,engine).launch(**options)
                try:suite(browser,engine)
                finally:browser.close()
        print(f'SEA JOURNAL PASS: {len(RESULTS)} checks')
    except Exception as exc:
        RESULTS.append({'test':'Sea Journal suite','result':'failed','error':str(exc)})
        raise
    finally:(OUT/'report.json').write_text(json.dumps({'base_url':URL,'release':'20260907-sea2paint','checks':RESULTS},ensure_ascii=False,indent=2))
