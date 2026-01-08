# データ取得スクリプト テストガイド

## 前提条件

### 1. 依存関係のインストール

```bash
# プロジェクトルートで実行
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env` ファイルを作成し、以下の設定を追加:

```bash
DATABASE_URL=postgresql://user:password@localhost:5434/vulnerability_db
JVN_API_ENDPOINT=https://jvndb.jvn.jp/myjvn
LOG_LEVEL=INFO
```

### 3. データベースの準備

```bash
# PostgreSQLコンテナの起動（docker-compose使用の場合）
docker-compose up -d postgres

# テーブル作成（Alembicマイグレーション使用の場合）
alembic upgrade head

# または、Pythonスクリプトで直接作成
python -c "from src.database import init_db; init_db()"
```

## テストシナリオ

### シナリオ 1: 構文チェック

スクリプトが正しく動作するか、基本的な構文チェックを行います。

```bash
# Python構文チェック
python -m py_compile scripts/fetch_vulnerabilities.py

# ヘルプ表示（依存関係がインストールされていれば動作）
python scripts/fetch_vulnerabilities.py --help
```

**期待される結果**:
- 構文エラーがないこと
- ヘルプメッセージが表示されること

### シナリオ 2: 少量データ取得テスト（10件）

実際にJVN iPedia APIから少量のデータを取得し、データベースに保存します。

```bash
# 10件のみ取得（テスト用）
python scripts/fetch_vulnerabilities.py --differential --max-items 10 --log-level DEBUG
```

**期待される結果**:
```
2026-01-08 15:00:00 - __main__ - INFO - === Vulnerability Data Fetch Started ===
2026-01-08 15:00:00 - __main__ - INFO - Checking database connection...
2026-01-08 15:00:00 - __main__ - INFO - Database connection successful
2026-01-08 15:00:00 - __main__ - INFO - Fetch mode: DIFFERENTIAL (only new/updated data)
2026-01-08 15:00:01 - src.fetchers.jvn_fetcher - INFO - Starting vulnerability fetch...
2026-01-08 15:00:05 - src.fetchers.jvn_fetcher - INFO - Fetched 10 vulnerabilities from API
2026-01-08 15:00:06 - src.services.database_vulnerability_service - INFO - Batch UPSERT completed: inserted=10, updated=0, failed=0
2026-01-08 15:00:06 - __main__ - INFO - === Vulnerability Data Fetch Completed ===
2026-01-08 15:00:06 - __main__ - INFO - Fetched: 10 vulnerabilities
2026-01-08 15:00:06 - __main__ - INFO - Inserted: 10 new records
2026-01-08 15:00:06 - __main__ - INFO - Updated: 0 existing records
2026-01-08 15:00:06 - __main__ - INFO - Failed: 0 errors
2026-01-08 15:00:06 - __main__ - INFO - Elapsed time: 5.23 seconds
```

**確認項目**:
- [ ] 終了コード 0 (成功)
- [ ] データベースに10件のレコードが挿入されたこと
- [ ] エラーログが出力されていないこと

### シナリオ 3: データベース確認

取得したデータがデータベースに正しく保存されているか確認します。

```bash
# PostgreSQLに接続してデータ確認
psql $DATABASE_URL -c "SELECT cve_id, title, severity, cvss_score FROM vulnerabilities LIMIT 10;"
```

**期待される結果**:
```
       cve_id       |                   title                    | severity | cvss_score
--------------------+--------------------------------------------+----------+------------
 CVE-2024-0001      | Example Vulnerability Title                | High     |        7.5
 CVE-2024-0002      | Another Vulnerability                      | Critical |        9.8
...
```

**確認項目**:
- [ ] CVE IDが正しく保存されていること
- [ ] タイトル、深刻度、CVSSスコアが正しいこと
- [ ] 日付フィールド（published_date, modified_date）が正しいこと

### シナリオ 4: 差分取得テスト（UPSERT動作確認）

同じデータを再度取得し、UPSERTが正しく動作するか確認します。

```bash
# 1回目: 新規挿入
python scripts/fetch_vulnerabilities.py --differential --max-items 10

# 2回目: 更新（同じデータを再取得）
python scripts/fetch_vulnerabilities.py --differential --max-items 10
```

**期待される結果（2回目）**:
```
2026-01-08 15:00:06 - src.services.database_vulnerability_service - INFO - Batch UPSERT completed: inserted=0, updated=10, failed=0
2026-01-08 15:00:06 - __main__ - INFO - Inserted: 0 new records
2026-01-08 15:00:06 - __main__ - INFO - Updated: 10 existing records
```

**確認項目**:
- [ ] inserted=0, updated=10 (新規挿入ではなく更新)
- [ ] データベースのレコード数が増えていないこと

### シナリオ 5: エラーハンドリングテスト

#### 5-1. データベース接続エラー

```bash
# 不正なDATABASE_URLで実行
DATABASE_URL=postgresql://invalid:invalid@localhost:9999/invalid python scripts/fetch_vulnerabilities.py --differential --max-items 1
```

**期待される結果**:
```
2026-01-08 15:00:00 - __main__ - ERROR - Database connection failed
2026-01-08 15:00:00 - __main__ - ERROR - Please check DATABASE_URL in .env file
```

**確認項目**:
- [ ] 終了コード 2 (データベースエラー)
- [ ] エラーメッセージが表示されること

#### 5-2. API接続エラー（テスト困難）

JVN iPedia APIが利用不可の場合、リトライロジックが動作することを確認します。

```bash
# 不正なエンドポイントで実行（環境変数を一時的に変更）
JVN_API_ENDPOINT=https://invalid-api-endpoint.example.com python scripts/fetch_vulnerabilities.py --differential --max-items 1
```

**期待される結果**:
```
2026-01-08 15:00:01 - src.fetchers.jvn_fetcher - WARNING - Request error (attempt 1/3): ...
2026-01-08 15:00:06 - src.fetchers.jvn_fetcher - WARNING - Request error (attempt 2/3): ...
2026-01-08 15:00:16 - src.fetchers.jvn_fetcher - WARNING - Request error (attempt 3/3): ...
2026-01-08 15:00:16 - __main__ - ERROR - JVN API error: API request failed after 3 attempts
```

**確認項目**:
- [ ] 終了コード 1 (取得エラー)
- [ ] 3回リトライしていること
- [ ] 指数バックオフが動作していること（待機時間: 5秒、10秒、20秒）

### シナリオ 6: 本番想定テスト（差分取得モード）

本番環境での定期実行を想定したテストです。

```bash
# 差分取得モード（前回更新以降のデータのみ）
python scripts/fetch_vulnerabilities.py --differential
```

**期待される動作**:
1. データベースから最新の `modified_date` を取得
2. その日付以降のデータのみをJVN iPedia APIから取得
3. UPSERT処理で新規挿入または更新
4. 統計情報を出力

**確認項目**:
- [ ] 前回更新日時が正しく取得されること
- [ ] その日時以降のデータのみが取得されること
- [ ] UPSERT処理が正しく動作すること

### シナリオ 7: 全件取得テスト（初期データロード）

初回実行時や全データを再取得する場合のテストです。

```bash
# 過去3年分のデータを取得（デフォルト）
python scripts/fetch_vulnerabilities.py

# 全履歴データを取得（長時間かかる可能性あり）
# python scripts/fetch_vulnerabilities.py --all
```

**注意**: 全件取得は非常に時間がかかるため、初回実行時のみ推奨します。

**確認項目**:
- [ ] 指定期間のデータが全て取得されること
- [ ] ページネーション処理が正しく動作すること（50件ずつ取得）
- [ ] レート制限が守られていること（0.4秒間隔 = 2.5リクエスト/秒）

## GitHub Actionsでのテスト

### 手動実行テスト

1. GitHub リポジトリページで `Actions` タブを開く
2. `Daily Vulnerability Fetch` ワークフローを選択
3. `Run workflow` をクリック
4. パラメータを設定:
   - **Fetch mode**: `differential` (差分取得)
   - **Log level**: `DEBUG` (詳細ログ)
5. `Run workflow` を実行

**確認項目**:
- [ ] ワークフローが正常に開始されること
- [ ] データベース接続が成功すること
- [ ] データ取得が完了すること
- [ ] ログに統計情報が出力されること

### エラー通知テスト

意図的にエラーを発生させ、GitHub Issueが自動作成されることを確認します。

1. DATABASE_URLシークレットを一時的に無効化
2. 手動でワークフローを実行
3. ワークフローが失敗することを確認
4. GitHub Issuesに自動的にIssueが作成されることを確認

**確認項目**:
- [ ] ワークフローが失敗すること（赤いバツマーク）
- [ ] Issueが自動作成されること
- [ ] Issueタイトルに日付が含まれること
- [ ] Issue本文にエラー詳細が含まれること
- [ ] ラベル `bug`, `automation`, `vulnerability-fetch` が付与されること

## パフォーマンステスト

### レート制限の確認

```bash
# デバッグログでレート制限を確認
python scripts/fetch_vulnerabilities.py --differential --max-items 100 --log-level DEBUG | grep "Rate limiting"
```

**期待される結果**:
```
2026-01-08 15:00:01 - src.fetchers.jvn_fetcher - DEBUG - Rate limiting: sleeping for 0.40 seconds
2026-01-08 15:00:02 - src.fetchers.jvn_fetcher - DEBUG - Rate limiting: sleeping for 0.40 seconds
```

### 実行時間の測定

```bash
# 100件取得時の実行時間を測定
time python scripts/fetch_vulnerabilities.py --differential --max-items 100
```

**期待される結果**:
- 100件取得（2ページ）: 約10-15秒
- 500件取得（10ページ）: 約40-60秒

**計算式**:
- 1ページ = 50件
- 1リクエスト = 0.4秒（レート制限） + API応答時間（約2-3秒）
- 総実行時間 ≈ (ページ数 × 3秒) + データベース保存時間

## トラブルシューティング

### よくあるエラーと解決方法

#### 1. ModuleNotFoundError: No module named 'sqlalchemy'

**原因**: 依存関係がインストールされていない

**解決方法**:
```bash
pip install -r requirements.txt
```

#### 2. Database connection failed

**原因**: DATABASE_URLが正しくない、またはデータベースが起動していない

**解決方法**:
```bash
# .env ファイルを確認
cat .env | grep DATABASE_URL

# PostgreSQLコンテナを起動
docker-compose up -d postgres

# 接続テスト
psql $DATABASE_URL -c "SELECT 1;"
```

#### 3. UPSERT failed: duplicate key value violates unique constraint

**原因**: CVE IDの重複（通常は発生しない）

**解決方法**:
```bash
# データベースの一貫性を確認
psql $DATABASE_URL -c "SELECT cve_id, COUNT(*) FROM vulnerabilities GROUP BY cve_id HAVING COUNT(*) > 1;"

# 重複データを削除（必要に応じて）
psql $DATABASE_URL -c "DELETE FROM vulnerabilities WHERE id NOT IN (SELECT MIN(id) FROM vulnerabilities GROUP BY cve_id);"
```

## チェックリスト

実装完了後、以下の項目を確認してください:

### 基本動作
- [ ] スクリプトが正常に起動すること
- [ ] ヘルプメッセージが表示されること
- [ ] データベース接続が確認できること

### データ取得
- [ ] JVN iPedia APIからデータを取得できること
- [ ] XMLパース処理が正しく動作すること
- [ ] ページネーション処理が正しく動作すること

### データベース操作
- [ ] UPSERT処理が正しく動作すること（新規挿入）
- [ ] UPSERT処理が正しく動作すること（更新）
- [ ] トランザクション管理が正しく動作すること

### エラーハンドリング
- [ ] データベース接続エラーが適切に処理されること
- [ ] API接続エラーが適切に処理されること
- [ ] リトライ処理が正しく動作すること

### GitHub Actions
- [ ] 定期実行（cron）が設定されていること
- [ ] 手動実行（workflow_dispatch）が動作すること
- [ ] エラー時にIssueが自動作成されること

### ログ出力
- [ ] 適切なログレベルで出力されること
- [ ] 統計情報が出力されること
- [ ] エラー詳細が出力されること

---

**作成日**: 2026-01-08
**最終更新日**: 2026-01-08
