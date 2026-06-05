# STEER-001 Skin Care Companion MVP

Status: Approved

## Story

Zennfes Spring 2026 / YouCam API 向けに、元美容部員の知見を活かした肌ケア伴走アプリの
MVPを mock モードで動かせる状態にする。

## Scope

- Flutter アプリで画像選択/カメラ、問診、診断結果、今日の朝夜ケア、1商品推薦、過去ログを表示する。
- FastAPI で肌分析、推薦、過去ログ、xangi向け最新/週次要約APIを提供する。
- YouCam APIキー未設定でも mock adapter で動作する。
- SQLite seed の商品DBと美容部員メモだけから推薦する。
- 顔写真はDBへ永続保存しない。

## Acceptance Criteria

- mock モードでバックエンドが起動する。
- Flutter から問診と画像選択の流れを確認できる。
- 肌診断 mock 結果が返る。
- 推薦結果が表示される。
- xangi向けに最新ログ要約/週次レポートAPIがある。
- READMEを見ればローカルで試せる。

