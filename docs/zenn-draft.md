# Zenn記事下書き: Skin Care Companion MVP

## 伝えたいこと

- 顔写真はスマホアプリとバックエンドだけで扱い、Discord/xangiには要約だけ送る設計にした。
- YouCam API の実仕様が未確定でも、adapter + mock でMVPを先に動かせる。
- LLMに商品を作らせず、SQLiteの商品DBに存在する候補だけを推薦する。
- 元美容部員メモを seed として入れ、最初はFTSとスコアリングで十分に検証できる。

## 構成

```text
Flutter -> FastAPI -> YouCam adapter
                |-> SQLite products / memos / skin logs
                |-> xangi/Discord safe summary endpoints
```

## デモの流れ

1. Flutterで写真を選ぶ。
2. 肌悩み、予算、朝のケア時間、手持ちアイテムを入力する。
3. mock診断を受け取る。
4. 今日の朝ケア、夜ケア、買い足すなら1つだけの推薦を見る。
5. xangi向け最新ログ要約と週次レポートAPIを叩く。

