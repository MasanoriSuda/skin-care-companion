# Skin Care Companion 設計メモ

## MVP境界

- 顔写真は Flutter と FastAPI の分析処理だけで扱う。
- SQLite には問診、診断結果、推薦結果のみ保存し、画像は保存しない。
- xangi/Discord には `GET /api/skin-logs/latest` と `GET /api/reports/weekly` の要約だけ渡す。
- YouCam API の実仕様は未確定のため、`youcam` adapter 配下に閉じ込める。

## API

- `POST /api/skin/analyze`: multipart で画像と問診JSONを受け、YouCam adapterを呼ぶ。mockがデフォルト。
- `POST /api/recommendations`: 肌診断結果と問診、または `skin_log_id` から推薦を作る。
- `GET /api/skin-logs`: 過去ログ一覧。
- `GET /api/skin-logs/latest`: xangi向け最新ログ要約。
- `GET /api/reports/weekly`: xangi向け週次レポート。

## 推薦

初期実装は SQLite seed + FTS + スコアリング。商品候補は `products` テーブルに存在するものだけを返す。
将来のベクトル検索差し替えは `app/rag/base.py` の Retriever interface で吸収する。

