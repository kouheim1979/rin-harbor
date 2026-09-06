# リンハーバー DX

リンちゃんと港を育てる、オリジナルの合成アドベンチャーゲームです。

## 現在の完成版

- GitHub Pages / iPhone / Android 対応
- 外部ライブラリなし
- localStorage 自動保存
- 旧セーブデータ引き継ぎ
- 6×6 合成ボード
- ドラッグ合成 / タップ合成
- 1手戻す / ヒント
- コンボボーナス
- 注文 / 自動納品
- リン号 5 段階修理
- オリジナル修理アルバム
- 港のストーリー
- リン図鑑
- デイリーミッション / 連続プレイ
- 効果音 / 触覚フィードバック
- セーブバックアップ / 復元
- Service Worker によるオフライン対応

## オリジナルアート

タイトル画面とリン号の修理進行用イラストをオリジナル制作し、`assets/` に組み込んでいます。

- `assets/hero-opening.webp` : タイトル画面
- `assets/repair-stage-0.jpg` : 壊れたリン号
- `assets/repair-stage-1.webp` : 船体修理
- `assets/repair-stage-2.webp` : 船体補強
- `assets/repair-stage-3.webp` : マスト修理
- `assets/repair-stage-4.webp` : 仕上げ・清掃
- `assets/repair-stage-5.webp` : リン号完成

## 公開URL

https://kouheim1979.github.io/rin-harbor/

## データ

進行状況はブラウザの `localStorage` に保存します。DX版の保存キーは `rin_harbor_save_v10` で、旧版 `v5`〜`v8` からの読み込みにも対応しています。

## 開発方針

オリジナルキャラクター・オリジナル世界観・オリジナル画像で構成しています。既存ゲームの画像・文章・キャラクター・固有データは使用していません。
