# Task Management

ガントチャート付きタスク管理アプリ。Project > Task の階層構造で、タスクは自己参照による親子関係で何階層でもネスト可能。

## 機能

- **ガントチャート** — frappe-gantt ベース、Day/Week/Month 切り替え
- **全プロジェクト一覧** — 1つのガントチャートで全プロジェクトを俯瞰
- **タスクカード** — 完了トグル、進捗表示（2/3 完了）、ドリルダウン
- **カレンダー対応** — 土日祝グレー表示、曜日ラベル（2026年日本祝日対応）
- **6色テーマ** — Nintendo / Mario / Splatoon / Zelda / Kirby / Monochrome
- **レポートAPI** — 日報・週報・月報（メンバーフィルタ対応）
- **REST API** — OpenAPI ドキュメント自動生成（Swagger UI）

## 技術スタック

| 項目 | 技術 |
|------|------|
| バックエンド | FastAPI (async) |
| DB | SQLite + aiosqlite (SQLAlchemy async ORM) |
| フロント | Jinja2 + frappe-gantt |
| テスト | pytest + pytest-asyncio + httpx |
| パッケージ管理 | uv |

## セットアップ

### 必要なもの

- **Python 3.12 以上**
- **uv**（パッケージマネージャー）

### 1. Python のインストール

#### Windows

[python.org](https://www.python.org/downloads/) から Python 3.12+ をダウンロードしてインストール。

インストール時に **「Add Python to PATH」にチェック** を入れてください。

```powershell
# 確認
python --version
```

#### macOS

```bash
# Homebrew
brew install python@3.12

# または pyenv
pyenv install 3.12
```

### 2. uv のインストール

#### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

インストール後、ターミナルを再起動してください。

#### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. プロジェクトのセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/pyaa6423/task-management.git
cd task-management

# 依存関係のインストール（仮想環境も自動作成）
uv sync
```

### 4. 起動

```bash
uv run uvicorn app.main:app --reload
```

ブラウザで以下にアクセス:

| URL | 内容 |
|-----|------|
| http://localhost:8000/gantt | ガントチャート |
| http://localhost:8000/milestones | マイルストーン タイムライン |
| http://localhost:8000/events | 予定管理 |
| http://localhost:8000/docs | Swagger UI (API ドキュメント) |
| http://localhost:8000/health | ヘルスチェック |

### 5. テスト実行

```bash
uv run pytest -v
```

カバレッジ付き:

```bash
uv run pytest --cov=app --cov-report=term-missing
```

## 環境設定

`.env.example` をコピーして `.env` を作成:

```bash
cp .env.example .env
```

```env
DATABASE_URL=sqlite+aiosqlite:///./taskmanager.db
DEBUG=true
```

DB ファイル (`taskmanager.db`) はアプリ初回起動時に自動作成されます。

## API エンドポイント

### プロジェクト

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/v1/projects` | 一覧 |
| POST | `/api/v1/projects` | 作成 |
| GET | `/api/v1/projects/{id}` | 詳細 |
| PUT | `/api/v1/projects/{id}` | 更新 |
| DELETE | `/api/v1/projects/{id}` | 削除 |

### タスク

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/v1/projects/{id}/tasks` | プロジェクトのタスク一覧 |
| POST | `/api/v1/projects/{id}/tasks` | タスク作成 |
| GET | `/api/v1/tasks/{id}` | タスク詳細 |
| PUT | `/api/v1/tasks/{id}` | タスク更新 |
| DELETE | `/api/v1/tasks/{id}` | タスク削除 |
| GET | `/api/v1/tasks/{id}/children` | 子タスク一覧 |
| POST | `/api/v1/tasks/{id}/children` | 子タスク作成 |

### レポート

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/v1/reports/daily?date=2026-03-15` | 日報 |
| GET | `/api/v1/reports/weekly?start_date=...&end_date=...` | 週報 |
| GET | `/api/v1/reports/monthly?year=2026&month=3` | 月報 |

全エンドポイントの詳細は Swagger UI (`/docs`) で確認できます。

## バックアップ / リストア

サーバー起動中にデータを JSON ファイルにエクスポート・インポートできます。DB スキーマ変更時のデータ移行に使用します。

### バックアップ

```bash
# サーバー起動中に実行
uv run python scripts/backup.py
# → backup.json が作成される
```

別のサーバーに対して実行する場合:

```bash
uv run python scripts/backup.py http://localhost:8000
```

### リストア

```bash
# 1. DB を削除
rm taskmanager.db

# 2. サーバーを再起動（新しい DB が自動作成される）
uv run uvicorn app.main:app --reload

# 3. バックアップからデータを復元
uv run python scripts/restore.py
# → backup.json からデータが復元される
```

別のファイルから復元する場合:

```bash
uv run python scripts/restore.py my_backup.json http://localhost:8000
```

### バックアップに含まれるデータ

- プロジェクト（名前、説明、日付、メンバー、完了状態）
- タスク（入れ子構造を含む全階層）
- 達成項目（チェック状態、input/output/results/evidences）
- 予定（プロジェクト紐づき + 全体）

## データモデル

```
Project (1) ──→ (N) Task
                     │ parent_id (self-referential)
                     └──→ (N) Task (children)
                              └──→ (N) Task ...
```

### ビジネスルール

- **カスケード削除** — Project 削除 → 配下の全 Task 削除
- **完了制約** — 未完了の子タスクがある場合、親タスクの完了を拒否
- **completed_at** — `is_completed = true` 設定時に UTC で自動記録

## トラブルシューティング

### `Address already in use` エラー

前回のプロセスが残っています:

```bash
# macOS / Linux
lsof -ti:8000 | xargs kill

# Windows (PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process
```

### `No module named 'xxx'` エラー

仮想環境が有効になっていません。`uv run` を付けて実行してください:

```bash
uv run uvicorn app.main:app --reload
```

### DB をリセットしたい

```bash
rm taskmanager.db
# 再起動で自動作成
uv run uvicorn app.main:app --reload
```
