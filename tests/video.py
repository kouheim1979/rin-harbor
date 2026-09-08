"""Video reward regression tests for Rin Harbor."""
import json, os, subprocess, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE=os.environ.get('BASE_URL','http://127.0.0.1:8765/').rstrip('/')+'/'
OUT=Path(os.environ.get('RESULT_DIR','test-results'))/'video';OUT.mkdir(parents=True,exist_ok=True)
R=Path(__file__).resolve().parents[1];checks=[]
def check(name,ok,detail=''):
    checks.append({'test':name,'result':'passed' if ok else 'failed','detail':detail})
    if not ok: raise AssertionError(name+(': '+detail if detail else ''))
def probe(path): return json.loads(subprocess.check_output(['ffprobe','-v','quiet','-print_format','json','-show_streams','-show_format',str(path)]))
files=['title-loop.mp4']+[f'repair-{i}.mp4' for i in range(1,6)]
for f in files:
    path=R/'assets/video'/f;check(f+' exists',path.exists() and path.stat().st_size>100000)
    data=probe(path);stream=next(x for x in data['streams'] if x['codec_type']=='video')
    check(f+' h264',stream['codec_name']=='h264');check(f+' yuv420p',stream.get('pix_fmt')=='yuv420p');check(f+' duration',float(data['format']['duration'])>=3.5)
    check(f+' silent',all(s['codec_type']!='audio' for s in data['streams']))
    check(f+' expected dimensions',(stream['width'],stream['height'])==((1280,720) if f=='title-loop.mp4' else (960,720)))
    check(f+' short reward duration',float(data['format']['duration'])<=7 if f=='title-loop.mp4' else float(data['format']['duration'])<=5)
def suite(browser_type):
    browser=browser_type.launch();page=browser.new_page(viewport={'width':390,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE,wait_until='networkidle');page.wait_for_function("typeof S!=='undefined' && RELEASE==='20260908-guide1'")
    check(browser_type.name+' title video',page.locator('#openingVideo').count()==1);page.wait_for_timeout(1200);check(browser_type.name+' title loaded',page.evaluate("openingVideo.readyState>=2 && openingVideo.muted && openingVideo.playsInline"))
    check(browser_type.name+' inline silent title loop',page.evaluate('openingVideo.autoplay && openingVideo.loop && !!openingVideo.poster && openingVideo.videoWidth>0'))
    page.wait_for_function("navigator.serviceWorker.controller!==null",timeout=30000)
    ranged=page.evaluate("""async()=>{const r=await fetch('assets/video/repair-1.mp4',{headers:{Range:'bytes=0-1023'}});const b=await r.arrayBuffer();return {status:r.status,range:r.headers.get('content-range')||'',accept:r.headers.get('accept-ranges')||'',length:b.byteLength,contentLength:r.headers.get('content-length'),mime:r.headers.get('content-type')}}""")
    check(browser_type.name+' cached mp4 range status',ranged['status']==206,str(ranged))
    check(browser_type.name+' cached mp4 range headers',ranged['range'].startswith('bytes 0-1023/') and ranged['accept']=='bytes',str(ranged))
    check(browser_type.name+' cached mp4 range length',ranged['length']==1024,str(ranged))
    check(browser_type.name+' cached mp4 content headers',ranged['contentLength']=='1024' and ranged['mime'].startswith('video/mp4'),str(ranged))
    page.evaluate("S.coins=9999;S.repair=0;saveNow();setView('home')");page.click('#repairBtn');page.wait_for_selector('#movieViewer.on')
    check(browser_type.name+' repair movie',page.evaluate("repairMovie.currentSrc.includes('repair-1.mp4') && movieTitle.textContent.includes('穴をふさぐ')"))
    page.wait_for_function("repairMovie.readyState>=2 && repairMovie.videoWidth>0",timeout=10000)
    check(browser_type.name+' repair ready',page.evaluate("repairMovie.readyState>=2 && repairMovie.videoWidth>0"))
    page.click('#movieSkip');page.wait_for_selector('#viewer.on');check(browser_type.name+' skip album',page.evaluate('albumIndex===1'))
    page.click('#viewerMovie');page.wait_for_selector('#movieViewer.on');check(browser_type.name+' replay',page.evaluate("repairMovie.currentSrc.includes('repair-1.mp4')"))
    page.wait_for_selector('#viewer.on',timeout=10000)
    check(browser_type.name+' natural movie ending opens album',page.evaluate("albumIndex===1&&!movieViewer.classList.contains('on')"))
    page.click('#viewerClose')
    for stage in range(2,6):
        page.evaluate("stage=>{S.coins=9999;S.repair=stage-1;setView('home')}",stage)
        page.click('#repairBtn');page.wait_for_selector('#movieViewer.on')
        page.wait_for_function('repairMovie.readyState>=2 && repairMovie.videoWidth>0',timeout=10000)
        check(browser_type.name+f' repair {stage} decodes inline',page.evaluate("stage=>repairMovie.currentSrc.includes('repair-'+stage+'.mp4')&&repairMovie.playsInline&&repairMovie.muted",stage))
        page.click('#movieSkip');page.wait_for_selector('#viewer.on')
        check(browser_type.name+f' repair {stage} skip opens correct album',page.evaluate('albumIndex')==stage)
        page.click('#viewerClose')
    page.emulate_media(reduced_motion='reduce')
    page.evaluate("S.coins=9999;S.repair=0;setView('home')");page.click('#repairBtn');page.wait_for_selector('#viewer.on')
    check(browser_type.name+' reduced motion opens album without movie',page.evaluate("albumIndex===1&&!movieViewer.classList.contains('on')"))
    check(browser_type.name+' no errors',not errors,' | '.join(errors));page.screenshot(path=str(OUT/f'{browser_type.name}-movie.png'));browser.close()
with sync_playwright() as p:
    for b in (p.chromium,p.webkit):suite(b)
for f in files:
    with urllib.request.urlopen(BASE+'assets/video/'+f,timeout=20) as r:check('HTTP '+f,r.status==200)
(OUT/'report.json').write_text(json.dumps({'base_url':BASE,'release':'20260908-guide1','checks':checks},ensure_ascii=False,indent=2));print('VIDEO PASS:',len(checks),'checks')
