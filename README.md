# リンハーバー — Sea Journal

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
