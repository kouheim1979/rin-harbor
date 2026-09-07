"""Reconstruct 2x artwork with OpenCV FSRCNN; keep native masters unchanged."""
import hashlib,json,urllib.request
from pathlib import Path
import cv2
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/art-hd'
OUT.mkdir(exist_ok=True)
MODEL_URL='https://raw.githubusercontent.com/Saafke/FSRCNN_Tensorflow/master/models/FSRCNN_x2.pb'
model=Path('/tmp/rin-FSRCNN_x2.pb')
with urllib.request.urlopen(MODEL_URL,timeout=30) as res:raw=res.read()
if len(raw)<10000 or len(raw)>1000000:raise ValueError('Unexpected model file size')
model.write_bytes(raw)
sr=cv2.dnn_superres.DnnSuperResImpl_create();sr.readModel(str(model));sr.setModel('fsrcnn',2)
cv2.setNumThreads(2)
rows=[]
def save(im,path,quality=93):
    im.save(path,'WEBP',quality=quality,method=6)
    actual=Image.open(path);actual.load()
    if actual.size!=im.size:raise ValueError('Image dimensions changed during encoding')
    rows.append({'path':str(path.relative_to(ROOT)),'width':im.width,'height':im.height,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
for name in ['hero']+[f'repair-{i}' for i in range(6)]:
    src=ROOT/f'assets/art-v1/{name}.jpg'
    img=cv2.imread(str(src))
    if img is None:raise ValueError('Missing/invalid source '+str(src))
    result=sr.upsample(img)
    if result.shape[:2]!=(img.shape[0]*2,img.shape[1]*2):raise ValueError('Incorrect SR output size')
    im=Image.fromarray(cv2.cvtColor(result,cv2.COLOR_BGR2RGB))
    save(im,OUT/f'{name}.webp')
    print(name,im.size,flush=True)
    if name.startswith('repair-'):
        thumb=im.copy();thumb.thumbnail((480,360),Image.Resampling.LANCZOS)
        save(thumb,OUT/f'thumb-{name.split("-")[-1]}.webp',88)
manifest={'method':'FSRCNN neural super-resolution x2 from existing 1440px masters; reconstructed detail, not native-resolution new art','model_source':MODEL_URL,'model_sha256':hashlib.sha256(raw).hexdigest(),'files':rows}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
