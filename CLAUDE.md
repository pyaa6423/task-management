# CLAUDE.md

## プロジェクト概要
ガントチャート付きタスク管理アプリ（FastAPI + SQLite + Jinja2 + frappe-gantt）

## 技術スタック
- **Backend**: FastAPI (async), SQLAlchemy (async + aiosqlite), Pydantic
- **Frontend**: Jinja2テンプレート + frappe-gantt (ローカルパッチ済み `app/static/frappe-gantt.min.js`)
- **DB**: SQLite (`taskmanager.db`、起動時に自動作成)
- **テスト**: pytest + pytest-asyncio + httpx (インメモリSQLite)
- **パッケージ管理**: uv

## コマンド
- `uv run uvicorn app.main:app --reload` — 開発サーバー起動
- `uv run pytest -v` — テスト実行
- `uv run pytest --cov=app` — カバレッジ付きテスト
- `uv run python scripts/backup.py` — データバックアップ
- `uv run python scripts/restore.py` — データリストア

## データモデル
- **Project** → Task (1:N)
- **Task** → Task (self-referential parent_id, 階層無制限)
- **Task** → CheckItem (1:N, 達成項目)
- **Event** (予定、project_id nullable = 全体 or プロジェクト紐づき)
- カスケード削除: Project → Task → CheckItem
- 完了ルール: 未完了の子タスクがある場合、親タスクの完了を拒否
- 子タスク全完了時、親タスクを自動完了
- 完了済みタスクに子タスク追加時、親の完了を自動解除

## UI/デザインルール
- **任天堂風**: 白基調、アクセントカラー `#e60012`（任天堂レッド）
- 土日: 青(`#0068b7`)、日曜/祝日: 赤(`#e60012`)
- テーマ6種: Nintendo, Mario, Splatoon, Zelda, Kirby, Monochrome
- CSS は基本的に `app/static/style.css`、ページ固有のスタイルはテンプレート内 `<style>` ブロック

## frappe-gantt 注意事項
- **SVGのDOM位置をずらす操作は禁止** — 必ず追記のみ（詳細: `skills/frontend-gantt/`）
- 月名は日本語パッチ済み（`language: "ja"`)
- `popup_trigger: "manual"` でデフォルトポップアップ無効化
- `on_click` はダブルクリックで発火。シングルクリックは `addEventListener("click")` で捕捉

## ページ構成
| URL | 内容 |
|-----|------|
| `/gantt` | ガントチャート（トップページ、`/` からリダイレクト） |
| `/milestones` | マイルストーン タイムライン |
| `/events` | 予定管理 |
| `/tasks/{id}/checks` | 達成項目テーブル |
| `/projects/new` | プロジェクト追加 |
| `/projects/{id}/edit` | プロジェクト編集/削除 |
| `/projects/{id}/tasks/new` | タスク追加 |
| `/tasks/{id}/edit` | タスク編集/削除 |
| `/docs` | Swagger UI |

## API構成
- `/api/v1/projects` — プロジェクトCRUD
- `/api/v1/projects/{id}/tasks` — タスクCRUD
- `/api/v1/tasks/{id}/children` — 子タスクCRUD
- `/api/v1/tasks/{id}/checks` — 達成項目CRUD
- `/api/v1/checks/{id}` — 達成項目個別操作
- `/api/v1/events` — 予定CRUD
- `/api/v1/reports/daily|weekly|monthly` — レポート
- `/api/v1/gantt/overview` — 全プロジェクトガントデータ
- `/api/v1/gantt/projects/{id}` — プロジェクトガントデータ
- `/api/v1/gantt/tasks/{id}/children` — 子タスクガントデータ
- `/api/v1/milestones` — マイルストーンデータ

## 開発規約
- テスト: 変更後は必ず `uv run pytest -v` を実行
- DB変更時: `taskmanager.db` を削除して再起動（もしくは backup → restore）
- コミット: `Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>` を付与
- JSキャッシュ: 変更後はブラウザでハードリロード（Ctrl+Shift+R）が必要
- `--reload` 付きで起動すればPythonファイルの変更は自動反映

## スキル
- `skills/python-backend/` — Python バックエンドのパターン集
- `skills/frontend-gantt/` — frappe-gantt カスタマイズのノウハウ
- `skills/ui-customization/` — UI 調整の一般ガイド
