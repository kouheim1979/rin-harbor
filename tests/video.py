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
def suite(browser_type):
    browser=browser_type.launch();page=browser.new_page(viewport={'width':390,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE,wait_until='networkidle');page.wait_for_function("typeof S!=='undefined' && RELEASE==='20260908-video1'")
    check(browser_type.name+' title video',page.locator('#openingVideo').count()==1);page.wait_for_timeout(1200);check(browser_type.name+' title loaded',page.evaluate("openingVideo.readyState>=2 && openingVideo.muted && openingVideo.playsInline"))
    page.evaluate("S.coins=9999;S.repair=0;saveNow();setView('home')");page.click('#repairBtn');page.wait_for_selector('#movieViewer.on')
    check(browser_type.name+' repair movie',page.evaluate("repairMovie.currentSrc.includes('repair-1.mp4') && movieTitle.textContent.includes('穴をふさぐ')"))
    page.wait_for_function("repairMovie.readyState>=2 && repairMovie.videoWidth>0",timeout=10000)
    check(browser_type.name+' repair ready',page.evaluate("repairMovie.readyState>=2 && repairMovie.videoWidth>0"))
    page.click('#movieSkip');page.wait_for_selector('#viewer.on');check(browser_type.name+' skip album',page.evaluate('albumIndex===1'))
    page.click('#viewerMovie');page.wait_for_selector('#movieViewer.on');check(browser_type.name+' replay',page.evaluate("repairMovie.currentSrc.includes('repair-1.mp4')"));page.click('#movieSkip');page.wait_for_selector('#viewer.on')
    check(browser_type.name+' no errors',not errors,' | '.join(errors));page.screenshot(path=str(OUT/f'{browser_type.name}-movie.png'));browser.close()
with sync_playwright() as p:
    for b in (p.chromium,p.webkit):suite(b)
for f in files:
    with urllib.request.urlopen(BASE+'assets/video/'+f,timeout=20) as r:check('HTTP '+f,r.status==200)
(OUT/'report.json').write_text(json.dumps({'base_url':BASE,'release':'20260908-video1','checks':checks},ensure_ascii=False,indent=2));print('VIDEO PASS:',len(checks),'checks')
