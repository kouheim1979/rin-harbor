from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
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
