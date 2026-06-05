# AGENTS.md - skin-care-companion

## 適用範囲

このファイルはリポジトリ全体に適用します。参照元の
`MasanoriSuda/virtual_voicebot` の「仕様駆動」「境界を守る」「テストで閉じる」
運用をベースにしますが、このリポジトリでは Claude Code は使わず Codex のみで
仕様、実装、テスト、README 更新を扱います。

## 目的

Zennfes Spring 2026 / YouCam API 向けの MVP として、元美容部員の知見を活かした
肌ケア伴走アプリと xangi/Discord 連携用 API を実装します。

## 仕様駆動の進め方

- 非自明な変更では `docs/steering/STEER-*.md` または README の受け入れ条件を先に確認する。
- ユーザーが今回のように具体的な目的、前提、受け入れ条件を直接提示した場合は、それを合意済み仕様として扱ってよい。
- 仕様とコードが矛盾する場合は、最新のユーザー指示、`docs/steering/`、README、コードの順に確認する。
- 仕様が曖昧でプライバシー、API契約、データ永続化に影響する場合は、推測で広げず質問する。
- 実装後は変更した仕様、README、テストが同じ振る舞いを説明しているか確認する。

## ディレクトリと責務

- `apps/mobile/`: Flutter アプリ。日本語UI、画像選択/カメラ、問診、診断結果、推薦、過去ログ表示を担当。
- `apps/api/`: FastAPI バックエンド。画像受領、YouCam adapter、SQLite、推薦、xangi/Discord向け要約APIを担当。
- `apps/api/app/youcam/`: YouCam API adapter。実API仕様の不確実性はここに閉じ込める。
- `apps/api/app/recommendation/`: 推薦ロジック。DBに存在する商品だけ返す。
- `apps/api/app/rag/`: Retriever interface と実装。将来のベクトル検索差し替え点。
- `apps/api/app/db/`: SQLite schema/seed。
- `docs/`: 設計メモ、steering、Zenn記事下書き。
- `skills/`: Codex向けのリポジトリ内スキル定義。

## セキュリティとプライバシー

- YouCam APIキー、LLM APIキー、Discord webhook は必ずバックエンド環境変数で管理する。
- Flutter アプリに APIキーや秘密値を埋め込まない。
- 顔写真は分析用の一時ファイルとして扱い、分析後に削除する。DBへ永続保存しない。
- Discord/xangi向けレスポンスには画像URL、画像パス、個人情報、手持ちアイテムの詳細を含めない。
- README には「医療診断ではなく美容アドバイス」と明記する。

## 実装ルール

- MVP優先。YouCam APIの正確な仕様が不明な場合は mock adapter で動作を維持する。
- 外部サービスI/Oは adapter 層に閉じ込め、timeout を設定する。
- RAG/推薦は SQLite の商品DBと美容部員メモを正とし、LLMやコードで商品を捏造しない。
- Flutter UIはスマホで自然に追える画面遷移にし、日本語表示にする。
- 変更は既存の責務境界に沿って小さく行う。

## 検証

- API変更時は `cd apps/api && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest` を実行する。
- Flutter変更時は `cd apps/mobile && flutter test` を実行する。
- 起動確認は mock モードを優先する。
- 最終報告には、実行したコマンドと成功/失敗、未実行なら理由を含める。
