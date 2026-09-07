"""Apply the Sea Journal UI to the verified r1 engine without changing saves/rules."""
from pathlib import Path
import re,json
R=Path(__file__).resolve().parents[1]
RELEASE='20260907-sea2'
code=(R/'game.js').read_text()
if "const RELEASE='20260906-r1'" not in code:
    raise RuntimeError('Unexpected engine revision: stop rather than overwrite newer work')
def replace_function(name,body):
    global code
    pattern=r'function '+re.escape(name)+r'\([^\n]*?\)[\s\S]*?(?=\nfunction |\nasync function |\n/\* Pointer)'
    code,count=re.subn(pattern,lambda m:body.rstrip()+'\n',code,count=1)
    if count!=1:raise RuntimeError('Missing function '+name)
code=code.replace("const RELEASE='20260906-r1'",f"const RELEASE='{RELEASE}'")
code=code.replace('${emojiOf(id)}','${itemArt(id)}').replace('${emojiOf(w.id)}','${itemArt(w.id)}').replace("${open?emojiOf(id):'❓'}","${open?itemArt(id):gameIcon('lock')}")
code=code.replace("drag.ghost.textContent=emojiOf(id)","drag.ghost.innerHTML=itemArt(id)")
code=code.replace("${isGen(id)?'<div class=\"tap\">TAP</div>'", "${isGen(id)?'<div class=\"tap\">材料</div>'")
code=code.replace("S.auto?'🤖 ON':'🤖 OFF'","S.auto?'自動 ON':'自動 OFF'")
code=code.replace("b.textContent=undoState?'↩️ '+undoLabel:'↩️ 戻す'","b.textContent='戻す';b.title=undoState?undoLabel+'を戻す':'戻せる操作なし'")
code=code.replace("$('streakBadge').textContent=`🔥 ${S.daily.streak}日`","$('streakBadge').textContent=`連続 ${S.daily.streak}日`")
code=code.replace("r>=5?'🚢 完成':'🔧 '+cost","r>=5?'修理完了':cost+' で修理'")
code=code.replace("${m.icon} ${esc(m.title)}","${gameIcon({generate:'ship',merge:'grid',deliver:'check'}[m.type])} ${esc(m.title)}")
code=code.replace("${data.icon} ${esc(data.label)}","${gameIcon({drink:'ship',dessert:'star',shell:'gem',fish:'anchor',toy:'compass'}[kind])} ${esc(data.label)}")
code=code.replace("${open?'📖':'🔒'} ${esc(s.t)}","${open?'●':'○'} ${esc(s.t)}")
replace_function('statsHtml',r'''function statsHtml(){
  const found=Object.keys(ITEMS).filter(id=>S.book[id]).length;
  return `<div class="stat"><small>コイン</small><b>${gameIcon('coin')}${S.coins}</b></div><div class="stat"><small>星</small><b>${gameIcon('star')}${S.stars}</b></div><div class="stat"><small>レベル</small><b>Lv.${S.level}</b></div><div class="stat"><small>船の修理</small><b>${S.repair}/5</b></div><div class="stat"><small>お宝</small><b>${found}/53</b></div>`;
}''')
replace_function('miniStatsHtml',r'''function miniStatsHtml(){
  return `<span>${gameIcon('coin')}${S.coins}</span><span>${gameIcon('star')}${S.stars}</span><span>Lv.${S.level}</span>${combo>1?`<span class="combo">${combo}コンボ!</span>`:''}`;
}''')
code=code.replace("$('miniStats').innerHTML=miniStatsHtml();", "$('miniStats').innerHTML=miniStatsHtml();$('gameXp').style.width=Math.min(100,S.xp/xpThreshold()*100)+'%';")
code=code.replace("return `assets/art-v1/repair-${int(stage,0,5)}.jpg`", "return `assets/art-hd/repair-${int(stage,0,5)}.webp`")
# Album thumbnails are kept small; the opened scene always uses the high-resolution master.
code=code.replace('src="${bestStagePath(i)}"','src="assets/art-hd/thumb-${i}.webp"')
code=code.replace("renderDaily();\n}","renderDaily();$('repairJourney').innerHTML=Array.from({length:5},(_,i)=>`<span class=\"${i<S.repair?'complete':i===S.repair?'current':''}\">${i<S.repair?'✓':i+1}</span>`).join('');\n}",1)
(R/'game.js').write_text(code)
# Preserve the complete DOM/API contract of the tested engine, with a redesigned structure.
html=(R/'index.html').read_text()
html=re.sub(r'<link rel="stylesheet"[^>]+>\s*','',html)
html=html.replace('</head>','<link rel="stylesheet" href="youth.css?v=sea2">\n</head>')
html=html.replace('#071622','#eaf6f1').replace('assets/art-v1/hero.jpg','assets/art-hd/hero.webp')
html=html.replace('RIN HARBOR · ADVENTURE','RIN HARBOR ／ SEA JOURNAL')
html=html.replace('A HARBOR MERGE ADVENTURE','ひとつ合成。ひとつ冒険。')
html=html.replace('小さな港から、大きな物語へ。リン号をよみがえらせる、あなたとリンの冒険。','この港のつづきは、きみとリンで。')
html=html.replace('<div class="openingCopy">','<div class="titleCompass" aria-hidden="true"><svg class="uiIcon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><path d="m16 8-2 6-6 2 2-6Z"/></svg></div><div class="openingCopy">')
html=html.replace('alt="リンとリン号が待つ夕暮れの港"','alt="リンとリン号が待つ夕暮れの港" width="2880" height="1620"')
html=html.replace('リンといっしょに、もう一度この船を海へ。','セーブは自動。自分のペースで冒険しよう。')
html=html.replace('<span class="eyebrow">HARBOR BASE</span><div class="title">リンハーバー</div><div class="sub">今日の港とリン号</div>','<span class="eyebrow">おかえり、キャプテン。</span><div class="title">リンの港</div>')
# Only the home heading receives the homeWelcome class.
home_start=html.index('<section id="screenHome"')
p=html.index('<div class="top">',home_start)
html=html[:p]+html[p:].replace('<div class="top">','<div class="top homeWelcome">',1)
html=html.replace('<b id="repairTitle">','<div class="tiny">次の目標</div><b id="repairTitle">')
html=html.replace('<div id="statsHome"','<div id="repairJourney" class="repairJourney" aria-label="修理の進み具合"></div><div id="statsHome"')
html=html.replace('<div class="homeGrid">','<button class="playBanner" data-go="game"><span><small>材料を集めて、船をよみがえらせよう</small><strong>合成して遊ぶ</strong></span><span aria-hidden="true">→</span></button><div class="homeGrid">')
html=html.replace('>物語と修理</b>','>冒険のきろく</b>').replace('>リン図鑑</b>','>お宝コレクション</b>')
html=html.replace('>MERGE DECK</span>','>つくって、届けて、港を育てる</span>').replace('>合成デッキ</div>','>合成アトリエ</div>')
html=html.replace('<div id="miniStats" class="miniStats"></div>','<div id="miniStats" class="miniStats"></div><div class="xpRail" aria-label="次のレベルまで"><i id="gameXp"></i></div>')
board=re.search(r'      <div class="boardBox">.*?</div></div>\n',html).group(0)
html=html.replace(board,'')
a=html.index('      <div class="controls">')
html=html[:a]+board+html[a:]
html=html.replace('<div class="orderStrip">','<div class="orderStrip"><div class="requestAvatar" aria-hidden="true"><svg class="uiIcon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M3 7h18v13H3zM3 7l9 7 9-7M8 4h8"/></svg></div>')
for a,b in [('🚢 納品','お届け'),('🤖 ON','自動 ON'),('💡 ヒント','ヒント'),('↩️ 戻す','戻す'),('🧺 整列','整列'),('🪙 売る','売る'),('>HARBOR REQUESTS</span>','>材料を届けて、港のみんなを笑顔に</span>'),('>注文</div>','>みんなのお願い</div>'),('>HARBOR STORY</span>','>少しずつ広がる、港の物語</span>'),('>物語</div>','>冒険のきろく</div>'),('>COLLECTION</span>','>まだ見ぬお宝を、見つけに行こう</span>'),('>リン図鑑</div>','>お宝コレクション</div>'),('2026.09.06-r1','2026.09.07 Sea Journal')]: html=html.replace(a,b)
html=html.replace('<script src="game.js?v=20260906r1"></script>','<script src="item-art.js?v=sea2"></script>\n<script src="game.js?v=sea2"></script>')
(R/'index.html').write_text(html)
# Complete versioned offline package; old assets and saves are deliberately retained.
sw=(R/'sw.js').read_text().replace("const VERSION='20260906-r1'",f"const VERSION='{RELEASE}'")
sw=re.sub(r'const CORE=\[.*?\];',"const CORE=['index.html','youth.css?v=sea2','item-art.js?v=sea2','game.js?v=sea2','manifest.webmanifest','assets/art-hd/hero.webp',...Array.from({length:6},(_,i)=>`assets/art-hd/repair-${i}.webp`),...Array.from({length:6},(_,i)=>`assets/art-hd/thumb-${i}.webp`),'assets/art-v1/icon-180.png','assets/art-v1/icon-192.png','assets/art-v1/icon-512.png'];",sw)
(R/'sw.js').write_text(sw)
man=json.loads((R/'manifest.webmanifest').read_text());man.update(name='リンハーバー',description='つくって、届けて、港を育てる。リンと一緒に楽しむ合成アドベンチャー。',background_color='#eaf6f1',theme_color='#eaf6f1')
(R/'manifest.webmanifest').write_text(json.dumps(man,ensure_ascii=False,indent=2)+'\n')
# Regression tests still cover the same game rules and previous saves.
t=(R/'tests/smoke.py').read_text().replace('20260906-r1',RELEASE)
old="board['y']+board['height']<=nav['y']+1 and board['x']+board['width']<=w+1 and boxes['#msg']['y']+boxes['#msg']['height']<=nav['y']+1"
new="board['x']+board['width']<=w+1 and (board['y']+board['height']<=nav['y']+1 or board['x']+board['width']<=nav['x']+1) and (boxes['#msg']['y']+boxes['#msg']['height']<=nav['y']+1 or boxes['#msg']['x']+boxes['#msg']['width']<=nav['x']+1)"
assert old in t;t=t.replace(old,new)
t=t.replace("if INLINE:options.update(executable_path='/usr/bin/chromium',args=['--no-sandbox'])","if INLINE or os.environ.get('SYSTEM_CHROMIUM')=='1':options.update(executable_path='/usr/bin/chromium',args=['--no-sandbox'])")
(R/'tests/smoke.py').write_text(t)
f=R/'tests/origin_offline.py';f.write_text(f.read_text().replace('20260906-r1',RELEASE))
# Small visual corrections discovered in the mobile screenshot review.
css=R/'youth.css'
text=css.read_text().replace('--teal:#168d8b','--teal:#087c79').replace('--muted:#648186','--muted:#58757a')
text+='\n.menuIcon svg{width:28px;height:28px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}\n'
css.write_text(text)
# Keep existing gates and add a visual/HD-specific gate for both PR and public app.
wf=R/'.github/workflows/verify-game.yml'
if wf.exists():
    y=wf.read_text().replace("'assets/art-v1/**'", "'assets/art-v1/**', 'assets/art-hd/**'")
    y=y.replace('node --check game.js','node --check game.js\n          node --check item-art.js')
    y=y.replace('run: python3 tests/smoke.py', 'run: |\n          python3 tests/smoke.py\n          python3 tests/youth.py')
    wf.write_text(y)
(R/'README.md').write_text('''# リンハーバー — Sea Journal

小学高学年向けの、海の冒険と合成を楽しむゲームです。

## 今回の更新
- アイボリー・海のグリーンを使った画面に刷新。暗いパネルや英語中心の見出しを廃止。
- 港、次の修理目標、遊ぶボタンを中心に整理。ゲーム盤面はスマホの実寸に合わせます。
- 53アイテムはブラウザ内のオリジナルSVGイラスト。表示倍率によるぼやけがありません。
- タイトルと修理イラストは、元の1440px画像をFSRCNNで縦横2倍に再構成。タイトル2880×1620、修理6枚2880×2160。新規に描いたネイティブ4K画像ではありません。
- 拡大アルバムは高解像度版、一覧は480×360の軽量サムネイルを使用。
- 全画像、ゲーム、操作、バックアップ復元、オフライン再起動をGitHub Actionsで検証します。

## データ
保存キー `rin_harbor_save_v10` は変更しません。旧セーブは引き継ぎ、移行前の控えも残します。UI更新でプレイヤーデータを初期化しません。

## 構成
`index.html` / `youth.css` / `item-art.js` / `game.js` / `sw.js` / `assets/art-hd/`。以前の素材も履歴と互換性のため残しています。

## 画像処理
OpenCV dnn_superres の FSRCNN x2 を使用。モデルの出典とSHA-256、各出力画像の寸法・バイト数・SHA-256は `assets/art-hd/manifest.json` に記録しています。
モデル: https://github.com/Saafke/FSRCNN_Tensorflow （Apache-2.0）
OpenCV: https://docs.opencv.org/4.x/d5/d29/tutorial_dnn_superres_upscale_image_single.html

## 検証
`python tests/smoke.py` と `python tests/youth.py`。
Playwright Chromium / WebKit の自動テストです。iPhone実機のテストではありません。
公開先: https://kouheim1979.github.io/rin-harbor/
''')
print('Sea Journal UI applied; save keys and gameplay rules unchanged.')
