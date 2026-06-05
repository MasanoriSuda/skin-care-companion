# 011_make_mvp - Skin Care Companion MVP

Status: Implemented
Owner: Codex
Date: 2026-06-06

## 目的

Zennfes Spring 2026 / YouCam API 向けに、`skin-care-companion` のMVPを作る。
元美容部員の知見を活かした肌ケア伴走アプリとして、Flutterアプリ、FastAPIバックエンド、
SQLiteベースの推薦、xangi/Discord向け要約APIを mock モードで動かせる状態にする。

## 前提

- スマホ側はFlutter。
- 顔写真などセンシティブ情報はFlutterアプリとバックエンドだけで扱う。
- Discord/xangiには顔写真を流さず、診断結果の要約、リマインド、週次レポートだけを送る。
- YouCam APIキーやLLM APIキーはバックエンド側で管理し、Flutterには埋め込まない。
- YouCam APIの実キーがなくても動くように mock adapter を用意する。
- 今回は Claude Code を使わず、Codex のみで仕様、実装、検証を行う。

## 実装内容

### Flutterアプリ

- `apps/mobile/` にFlutterアプリを作成。
- 日本語UIで以下を実装。
  - 画像選択またはカメラ撮影。
  - 問診フォーム。
    - 肌悩み: 乾燥 / 赤み / 毛穴 / 皮脂 / くすみ / 敏感。
    - 予算。
    - 朝のケア時間。
    - 今使っているアイテム。
  - 診断結果画面。
  - 今日の朝ケア / 夜ケア提案。
  - 「買い足すなら1つだけ」推薦。
  - 過去ログ一覧。
- `API_BASE_URL` は `--dart-define` で注入し、APIキーは持たない。
- Android/iOS向けに画像選択・カメラ権限を追加。

### FastAPIバックエンド

- `apps/api/` にFastAPIアプリを作成。
- 実装API:
  - `POST /api/skin/analyze`
  - `POST /api/recommendations`
  - `GET /api/skin-logs`
  - `GET /api/skin-logs/latest`
  - `GET /api/reports/weekly`
  - `GET /health`
- `POST /api/skin/analyze` は multipart で画像と問診JSONを受け取り、YouCam adapterを呼ぶ。
- 画像は一時ファイルとして保存し、分析後に削除する。
- `UploadFile.close()` のasync closeが環境によってハングしたため、同期closeで安全に閉じる実装にした。
- `YOUCAM_MODE=mock` をデフォルトにし、APIキー未設定でも診断結果を返す。
- real adapter は `YOUCAM_MODE=real`、`YOUCAM_API_KEY`、`YOUCAM_ENDPOINT` が揃った場合だけ使う。

### RAG/推薦

- SQLite schema/seed を追加。
- seedデータ:
  - 商品DB。
  - 元美容部員メモ。
- `app/rag/base.py` に Retriever interface を用意。
- 初期実装は SQLite FTS + 単純スコアリング。
- 推薦はDBに存在する商品だけを返す。
- LLMが商品を捏造する余地をMVPでは作らない。

### セキュリティ/プライバシー

- `.env.example` を追加。
- APIキー、LLMキー、Discord webhook URL はバックエンド環境変数で扱う。
- 顔写真をDBへ永続保存しない。
- xangi/Discord向けレスポンスに画像URL、画像パス、個人情報を含めない。
- READMEに「医療診断ではなく美容アドバイス」と明記。

### ドキュメント/運用

- `AGENTS.md` をCodex-only運用向けに作成。
- repo内スキル `skills/skin-care-companion-mvp/SKILL.md` を作成。
- `README.md` に概要、アーキテクチャ、セットアップ、mock起動、Zenn記事向け説明ポイントを記載。
- `docs/design-memo.md` と `docs/zenn-draft.md` を追加。

## 検証結果

実行済み:

- `cd apps/api && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest`
  - 2 passed。
- `cd apps/api && .venv/bin/python -m py_compile ...`
  - 成功。
- `cd apps/api && .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
  - mockモード起動成功。
- `cd apps/mobile && flutter pub get`
  - 成功。
- `cd apps/mobile && dart format lib/main.dart test/widget_test.dart`
  - 成功。
- `cd apps/mobile && flutter analyze`
  - No issues。
- `cd apps/mobile && flutter test`
  - All tests passed。

補足:

- sandbox環境では、別コマンドから起動中uvicornのlocalhostへ接続できなかった。
- API疎通はendpoint関数の直接呼び出しテストで、画像分析、推薦、最新ログ要約、週次レポートまで確認した。

## 受け入れ条件との対応

- mockモードでバックエンドが起動する: 対応済み。
- Flutter側から問診と画像選択の流れが確認できる: 対応済み。
- 肌診断mock結果が返る: 対応済み。
- 推薦結果が表示される: 対応済み。
- xangi向けに最新ログ要約/週次レポートAPIがある: 対応済み。
- READMEを見ればローカルで試せる: 対応済み。

## 残課題

- YouCam実API仕様に合わせた `RealYouCamAdapter` のレスポンス正規化。
- Discord/xangiへの実送信処理。
- 商品DBと美容部員メモのseed拡充。
- 実機/エミュレータでの画像選択、カメラ、API接続確認。
- UIの詳細デザイン調整。

