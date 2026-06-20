# 旧UI（任天堂風）の保全と復帰方法

2026-06 に UI を「任天堂風（白基調・赤 `#e60012`・上部ナビ）」から
「モダンなダークダッシュボード（左サイドバー＋ライト/ダーク切替）」へ全面リデザインした。

旧UIはいつでも戻せるように保全してある。

## 完全に旧UIへ戻す（推奨）
リデザイン直前のコミットに `ui-legacy-nintendo` タグを打ってある。
テンプレート・CSS をまとめてそのタグの状態に戻す:

```bash
git checkout ui-legacy-nintendo -- app/templates app/static/style.css
```

※ 各ページのテンプレートも新トークン参照に変換済みのため、`base.html` と
`style.css` だけ戻しても完全には復元できない。必ず上記でまとめて戻すこと。

## このフォルダのファイル
- `base.nintendo.html` — 旧 `app/templates/base.html`（上部ナビ・シェル）の参照用コピー
- `style.nintendo.css` — 旧 `app/static/style.css`（白基調テーマ）の参照用コピー

参照用スナップショット。実際の復帰は上のタグ checkout を使う。

## ライト/ダークの切替（新UI内）
新UIは右下サイドバーのトグル、または `localStorage["ui-theme"]`（`dark`/`light`）で切替。
旧・任天堂風UIとは別物（新UIの明暗テーマ）。
