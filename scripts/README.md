# Scripts Directory

このディレクトリには、脆弱性管理システムの自動化スクリプトが含まれています。

## fetch_vulnerabilities.py

JVN iPedia APIから脆弱性データを取得し、データベースに保存するスクリプトです。

### 前提条件

1. **環境変数の設定** (.envファイル)
   ```bash
   DATABASE_URL=postgresql://user:password@host:port/dbname
   JVN_API_ENDPOINT=https://jvndb.jvn.jp/myjvn
   LOG_LEVEL=INFO
   ```

2. **依存関係のインストール**
   ```bash
   pip install -r requirements.txt
   ```

### 使用方法

#### 基本的な使い方

```bash
# デフォルト: 過去3年分のデータを取得
python scripts/fetch_vulnerabilities.py

# 差分取得: 前回更新以降のデータのみ取得
python scripts/fetch_vulnerabilities.py --differential

# 全履歴データを取得
python scripts/fetch_vulnerabilities.py --all

# 特定期間のデータを取得
python scripts/fetch_vulnerabilities.py --start-date 2024-01-01 --end-date 2024-12-31

# 最大件数を指定（テスト用）
python scripts/fetch_vulnerabilities.py --differential --max-items 10

# ログレベルを指定
python scripts/fetch_vulnerabilities.py --differential --log-level DEBUG
```

#### コマンドライン引数

| 引数 | 説明 | デフォルト |
|------|------|-----------|
| `--differential` | 前回更新以降のデータのみ取得 | False |
| `--all` | 全履歴データを取得 | False |
| `--start-date` | 取得開始日 (YYYY-MM-DD) | 3年前 |
| `--end-date` | 取得終了日 (YYYY-MM-DD) | 今日 |
| `--max-items` | 最大取得件数（テスト用） | None（全件） |
| `--log-level` | ログレベル (DEBUG/INFO/WARNING/ERROR) | INFO |

### 終了コード

| コード | 説明 |
|--------|------|
| 0 | 成功 |
| 1 | 取得エラー（API障害、ネットワークエラー等） |
| 2 | データベースエラー |
| 3 | 設定エラー |

### GitHub Actionsでの使用

このスクリプトは `.github/workflows/daily_fetch.yml` で自動実行されます。

#### 定期実行
- 毎日日本時間 午前3時 (UTC 18時) に自動実行
- 差分取得モードで実行（新規・更新データのみ）

#### 手動実行
1. GitHub リポジトリページで `Actions` タブを開く
2. `Daily Vulnerability Fetch` ワークフローを選択
3. `Run workflow` をクリック
4. 取得モード（差分/全件）とログレベルを選択
5. `Run workflow` を実行

#### エラー通知
- スクリプト実行に失敗した場合、自動的にGitHub Issueが作成されます
- Issue には以下の情報が含まれます：
  - 実行日時
  - エラー詳細
  - ワークフロー実行ログへのリンク
  - 確認事項チェックリスト

### トラブルシューティング

#### データベース接続エラー

```
Database connection failed
```

**解決方法**:
1. `.env` ファイルの `DATABASE_URL` が正しいか確認
2. データベースサーバーが起動しているか確認
3. ネットワーク接続を確認

#### API エラー

```
JVN API error: API request failed after 3 attempts
```

**解決方法**:
1. JVN iPedia API が正常に応答しているか確認
2. ネットワーク接続を確認
3. レート制限に引っかかっていないか確認（スクリプトは自動的に0.4秒間隔でリクエスト）

#### XML パースエラー

```
XML parsing error: Failed to parse XML response
```

**解決方法**:
1. JVN iPedia API のレスポンス形式が変更されていないか確認
2. `--log-level DEBUG` でデバッグログを確認

### ログ出力例

```
2026-01-08 15:00:00 - __main__ - INFO - === Vulnerability Data Fetch Started ===
2026-01-08 15:00:00 - __main__ - INFO - Checking database connection...
2026-01-08 15:00:00 - __main__ - INFO - Database connection successful
2026-01-08 15:00:00 - __main__ - INFO - Fetch mode: DIFFERENTIAL (only new/updated data)
2026-01-08 15:00:01 - src.fetchers.jvn_fetcher - INFO - Starting vulnerability fetch: start_date=2024-01-01, end_date=2026-01-08
2026-01-08 15:00:05 - src.fetchers.jvn_fetcher - INFO - Fetched 150 vulnerabilities from API
2026-01-08 15:00:06 - src.services.database_vulnerability_service - INFO - Batch UPSERT completed: inserted=120, updated=30, failed=0
2026-01-08 15:00:06 - __main__ - INFO - === Vulnerability Data Fetch Completed ===
2026-01-08 15:00:06 - __main__ - INFO - Fetched: 150 vulnerabilities
2026-01-08 15:00:06 - __main__ - INFO - Inserted: 120 new records
2026-01-08 15:00:06 - __main__ - INFO - Updated: 30 existing records
2026-01-08 15:00:06 - __main__ - INFO - Failed: 0 errors
2026-01-08 15:00:06 - __main__ - INFO - Elapsed time: 5.23 seconds
```

## 開発者向け情報

### スクリプトの構造

```python
# メインフロー
main()
  ↓
parse_arguments()  # コマンドライン引数解析
  ↓
check_db_connection()  # データベース接続確認
  ↓
fetch_and_store()  # 非同期処理
  ↓
  ├─ JVNFetcherService.fetch_vulnerabilities()  # API データ取得
  └─ DatabaseVulnerabilityService.upsert_vulnerabilities_batch()  # データベース保存
```

### 依存サービス

- `src.fetchers.jvn_fetcher.JVNFetcherService`: JVN iPedia API データ取得
- `src.services.database_vulnerability_service.DatabaseVulnerabilityService`: データベース操作
- `src.database.SessionLocal`: データベースセッション管理
- `src.config.settings`: アプリケーション設定

### テスト方法

```bash
# 少量データでテスト（10件のみ取得）
python scripts/fetch_vulnerabilities.py --differential --max-items 10 --log-level DEBUG

# 特定日付範囲でテスト
python scripts/fetch_vulnerabilities.py --start-date 2024-01-01 --end-date 2024-01-31 --log-level DEBUG
```

---

**作成日**: 2026-01-08
**最終更新日**: 2026-01-08
