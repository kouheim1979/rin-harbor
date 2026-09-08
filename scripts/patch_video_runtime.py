from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'game.js'
s=p.read_text()
old="try{video.pause();video.removeAttribute('src');video.load()}catch(_e){}"
new="try{video.onended=null;video.onerror=null;video.pause();video.removeAttribute('src');video.load()}catch(_e){}"
if new in s:
    print('Safe movie cleanup already applied.')
elif old in s:
    p.write_text(s.replace(old,new,1))
    print('Patched movie cleanup to prevent stale media events from closing the next repair movie.')
else:
    raise RuntimeError('Movie cleanup anchor not found')
