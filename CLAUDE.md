# プロジェクト設定

## 基本設定
```yaml
プロジェクト名: 脆弱性管理システム（Phase 1: 脆弱性情報取得基盤）
開始日: 2026-01-07
技術スタック:
  backend: Python 3.11+, FastAPI, SQLAlchemy
  database: PostgreSQL 15+ (Neon)
  frontend: FastAPI + Jinja2（簡易UI）
  testing: pytest, pytest-cov
  ci_cd: GitHub Actions
```

## 開発環境
```yaml
ポート設定:
  # 複数プロジェクト並行開発のため、一般的でないポートを使用
  backend: 8347
  database: 5434

環境変数:
  設定ファイル: .env（ルートディレクトリ）
  必須項目:
    - DATABASE_URL: PostgreSQL接続文字列
    - JVN_API_ENDPOINT: https://jvndb.jvn.jp/myjvn（デフォルト値あり）
    - LOG_LEVEL: INFO（デフォルト値あり）
```

## 外部サービス
```yaml
必須サービス:
  JVN_iPedia_API:
    エンドポイント: https://jvndb.jvn.jp/myjvn
    認証: 不要
    レート制限: 明示的制限なし（推奨: 秒間2-3リクエスト）

  PostgreSQL_Neon:
    取得先: https://neon.tech
    セットアップ: Phase 5で実施
    無料枠: あり

推奨サービス（Phase 2以降）:
  NVD_API:
    エンドポイント: https://services.nvd.nist.gov/rest/json/cves/2.0
    APIキー取得: https://nvd.nist.gov/developers/request-an-api-key

  CISA_KEV:
    エンドポイント: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
    認証: 不要
```

## コーディング規約

### 命名規則
```yaml
ファイル名:
  - モジュール: snake_case.py (例: vulnerability_fetcher.py)
  - テスト: test_*.py (例: test_vulnerability_fetcher.py)
  - 設定: snake_case (例: database.py, config.py)

変数・関数:
  - 変数: snake_case
  - 関数: snake_case
  - 定数: UPPER_SNAKE_CASE
  - クラス: PascalCase
```

### コード品質
```yaml
必須ルール:
  - 未使用の変数/import禁止
  - print文本番環境禁止（loggingモジュールを使用）
  - エラーハンドリング必須
  - 関数行数: 100行以下
  - ファイル行数: 700行以下
  - 複雑度(McCabe): 10以下
  - 行長: 120文字

フォーマット:
  - インデント: スペース4つ
  - クォート: シングル（docstringはダブル）
  - Linter: flake8
  - Formatter: black
  - Import整理: isort

テスト:
  - カバレッジ: 80%以上
  - テストフレームワーク: pytest
  - モック: pytest-mock
```

## プロジェクト固有ルール

### APIエンドポイント
```yaml
命名規則:
  - RESTful形式を厳守
  - 複数形を使用 (/vulnerabilities)
  - ケバブケースは不要（単一リソース）

ヘルスチェック:
  - エンドポイント: /api/health
  - 応答時間: 5秒以内
  - DB接続確認: 必須
```

### データベース
```yaml
テーブル命名:
  - snake_case（複数形）
  - 例: vulnerabilities

カラム命名:
  - snake_case
  - 日付: created_at, updated_at
  - ID: id（主キー）、cve_id（CVE識別子）

マイグレーション:
  - ツール: Alembic（SQLAlchemyと統合）
  - Phase 5で設定
```

### ロギング
```yaml
ログレベル:
  - ERROR: API障害、DB接続失敗、致命的エラー
  - WARNING: リトライ実行、部分的失敗
  - INFO: 処理開始/完了、取得件数、差分取得結果
  - DEBUG: 詳細なAPI応答、SQL実行内容

ログ出力:
  - フォーマット: JSON（本番環境）、テキスト（開発環境）
  - タイムスタンプ: ISO 8601形式
  - 機密情報の出力禁止（APIキー、パスワード等）
```

## 🆕 最新技術情報（知識カットオフ対応）
```yaml
# Web検索で解決した破壊的変更を記録

Python 3.11以降の注意点:
  - xml.etree.ElementTree: 標準ライブラリ、JVN iPedia APIのXMLパース用
  - httpx推奨: requestsより非同期対応が優れている
  - pydantic v2: FastAPIでのバリデーション（v1から破壊的変更あり）

SQLAlchemy 2.0系:
  - 2.0スタイル推奨（select(), sessionmaker等）
  - 1.x系との非互換性に注意

FastAPI:
  - Pydantic v2対応（2023年以降）
  - async/awaitサポート（httpxとの組み合わせ推奨）

GitHub Actions:
  - actions/checkout@v4（最新）
  - actions/setup-python@v5（最新）
  - cron実行: "0 18 * * *"（日本時間午前3時 = UTC 18時）
```

## プロジェクト構造（予定）
```
zjs_project/
├── src/
│   ├── api/               # FastAPI エンドポイント
│   ├── models/            # SQLAlchemy モデル
│   ├── services/          # ビジネスロジック
│   ├── fetchers/          # API取得処理
│   ├── database.py        # DB接続設定
│   └── config.py          # 設定管理
├── tests/
│   ├── test_api/
│   ├── test_services/
│   └── test_fetchers/
├── docs/
│   ├── requirements.md    # 要件定義書
│   └── SCOPE_PROGRESS.md  # 進捗管理
├── .github/
│   └── workflows/
│       └── daily_fetch.yml # 定期実行
├── docker-compose.yml     # PostgreSQL環境
├── pyproject.toml         # プロジェクト設定
├── .flake8                # Linter設定
├── .env                   # 環境変数（Git管理外）
└── README.md              # セットアップ手順
```

## セキュリティ要件
```yaml
環境変数管理:
  - .envファイルを.gitignoreに追加
  - .env.exampleでテンプレート提供
  - 本番環境はGitHub Secrets使用

外部API呼び出し:
  - タイムアウト設定: 30秒
  - リトライ: 最大3回（指数バックオフ）
  - エラーログに機密情報含めない

データベース:
  - 接続文字列の環境変数化
  - SSL/TLS接続（本番環境）
  - パスワードの平文保存禁止

HTTPS:
  - 本番環境で強制
  - セキュリティヘッダー設定（Content-Security-Policy等）
```

## 開発フロー
```yaml
Phase_1: 要件定義（進行中 - 82%完了）
  - ✅ Step#1〜8完了
  - 🔄 Step#9: CLAUDE.md生成（完了）
  - 📋 Step#10: ページの深掘り（残り）

Phase_2: Git/GitHub管理
Phase_3: フロントエンド基盤（簡易UI）
Phase_4: ページ実装（P-001: 脆弱性一覧ページ）
Phase_5: バックエンドAPI実装
  - JVN iPedia API統合
  - PostgreSQL永続化
  - 差分取得ロジック
  - リトライ処理
Phase_6: テスト実装（カバレッジ80%以上）
Phase_7: CI/CD構築（GitHub Actions）
Phase_8: Docker環境構築
Phase_9: ドキュメント整備
Phase_10: リリース準備
Phase_11: 機能拡張（NVD API、CISA KEV統合）
```

---

**CLAUDE.md 作成日**: 2026-01-07
**最終更新日**: 2026-01-07
