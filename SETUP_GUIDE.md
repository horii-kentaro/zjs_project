# セットアップガイド - Phase 1 実装

## 実装完了ファイル

### バックエンド
- `/home/horii-kentaro/projects/zjs_project/src/main.py` - FastAPIアプリケーション
- `/home/horii-kentaro/projects/zjs_project/src/api/vulnerabilities.py` - 脆弱性API
- `/home/horii-kentaro/projects/zjs_project/src/services/mock_vulnerability_service.py` - モックサービス

### フロントエンド
- `/home/horii-kentaro/projects/zjs_project/src/templates/base.html` - ベーステンプレート
- `/home/horii-kentaro/projects/zjs_project/src/templates/vulnerabilities.html` - 脆弱性一覧ページ
- `/home/horii-kentaro/projects/zjs_project/src/static/css/style.css` - スタイルシート
- `/home/horii-kentaro/projects/zjs_project/src/static/js/main.js` - JavaScript

### 設定ファイル
- `/home/horii-kentaro/projects/zjs_project/requirements.txt` - 依存関係
- `/home/horii-kentaro/projects/zjs_project/run_server.sh` - 起動スクリプト

## セットアップ手順

### 0. 前提条件（WSL/Ubuntu）

Python 3.12の仮想環境パッケージをインストールする必要があります：

```bash
# python3-venvパッケージのインストール
sudo apt update
sudo apt install python3.12-venv -y
```

### 1. 仮想環境の作成とアクティブ化

```bash
cd /home/horii-kentaro/projects/zjs_project
python3 -m venv venv
source venv/bin/activate
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

必要なパッケージ:
- fastapi (FastAPIフレームワーク)
- uvicorn (ASGIサーバー)
- jinja2 (テンプレートエンジン)
- pydantic (バリデーション)
- pydantic-settings (設定管理)

### 3. 環境変数の設定

`.env`ファイルが作成されているか確認:

```bash
ls -la .env
```

必要に応じて設定を変更:

```bash
# デフォルト設定（モック動作のため変更不要）
DEBUG=False
LOG_LEVEL=INFO
PORT=8347
```

### 4. サーバーの起動

#### 方法1: 起動スクリプトを使用（推奨）

```bash
./run_server.sh
```

#### 方法2: 直接起動

```bash
python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8347 --reload
```

## 動作確認方法

### 1. ヘルスチェック

```bash
curl http://localhost:8347/api/health
```

期待される応答:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-07T...",
  "version": "1.0.0",
  "environment": {
    "debug": false,
    "port": 8347
  }
}
```

### 2. 脆弱性一覧ページ（HTML）

ブラウザで以下のURLにアクセス:

```
http://localhost:8347/
```

確認項目:
- ✅ 脆弱性一覧テーブルが表示される
- ✅ 検索ボックスが機能する（CVE IDまたはタイトルで検索）
- ✅ ソートドロップダウンが機能する（更新日、公開日、重要度）
- ✅ ページネーションが表示される
- ✅ 「詳細表示」ボタンをクリックするとモーダルが開く
- ✅ モーダルに詳細情報が表示される

### 3. API エンドポイント（JSON）

#### 脆弱性一覧取得

```bash
curl "http://localhost:8347/api/vulnerabilities?page=1&page_size=10"
```

#### 検索機能テスト

```bash
curl "http://localhost:8347/api/vulnerabilities?search=Apache&page=1&page_size=10"
```

#### ソート機能テスト

```bash
# 更新日（新しい順）
curl "http://localhost:8347/api/vulnerabilities?sort_by=modified_date&sort_order=desc"

# 重要度（高い順）
curl "http://localhost:8347/api/vulnerabilities?sort_by=severity&sort_order=desc"

# CVSSスコア（高い順）
curl "http://localhost:8347/api/vulnerabilities?sort_by=cvss_score&sort_order=desc"
```

#### 詳細情報取得

```bash
curl "http://localhost:8347/api/vulnerabilities/CVE-2024-0001"
```

### 4. API ドキュメント確認

ブラウザで以下のURLにアクセス:

```
http://localhost:8347/api/docs
```

Swagger UIでAPIドキュメントを確認できます。

## 機能一覧

### 実装済み機能
- ✅ 脆弱性一覧ページ（HTML + Jinja2）
- ✅ 検索機能（CVE ID、タイトル）
- ✅ ソート機能（更新日、公開日、重要度、CVSSスコア）
- ✅ ページネーション（1ページ50件）
- ✅ 詳細表示モーダル
- ✅ レスポンシブデザイン（mockupと同等）
- ✅ REST API（JSON）
- ✅ ヘルスチェックエンドポイント
- ✅ モックデータ（100件）
- ✅ エラーハンドリング
- ✅ ロギング

### Phase 5で実装予定
- 🔄 JVN iPedia API統合
- 🔄 PostgreSQL永続化
- 🔄 差分取得ロジック
- 🔄 リトライ処理

## トラブルシューティング

### ポート8347が使用中の場合

```bash
# ポート使用状況確認
lsof -i :8347

# .envファイルでポート変更
PORT=8348
```

### 依存関係のインストールエラー

```bash
# pipをアップグレード
pip install --upgrade pip

# 個別にインストール
pip install fastapi uvicorn jinja2 pydantic pydantic-settings
```

### テンプレートが見つからないエラー

プロジェクトルートディレクトリから起動していることを確認:

```bash
cd /home/horii-kentaro/projects/zjs_project
python3 -m uvicorn src.main:app --reload
```

## 次のステップ

Phase 2以降の実装:
1. Git hooks + CI/CD設定（Phase 2）
2. フロントエンド基盤（Phase 3）
3. バックエンドAPI実装（Phase 5）
4. テスト実装（Phase 6）
5. Docker環境構築（Phase 8）

## 技術スタック

- **バックエンド**: Python 3.11+, FastAPI, SQLAlchemy
- **フロントエンド**: Jinja2, JavaScript (Vanilla)
- **スタイル**: CSS (Roboto font, Material Icons)
- **サーバー**: Uvicorn (ASGI)
- **ポート**: 8347

## 参考情報

- FastAPI ドキュメント: https://fastapi.tiangolo.com/
- Jinja2 ドキュメント: https://jinja.palletsprojects.com/
- JVN iPedia API: https://jvndb.jvn.jp/apis/myjvn/
