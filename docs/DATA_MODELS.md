# データモデル設計書

## 概要

本プロジェクトのデータモデルは、JVN iPedia APIから取得した脆弱性情報を効率的に管理するために設計されています。FastAPI + SQLAlchemy + Pydanticの組み合わせにより、型安全性とバリデーションを確保しています。

---

## 1. SQLAlchemyモデル (`src/models/vulnerability.py`)

### Vulnerabilityテーブル

JVN iPedia APIから取得した脆弱性情報を永続化するテーブル。

#### カラム定義

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| `cve_id` | VARCHAR(20) | PRIMARY KEY, INDEX | CVE識別子（例: CVE-2024-0001） |
| `title` | VARCHAR(500) | NOT NULL | 脆弱性のタイトル |
| `description` | TEXT | NOT NULL | 脆弱性の詳細説明 |
| `cvss_score` | FLOAT | NULLABLE | CVSS基本値（0.0〜10.0） |
| `severity` | VARCHAR(20) | NULLABLE, INDEX | 重要度（Critical/High/Medium/Low） |
| `published_date` | TIMESTAMP WITH TIMEZONE | NOT NULL, INDEX | 公開日（JVN iPediaより） |
| `modified_date` | TIMESTAMP WITH TIMEZONE | NOT NULL, INDEX | 更新日（JVN iPediaより） |
| `affected_products` | JSON | NULLABLE | 影響を受ける製品情報 |
| `vendor_info` | JSON | NULLABLE | ベンダー情報 |
| `references` | JSON | NULLABLE | 参照リンク（JVN iPedia, NVD, CWE等） |
| `created_at` | TIMESTAMP WITH TIMEZONE | NOT NULL, DEFAULT NOW() | DB登録日時 |
| `updated_at` | TIMESTAMP WITH TIMEZONE | NOT NULL, DEFAULT NOW() | DB更新日時 |

#### インデックス

- **主キー**: `cve_id`
- **検索用インデックス**: `severity`, `published_date`, `modified_date`

#### バリデーションメソッド

- `validate_cve_id(cve_id: str) -> bool`: CVE ID形式チェック（CVE-YYYY-NNNNN）
- `validate_cvss_score(score: float) -> bool`: CVSS範囲チェック（0.0〜10.0）
- `validate_severity(severity: str) -> bool`: 重要度レベルチェック

---

## 2. Pydanticスキーマ (`src/schemas/vulnerability.py`)

### スキーマ一覧

#### 2.1 VulnerabilityBase

共通フィールドを定義する基底スキーマ。

**フィールド**:
- `title`: str（1〜500文字）
- `description`: str（1文字以上）
- `cvss_score`: Optional[float]（0.0〜10.0）
- `severity`: Optional[str]（Critical/High/Medium/Low）
- `published_date`: datetime
- `modified_date`: datetime
- `affected_products`: Optional[dict]
- `vendor_info`: Optional[dict]
- `references`: Optional[dict]

#### 2.2 VulnerabilityCreate

新規脆弱性レコード作成用スキーマ。

**追加フィールド**:
- `cve_id`: str（CVE-YYYY-NNNNN形式）

**バリデーション**:
- CVE ID形式チェック（正規表現: `^CVE-\d{4}-\d{4,}$`）

#### 2.3 VulnerabilityUpdate

既存脆弱性レコード更新用スキーマ。

**特徴**:
- 全フィールドがOptional（部分更新対応）

#### 2.4 VulnerabilityInDB

DB格納データのスキーマ。

**追加フィールド**:
- `cve_id`: str
- `created_at`: datetime
- `updated_at`: datetime

**設定**:
- `from_attributes = True`（SQLAlchemyモデルからの変換対応）

#### 2.5 VulnerabilityResponse

API応答用スキーマ（VulnerabilityInDBと同一）。

#### 2.6 VulnerabilityListResponse

ページネーション対応の一覧表示用スキーマ。

**フィールド**:
- `items`: List[VulnerabilityResponse]
- `total`: int（総件数）
- `page`: int（現在のページ番号）
- `page_size`: int（ページサイズ）
- `total_pages`: int（総ページ数）

#### 2.7 VulnerabilitySearchParams

検索・ソート条件のクエリパラメータスキーマ。

**フィールド**:
- `page`: int（1始まり）
- `page_size`: int（1〜100）
- `sort_by`: str（published_date/modified_date/severity/cvss_score）
- `sort_order`: str（asc/desc）
- `search`: Optional[str]（CVE IDまたはタイトルで部分一致検索）

---

## 3. データベース設定 (`src/database.py`)

### 主要機能

#### 3.1 エンジン設定

```python
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
```

- **接続プール**: 最大5接続、オーバーフロー10接続
- **ヘルスチェック**: `pool_pre_ping=True`で接続確認

#### 3.2 セッション管理

- `SessionLocal`: セッションファクトリ
- `get_db()`: FastAPI依存性注入用のジェネレータ

#### 3.3 ユーティリティ関数

- `init_db()`: テーブル初期化（開発・テスト用）
- `check_db_connection()`: ヘルスチェック（`/api/health`用）
- `close_db()`: 接続クリーンアップ

---

## 4. 設定管理 (`src/config.py`)

### Settings クラス

環境変数から設定を読み込むPydantic設定クラス。

#### 主要設定項目

**データベース**:
- `DATABASE_URL`: PostgreSQL接続文字列

**JVN iPedia API**:
- `JVN_API_ENDPOINT`: APIエンドポイント
- `JVN_API_TIMEOUT`: タイムアウト（30秒）
- `JVN_API_MAX_RETRIES`: リトライ回数（3回）
- `JVN_API_RETRY_DELAY`: リトライ間隔（5秒）

**NVD API（Phase 2以降）**:
- `NVD_API_ENDPOINT`: APIエンドポイント
- `NVD_API_KEY`: APIキー（任意）

**ロギング**:
- `LOG_LEVEL`: ログレベル（INFO）
- `LOG_FORMAT`: ログフォーマット

**アプリケーション**:
- `DEBUG`: デバッグモード
- `PORT`: ポート番号（8347）

**データ取得**:
- `FETCH_YEARS`: 取得期間（3年分）
- `FETCH_ALL_DATA`: 全期間取得フラグ

#### ユーティリティメソッド

- `configure_logging()`: ロギング設定
- `get_fetch_start_date()`: 取得開始日の計算
- `mask_sensitive_info()`: 機密情報のマスキング

---

## 5. データフロー

### 5.1 データ取得フロー（JVN iPedia API → DB）

```
JVN iPedia API
    ↓ (XML応答)
XMLパース処理
    ↓ (dict)
VulnerabilityCreateスキーマ
    ↓ (バリデーション)
Vulnerabilityモデル
    ↓ (UPSERT)
PostgreSQL
```

### 5.2 API応答フロー（DB → クライアント）

```
PostgreSQL
    ↓ (SQLAlchemyクエリ)
Vulnerabilityモデル
    ↓ (from_attributes=True)
VulnerabilityResponseスキーマ
    ↓ (JSON変換)
FastAPI応答
```

---

## 6. バリデーションルール

### 6.1 CVE ID

- **形式**: `CVE-YYYY-NNNNN`
- **正規表現**: `^CVE-\d{4}-\d{4,}$`
- **例**: `CVE-2024-0001`, `CVE-2023-12345`

### 6.2 CVSS基本値

- **範囲**: 0.0〜10.0
- **型**: float
- **任意**: True

### 6.3 重要度

- **有効値**: `Critical`, `High`, `Medium`, `Low`
- **任意**: True

### 6.4 日付

- **形式**: ISO 8601（YYYY-MM-DDTHH:MM:SSZ）
- **タイムゾーン**: UTC
- **必須**: `published_date`, `modified_date`

---

## 7. 使用例

### 7.1 新規脆弱性の作成

```python
from src.models import Vulnerability
from src.database import SessionLocal

vulnerability = Vulnerability(
    cve_id='CVE-2024-0001',
    title='Apache HTTP Server における任意のコード実行の脆弱性',
    description='Apache HTTP Server 2.4.58 以前のバージョンにおいて...',
    cvss_score=9.8,
    severity='Critical',
    published_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
    modified_date=datetime(2024, 1, 20, tzinfo=timezone.utc),
)

db = SessionLocal()
db.add(vulnerability)
db.commit()
db.close()
```

### 7.2 Pydanticバリデーション

```python
from src.schemas import VulnerabilityCreate

# 成功例
vulnerability_data = VulnerabilityCreate(
    cve_id='CVE-2024-0001',
    title='Apache HTTP Server における脆弱性',
    description='詳細な説明...',
    cvss_score=9.8,
    severity='Critical',
    published_date='2024-01-15T00:00:00Z',
    modified_date='2024-01-20T00:00:00Z',
)

# エラー例（CVE ID形式不正）
try:
    invalid_data = VulnerabilityCreate(
        cve_id='INVALID-ID',  # ValidationError
        ...
    )
except ValidationError as e:
    print(e)
```

---

**作成日**: 2026-01-07
**最終更新日**: 2026-01-07
