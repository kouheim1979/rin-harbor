from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1] if '__file__' in globals() else Path.cwd()

def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Patch anchor missing: {label}')
    return text.replace(old,new,1)

# index.html
p=ROOT/'index.html'; s=p.read_text()
s=s.replace('youth.css?v=atelier4','youth.css?v=video1').replace('item-art.js?v=atelier4','item-art.js?v=video1').replace('game.js?v=atelier4','game.js?v=video1')
s=replace_once(s,
    '<div id="openingFallback" class="openingFallback"></div>\n      <img id="openingImage"',
    '<div id="openingFallback" class="openingFallback"></div>\n      <video id="openingVideo" class="openingVideo" muted autoplay loop playsinline preload="metadata" poster="assets/art-hd/hero.webp" aria-hidden="true"><source src="assets/video/title-loop.mp4" type="video/mp4"></video>\n      <img id="openingImage"',
    'title video')
s=replace_once(s,
    '<div class="viewerHead"><b id="viewerTitle">修理アルバム</b><button id="viewerClose" class="off">閉じる</button></div>',
    '<div class="viewerHead"><b id="viewerTitle">修理アルバム</b><div class="viewerActions"><button id="viewerMovie" class="warn">ムービー</button><button id="viewerClose" class="off">閉じる</button></div></div>',
    'album movie button')
movie='''<div id="movieViewer" class="movieViewer" role="dialog" aria-modal="true" aria-hidden="true" aria-labelledby="movieTitle">
  <div class="moviePanel">
    <div class="movieTop"><div><span class="movieKicker">REPAIR MOVIE</span><b id="movieTitle">リン号を修理！</b></div><button id="movieSkip" class="off">スキップ</button></div>
    <video id="repairMovie" class="repairMovie" muted playsinline preload="metadata"></video>
    <div id="movieCaption" class="movieCaption">リン号が少しずつ元気になっていくよ。</div>
  </div>
</div>

'''
if 'id="movieViewer"' not in s:
    s=replace_once(s,'<script src="item-art.js?v=video1"></script>',movie+'<script src="item-art.js?v=video1"></script>','repair movie modal')
p.write_text(s)

# game.js
p=ROOT/'game.js'; s=p.read_text()
s=s.replace("const RELEASE='20260908-atelier4';","const RELEASE='20260908-video1';")
s=s.replace("let hintTimer=null, comboTimer=null, albumIndex=0, albumReturnFocus=null, diskAvailable=true;","let hintTimer=null, comboTimer=null, albumIndex=0, albumReturnFocus=null, movieReturnFocus=null, movieStage=0, diskAvailable=true;")
s=s.replace("  renderAll();saveNow();openAlbum(S.repair);","  renderAll();saveNow();playRepairMovie(S.repair);")
video_funcs='''function finishRepairMovie(openAlbumAfter=true){
  const modal=$('movieViewer'),video=$('repairMovie');
  if(!modal)return;
  try{video.pause();video.removeAttribute('src');video.load()}catch(_e){}
  modal.classList.remove('on');modal.setAttribute('aria-hidden','true');
  document.querySelector('.app').inert=false;$('nav').inert=false;
  const stage=movieStage;
  if(openAlbumAfter&&stage>0){openAlbum(stage);return}
  if(movieReturnFocus?.isConnected)movieReturnFocus.focus({preventScroll:true});
  movieReturnFocus=null;
}

function playRepairMovie(stage,openAlbumAfter=true){
  stage=int(stage,1,5,1);movieStage=stage;
  if(reducedMotion()){if(openAlbumAfter)openAlbum(stage);return}
  const modal=$('movieViewer'),video=$('repairMovie');
  if(!modal||!video){if(openAlbumAfter)openAlbum(stage);return}
  movieReturnFocus=document.activeElement;
  $('movieTitle').textContent=REPAIR_TITLES[stage];
  $('movieCaption').textContent=stage===5?'リン号、ついに完成！ 港から新しい冒険へ。':REPAIR_MESSAGES[stage];
  video.poster=bestStagePath(stage);
  video.src=`assets/video/repair-${stage}.mp4`;
  video.currentTime=0;video.muted=true;video.playsInline=true;
  modal.classList.add('on');modal.setAttribute('aria-hidden','false');
  document.querySelector('.app').inert=true;$('nav').inert=true;
  video.onended=()=>finishRepairMovie(openAlbumAfter);
  video.onerror=()=>finishRepairMovie(openAlbumAfter);
  const promise=video.play();if(promise?.catch)promise.catch(()=>finishRepairMovie(openAlbumAfter));
  $('movieSkip').focus({preventScroll:true});
}

'''
if 'function playRepairMovie(' not in s:
    s=replace_once(s,'function setView(v){\n',video_funcs+'function setView(v){\n','video functions')
s=replace_once(s,"  $('nav').classList.toggle('hidden',v==='opening');", "  $('nav').classList.toggle('hidden',v==='opening');\n  const openingMovie=$('openingVideo');if(openingMovie){if(v==='opening'&&!reducedMotion())openingMovie.play().catch(()=>{});else openingMovie.pause();}",'title movie view management')
s=replace_once(s,"  $('viewerTitle').textContent=item.title;$('viewerText').textContent=item.text;", "  $('viewerTitle').textContent=item.title;$('viewerText').textContent=item.text;\n  if($('viewerMovie')){$('viewerMovie').hidden=albumIndex===0;$('viewerMovie').disabled=albumIndex===0;}",'album movie state')
s=replace_once(s,"bind('repairBtn',repairShip);bind('openAlbum',()=>openAlbum(S.repair));bind('viewerClose',closeAlbum);", "bind('repairBtn',repairShip);bind('openAlbum',()=>openAlbum(S.repair));bind('viewerClose',closeAlbum);bind('viewerMovie',()=>{const stage=albumIndex;closeAlbum();playRepairMovie(stage,true)});bind('movieSkip',()=>finishRepairMovie(true));",'movie bindings')
s=replace_once(s,"$('viewer').addEventListener('click',e=>{if(e.target===$('viewer'))closeAlbum()});", "$('viewer').addEventListener('click',e=>{if(e.target===$('viewer'))closeAlbum()});\n$('movieViewer').addEventListener('click',e=>{if(e.target===$('movieViewer'))finishRepairMovie(true)});\n$('movieViewer').addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();finishRepairMovie(true)}});",'movie modal events')
s=replace_once(s,"$('openingImage').onerror=()=>{$('openingImage').style.display='none';$('openingFallback').hidden=false;$('openingFallback').textContent='港の絵を読み込めませんでした。再読み込みしてください。'};", "$('openingImage').onerror=()=>{$('openingImage').style.display='none';$('openingFallback').hidden=false;$('openingFallback').textContent='港の絵を読み込めませんでした。再読み込みしてください。'};\nif($('openingVideo')){$('openingVideo').onerror=()=>{$('openingVideo').style.display='none'};if(reducedMotion())$('openingVideo').style.display='none';}",'title video fallback')
s=replace_once(s,"document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden'){cancelDrag();saveNow()}else if(S){ensureDaily();renderAll()}});", "document.addEventListener('visibilitychange',()=>{const video=$('openingVideo');if(document.visibilityState==='hidden'){cancelDrag();if(video)video.pause();saveNow()}else if(S){ensureDaily();renderAll();if(view==='opening'&&video&&!reducedMotion())video.play().catch(()=>{})}});",'visibility video pause')
p.write_text(s)

# youth.css
p=ROOT/'youth.css'; s=p.read_text()
css='''

/* Video rewards */
.openingVideo{position:absolute;left:0;top:143px;width:100%;height:calc(100% - 282px);object-fit:cover;object-position:23% 50%;border-radius:34px 34px 0 0;z-index:.5;background:#b5d8d0}.openingHero>img{z-index:0}.viewerActions{display:flex;gap:7px;align-items:center}.movieViewer{display:none;position:fixed;inset:0;z-index:260;align-items:center;justify-content:center;padding:calc(12px + env(safe-area-inset-top,0px)) 12px calc(12px + env(safe-area-inset-bottom,0px));background:#183d3adf;backdrop-filter:blur(10px)}.movieViewer.on{display:flex}.moviePanel{width:min(100%,820px);overflow:hidden;border-radius:24px;background:#fffaf0;border:1px solid #d5e5db;box-shadow:0 24px 80px #08292570}.movieTop{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:13px 14px 10px}.movieTop>div{min-width:0}.movieTop b{display:block;font-size:18px}.movieKicker{display:block;font-size:9px;font-weight:900;letter-spacing:.16em;color:#b17748;margin-bottom:2px}.movieTop button{min-height:38px;padding:6px 12px;font-size:11px}.repairMovie{display:block;width:100%;aspect-ratio:4/3;object-fit:cover;background:#cddfd8}.movieCaption{padding:12px 15px 15px;font-size:13px;line-height:1.65;color:#54736f;font-weight:700}.viewerActions #viewerMovie{min-height:42px;font-size:12px}@media(min-width:700px){.openingVideo{top:0;height:100%;object-position:center;border-radius:0}.movieTop{padding:16px 18px 12px}.movieTop b{font-size:22px}.movieCaption{font-size:14px;padding:14px 18px 18px}}@media(max-height:670px) and (orientation:portrait){.openingVideo{top:127px;height:calc(100% - 249px)}}@media(orientation:landscape) and (max-height:540px){.openingVideo{top:0;height:100%;border-radius:0;object-position:center}.moviePanel{width:min(760px,88vw)}.repairMovie{max-height:68vh;aspect-ratio:auto;object-fit:contain}}@media(prefers-reduced-motion:reduce){.openingVideo{display:none!important}}
'''
if '/* Video rewards */' not in s:s+=css
p.write_text(s)

# sw.js
p=ROOT/'sw.js'; s=p.read_text()
s=s.replace("const VERSION='20260908-atelier4';","const VERSION='20260908-video1';")
s=s.replace("'youth.css?v=atelier4','item-art.js?v=atelier4','game.js?v=atelier4'","'youth.css?v=video1','item-art.js?v=video1','game.js?v=video1'")
if "assets/video/title-loop.mp4" not in s:
    s=s.replace("'assets/art-v1/icon-180.png','assets/art-v1/icon-192.png','assets/art-v1/icon-512.png'", "'assets/art-v1/icon-180.png','assets/art-v1/icon-192.png','assets/art-v1/icon-512.png','assets/video/title-loop.mp4',...Array.from({length:5},(_,i)=>`assets/video/repair-${i+1}.mp4`)")
p.write_text(s)

# Existing tests now target the new release/versioned files.
for name in ['tests/smoke.py','tests/youth.py','tests/atelier4.py','tests/origin_offline.py']:
    p=ROOT/name;s=p.read_text();s=s.replace('20260908-atelier4','20260908-video1').replace('youth.css?v=atelier4','youth.css?v=video1').replace('item-art.js?v=atelier4','item-art.js?v=video1').replace("fetch(name+'?v=atelier4')","fetch(name+'?v=video1')");p.write_text(s)

(ROOT/'tests/video.py').write_text(r'''"""Video reward regression tests for Rin Harbor."""
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
    check(browser_type.name+' repair movie',page.evaluate("repairMovie.currentSrc.includes('repair-1.mp4') && movieTitle.textContent.includes('穴をふさぐ')"));check(browser_type.name+' repair ready',page.evaluate("repairMovie.readyState>=2"))
    page.click('#movieSkip');page.wait_for_selector('#viewer.on');check(browser_type.name+' skip album',page.evaluate('albumIndex===1'))
    page.click('#viewerMovie');page.wait_for_selector('#movieViewer.on');check(browser_type.name+' replay',page.evaluate("repairMovie.currentSrc.includes('repair-1.mp4')"));page.click('#movieSkip');page.wait_for_selector('#viewer.on')
    check(browser_type.name+' no errors',not errors,' | '.join(errors));page.screenshot(path=str(OUT/f'{browser_type.name}-movie.png'));browser.close()
with sync_playwright() as p:
    for b in (p.chromium,p.webkit):suite(b)
for f in files:
    with urllib.request.urlopen(BASE+'assets/video/'+f,timeout=20) as r:check('HTTP '+f,r.status==200)
(OUT/'report.json').write_text(json.dumps({'base_url':BASE,'release':'20260908-video1','checks':checks},ensure_ascii=False,indent=2));print('VIDEO PASS:',len(checks),'checks')
''')

# Verification workflow includes the movie regression suite.
p=ROOT/'.github/workflows/verify-game.yml';s=p.read_text()
s=s.replace("'assets/art-v1/**', 'assets/art-hd/**', 'tests/**'", "'assets/art-v1/**', 'assets/art-hd/**', 'assets/video/**', 'tests/**'")
if 'tests/video.py' not in s:s=s.replace('          python3 tests/atelier4.py\n','          python3 tests/atelier4.py\n          python3 tests/video.py\n')
if 'assets/video/title-loop.mp4' not in s:s=s.replace('          node --check sw.js\n','          node --check sw.js\n          test -s assets/video/title-loop.mp4\n          test -s assets/video/repair-5.mp4\n')
p.write_text(s)

# Generate MP4s from the existing HD artwork (no external media, no sound).
out=ROOT/'assets/video';out.mkdir(parents=True,exist_ok=True)
def run(cmd): subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
run(['ffmpeg','-y','-loop','1','-i',str(ROOT/'assets/art-hd/hero.webp'),'-vf',"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,zoompan=z='1+0.03*sin(on*PI/143)':x='iw/2-(iw/zoom/2)+3*sin(on*2*PI/143)':y='ih/2-(ih/zoom/2)+2*sin(on*PI/143)':d=144:s=1280x720:fps=24,format=yuv420p",'-t','6','-an','-c:v','libx264','-preset','medium','-crf','26','-movflags','+faststart',str(out/'title-loop.mp4')])
for stage in range(1,6):
    fc="[0:v]scale=960:720:force_original_aspect_ratio=increase,crop=960:720,zoompan=z='min(zoom+0.00055,1.045)':x='iw/2-(iw/zoom/2)-4':y='ih/2-(ih/zoom/2)':d=64:s=960x720:fps=24,setsar=1[v0];[1:v]scale=960:720:force_original_aspect_ratio=increase,crop=960:720,zoompan=z='if(lte(zoom,1.0),1.04,max(1.0,zoom-0.00045))':x='iw/2-(iw/zoom/2)+4':y='ih/2-(ih/zoom/2)':d=64:s=960x720:fps=24,setsar=1[v1];[v0][v1]xfade=transition=fade:duration=0.7:offset=1.95,fade=t=in:st=0:d=0.25,fade=t=out:st=3.7:d=0.25,format=yuv420p[v]"
    run(['ffmpeg','-y','-loop','1','-t','2.8','-i',str(ROOT/f'assets/art-hd/repair-{stage-1}.webp'),'-loop','1','-t','2.8','-i',str(ROOT/f'assets/art-hd/repair-{stage}.webp'),'-filter_complex',fc,'-map','[v]','-t','4','-an','-c:v','libx264','-preset','medium','-crf','27','-movflags','+faststart',str(out/f'repair-{stage}.mp4')])
print('Video rewards built.')
