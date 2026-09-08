from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

# Existing gameplay test: a successful repair now shows the short reward movie
# before opening the repair album.
p=ROOT/'tests/smoke.py'
s=p.read_text()
old="""    for stage in range(1,6):
        page.locator('#repairBtn').click();page.wait_for_function(\"document.getElementById('viewerImg').complete&&document.getElementById('viewerImg').naturalWidth>0\")
        check(engine+f' repair stage {stage}',page.evaluate('S.repair')==stage)
        check(engine+f' album unlock {stage}',page.locator('.viewerThumb').count()==stage+1)
        page.keyboard.press('Escape')
"""
new="""    for stage in range(1,6):
        page.locator('#repairBtn').click();page.wait_for_selector('#movieViewer.on')
        check(engine+f' repair stage {stage}',page.evaluate('S.repair')==stage)
        check(engine+f' repair movie {stage}',page.evaluate(f\"repairMovie.currentSrc.includes('repair-{stage}.mp4')\"))
        page.locator('#movieSkip').click();page.wait_for_selector('#viewer.on')
        page.wait_for_function(\"document.getElementById('viewerImg').complete&&document.getElementById('viewerImg').naturalWidth>0\")
        check(engine+f' album unlock {stage}',page.locator('.viewerThumb').count()==stage+1)
        page.keyboard.press('Escape')
"""
if new in s:
    print('Video-aware smoke repair test already applied.')
elif old in s:
    p.write_text(s.replace(old,new,1))
    print('Patched smoke repair test for movie-before-album flow.')
else:
    raise RuntimeError('Smoke repair-loop anchor not found')

# Dedicated movie test: opening the modal can precede loadeddata by a few frames,
# especially in headless Chromium/WebKit. Wait for actual decoded video data
# instead of sampling readyState immediately after the modal becomes visible.
p=ROOT/'tests/video.py'
s=p.read_text()
old="""    check(browser_type.name+' repair movie',page.evaluate(\"repairMovie.currentSrc.includes('repair-1.mp4') && movieTitle.textContent.includes('穴をふさぐ')\"));check(browser_type.name+' repair ready',page.evaluate(\"repairMovie.readyState>=2\"))
"""
new="""    check(browser_type.name+' repair movie',page.evaluate(\"repairMovie.currentSrc.includes('repair-1.mp4') && movieTitle.textContent.includes('穴をふさぐ')\"))
    page.wait_for_function(\"repairMovie.readyState>=2 && repairMovie.videoWidth>0\",timeout=10000)
    check(browser_type.name+' repair ready',page.evaluate(\"repairMovie.readyState>=2 && repairMovie.videoWidth>0\"))
"""
if new in s:
    print('Video readiness wait already applied.')
elif old in s:
    p.write_text(s.replace(old,new,1))
    print('Patched video test to wait for decoded media data.')
else:
    raise RuntimeError('Video readiness assertion anchor not found')
