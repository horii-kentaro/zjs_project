# CPEマッチング機能 - 要件定義書（Phase 2）

## 要件定義の作成原則
- **「あったらいいな」は絶対に作らない**
- **拡張可能性のための余分な要素は一切追加しない**
- **将来の「もしかして」のための準備は禁止**
- **今、ここで必要な最小限の要素のみ**

---

## 1. プロジェクト概要

### 1.1 成果目標
既存の脆弱性情報（JVN iPedia APIから取得したPostgreSQLデータ）と、自社の資産情報（ソフトウェア、ライブラリ、コンテナ）をCPE（Common Platform Enumeration）コードで自動マッチングし、「どの脆弱性が自社システムに影響するか」を即座に判定できるシステム。

### 1.2 成功指標

#### 定量的指標
- マッチング精度: 95%以上（既知のテストケースで検証）
- マッチング処理時間: 1,000資産 × 1,000脆弱性を5分以内
- CPEコード生成成功率: 90%以上（Composer/NPM/Dockerファイルから）
- マッチング結果の冪等性: 同一データで3回実行してデータ不整合ゼロ

#### 定性的指標
- 運用性: エンジニアが10分以内に資産登録からマッチング結果確認まで完了可能
- 視認性: ダッシュボードで影響資産数・重要度を即座に把握可能
- 拡張性: 将来的なNVD API、CISA KEVデータとの統合を阻害しない設計

---

## 2. システム全体像

### 2.1 主要機能一覧
- **資産管理**: 手動登録、ファイルアップロード（Composer/NPM/Docker）、CPEコード自動生成
- **CPEマッチング**: 資産情報と脆弱性情報の自動マッチング、バージョン範囲判定
- **結果表示**: 影響を受ける資産と脆弱性の一覧、フィルタリング、統計ダッシュボード
- **定期実行**: GitHub Actionsで新規脆弱性取得後に自動マッチング実行

### 2.2 ユーザーロールと権限
**Phase 2では認証機能なし（Phase 1同様）**
- ゲスト（全ユーザー）: 資産管理、マッチング実行、結果閲覧

### 2.3 認証・認可要件
- 認証方式: なし（公開ページ）
- セキュリティレベル: 公開情報（社内ネットワークでの使用を想定）
- 管理機能: 不要

---

## 3. ページ詳細仕様

### 3.1 P-002: 資産管理ページ

#### 目的
自社の資産（ソフトウェア、ライブラリ、コンテナ）を登録・管理し、CPEコードを自動生成・表示する。

#### 主要機能
- 資産一覧表示（資産名、CPEコード、バージョン、取得元、登録日）
- 資産登録フォーム（手動入力: 資産名、ベンダー、製品名、バージョン）
- ファイルアップロード（Composer/NPM/Docker、複数ファイル対応）
- 資産編集・削除
- ページネーション（50件/ページ）

#### 必要な操作
| 操作種別 | 操作内容 | 必要な入力 | 期待される出力 |
|---------|---------|-----------|---------------|
| 取得 | 資産一覧を取得 | ページ番号、フィルタ条件（任意） | 資産情報のリスト（50件） |
| 作成 | 資産を手動登録 | 資産名、ベンダー、製品名、バージョン | CPEコード自動生成、DB保存 |
| 作成 | ファイルアップロード | composer.json/package.json/Dockerfile | CPEコード一括生成、DB保存 |
| 更新 | 資産情報を更新 | 資産ID、更新内容 | CPEコード再生成、DB更新 |
| 削除 | 資産を削除 | 資産ID | DB削除、関連マッチング結果も削除 |

#### 処理フロー

**手動登録フロー**:
1. ユーザーがフォームに資産名・ベンダー・製品名・バージョンを入力
2. バックエンドがCPE 2.3形式でCPEコードを生成（例: `cpe:2.3:a:vendor:product:version:*:*:*:*:*:*:*`）
3. PostgreSQLに保存（assetsテーブル）
4. 成功メッセージを表示、一覧に追加

**ファイルアップロードフロー（Composer）**:
1. ユーザーがcomposer.jsonまたはcomposer.lockをアップロード
2. バックエンドがJSONパース、dependenciesとdev-dependenciesを抽出
3. 各パッケージ（例: `symfony/console: ^5.4`）をCPEコードに変換
   - ベンダー: symfonyまたは自動推定
   - 製品名: console
   - バージョン: 5.4（メジャー・マイナーのみ）
4. 一括保存（UPSERT処理、重複はスキップ）
5. 成功メッセージと登録件数を表示

**ファイルアップロードフロー（NPM）**:
1. ユーザーがpackage.jsonまたはpackage-lock.jsonをアップロード
2. バックエンドがJSONパース、dependenciesとdevDependenciesを抽出
3. 各パッケージ（例: `react: ^18.2.0`）をCPEコードに変換
   - ベンダー: npmjs（公式）またはfacebook（Reactの場合）
   - 製品名: react
   - バージョン: 18.2（メジャー・マイナーのみ）
4. 一括保存（UPSERT処理、重複はスキップ）
5. 成功メッセージと登録件数を表示

**ファイルアップロードフロー（Docker）**:
1. ユーザーがDockerfileをアップロード
2. バックエンドがFROM行、RUN apt/yum/apk install行を解析
3. 各パッケージ（例: `nginx:1.25.3-alpine`）をCPEコードに変換
   - ベンダー: nginx（公式Dockerイメージ）、debian（apt）、redhat（yum）、alpine（apk）
   - 製品名: nginx
   - バージョン: 1.25.3
4. 一括保存（UPSERT処理、重複はスキップ）
5. 成功メッセージと登録件数を表示

#### データ構造（概念）
```yaml
Asset:
  識別子: 資産ID（UUID自動生成）
  基本情報:
    - 資産名（必須、例: "本番APIサーバー - Nginx"）
    - ベンダー（必須、例: "nginx"）
    - 製品名（必須、例: "nginx"）
    - バージョン（必須、例: "1.25.3"）
    - CPEコード（自動生成、例: "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"）
  メタ情報:
    - 取得元（手動/Composer/NPM/Docker）
    - 登録日時
    - 更新日時
```

---

### 3.2 P-003: マッチング結果ページ

#### 目的
資産情報と脆弱性情報のマッチング結果を表示し、影響を受ける資産と重要度を即座に把握可能にする。

#### 主要機能
- マッチング結果一覧表示（資産名、CVE ID、タイトル、重要度、マッチング理由、マッチング日時）
- フィルタリング（重要度: Critical/High/Medium/Low、資産タイプ: Composer/NPM/Docker）
- ダッシュボード（統計情報: 影響資産数、Critical/High脆弱性数、最新マッチング日時）
- 詳細表示（マッチングした資産の脆弱性一覧、脆弱性の資産一覧）
- ページネーション（50件/ページ）

#### 必要な操作
| 操作種別 | 操作内容 | 必要な入力 | 期待される出力 |
|---------|---------|-----------|---------------|
| 取得 | マッチング結果一覧を取得 | ページ番号、フィルタ条件（任意） | マッチング結果のリスト（50件） |
| 取得 | 統計情報を取得 | なし | 影響資産数、Critical/High脆弱性数、最新マッチング日時 |
| 取得 | 資産別脆弱性一覧 | 資産ID | 特定資産に影響する脆弱性リスト |
| 取得 | 脆弱性別資産一覧 | CVE ID | 特定脆弱性に影響される資産リスト |

#### 処理フロー

**マッチング結果表示フロー**:
1. ユーザーがマッチング結果ページにアクセス
2. バックエンドがPostgreSQLからマッチング結果を取得（asset_vulnerability_matchesテーブル）
3. 一覧をテーブル形式で表示（デフォルト: マッチング日時降順）
4. ユーザーがフィルタ条件（重要度、資産タイプ）を変更可能

**統計ダッシュボード表示フロー**:
1. ユーザーがページ上部のダッシュボードを表示
2. バックエンドが以下を集計:
   - 影響を受ける資産数（DISTINCT asset_id）
   - Critical脆弱性数（severity = 'Critical'）
   - High脆弱性数（severity = 'High'）
   - 最新マッチング日時（MAX(matched_at)）
3. ダッシュボードに統計情報を表示

**資産別脆弱性一覧フロー**:
1. ユーザーが資産一覧から特定の資産をクリック
2. バックエンドが該当資産のマッチング結果を取得
3. モーダルまたは別ページで脆弱性一覧を表示（CVE ID、タイトル、重要度、CVSS、マッチング理由）

#### データ構造（概念）
```yaml
AssetVulnerabilityMatch:
  識別子: マッチングID（UUID自動生成）
  関連:
    - 資産ID（外部キー: assetsテーブル）
    - CVE ID（外部キー: vulnerabilitiesテーブル）
  マッチング情報:
    - マッチング理由（完全一致/バージョン範囲/ワイルドカード）
    - マッチング日時
```

---

## 4. データ設計概要

### 4.1 主要エンティティ

```yaml
Asset（資産情報）:
  概要: 自社の資産（ソフトウェア、ライブラリ、コンテナ）
  主要属性:
    - 資産ID: UUID（主キー）
    - 資産名: 文字列（例: "本番APIサーバー - Nginx"）
    - ベンダー: 文字列（例: "nginx"）
    - 製品名: 文字列（例: "nginx"）
    - バージョン: 文字列（例: "1.25.3"）
    - CPEコード: 文字列（例: "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"）
    - 取得元: ENUM（manual/composer/npm/docker）
    - 登録日時: タイムスタンプ
    - 更新日時: タイムスタンプ
  関連:
    - AssetVulnerabilityMatch（1対多）

AssetVulnerabilityMatch（マッチング結果）:
  概要: 資産と脆弱性のマッチング結果
  主要属性:
    - マッチングID: UUID（主キー）
    - 資産ID: UUID（外部キー: assetsテーブル）
    - CVE ID: 文字列（外部キー: vulnerabilitiesテーブル）
    - マッチング理由: 文字列（exact_match/version_range/wildcard_match）
    - マッチング日時: タイムスタンプ
  関連:
    - Asset（多対1）
    - Vulnerability（多対1）

Vulnerability（脆弱性情報 - 既存）:
  概要: JVN iPedia APIから取得した脆弱性情報（Phase 1で実装済み）
  主要属性:
    - CVE ID: 文字列（主キー）
    - タイトル: 文字列
    - 重要度: 文字列（Critical/High/Medium/Low）
    - CVSS基本値: 浮動小数点
    - 公開日: タイムスタンプ
    - 更新日: タイムスタンプ
    - affected_products: JSON（CPE情報を含む）
  関連:
    - AssetVulnerabilityMatch（1対多）
```

### 4.2 エンティティ関係図
```
Asset (資産情報)
  ├─ asset_id (PK)
  ├─ asset_name
  ├─ vendor
  ├─ product
  ├─ version
  ├─ cpe_code
  ├─ source (manual/composer/npm/docker)
  ├─ created_at
  └─ updated_at
      │
      │ 1:N
      ↓
AssetVulnerabilityMatch (マッチング結果)
  ├─ match_id (PK)
  ├─ asset_id (FK: Asset)
  ├─ cve_id (FK: Vulnerability)
  ├─ match_reason (exact_match/version_range/wildcard_match)
  └─ matched_at
      │
      │ N:1
      ↓
Vulnerability (脆弱性情報 - 既存)
  ├─ cve_id (PK)
  ├─ title
  ├─ severity
  ├─ cvss_score
  ├─ published_date
  ├─ modified_date
  └─ affected_products (JSON - CPE情報含む)
```

### 4.3 テーブル定義（詳細）

#### assetsテーブル
| カラム名 | データ型 | NULL | キー | デフォルト | 説明 |
|---------|---------|------|-----|----------|------|
| asset_id | UUID | NOT NULL | PK | gen_random_uuid() | 資産ID |
| asset_name | VARCHAR(200) | NOT NULL | | | 資産名（例: "本番APIサーバー - Nginx"） |
| vendor | VARCHAR(100) | NOT NULL | INDEX | | ベンダー名（例: "nginx"） |
| product | VARCHAR(100) | NOT NULL | INDEX | | 製品名（例: "nginx"） |
| version | VARCHAR(50) | NOT NULL | | | バージョン（例: "1.25.3"） |
| cpe_code | VARCHAR(200) | NOT NULL | INDEX | | CPEコード（例: "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"） |
| source | VARCHAR(20) | NOT NULL | | | 取得元（manual/composer/npm/docker） |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL | | now() | 登録日時 |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL | | now() | 更新日時 |

**制約**:
- UNIQUE(vendor, product, version): 同一製品・バージョンの重複登録を防止

#### asset_vulnerability_matchesテーブル
| カラム名 | データ型 | NULL | キー | デフォルト | 説明 |
|---------|---------|------|-----|----------|------|
| match_id | UUID | NOT NULL | PK | gen_random_uuid() | マッチングID |
| asset_id | UUID | NOT NULL | FK, INDEX | | 資産ID |
| cve_id | VARCHAR(20) | NOT NULL | FK, INDEX | | CVE ID |
| match_reason | VARCHAR(50) | NOT NULL | | | マッチング理由 |
| matched_at | TIMESTAMP WITH TIME ZONE | NOT NULL | INDEX | now() | マッチング日時 |

**制約**:
- UNIQUE(asset_id, cve_id): 同一資産・脆弱性の重複マッチング防止
- FOREIGN KEY(asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
- FOREIGN KEY(cve_id) REFERENCES vulnerabilities(cve_id) ON DELETE CASCADE

### 4.4 バリデーションルール
```yaml
CPEコード:
  - ルール: CPE 2.3形式（cpe:2.3:part:vendor:product:version:update:edition:language:sw_edition:target_sw:target_hw:other）
  - 理由: CPE標準仕様の遵守、マッチング精度保証

ベンダー・製品名:
  - ルール: 小文字英数字、ハイフン、アンダースコアのみ（正規化）
  - 理由: マッチング精度向上、CPEコード生成の一貫性

バージョン:
  - ルール: セマンティックバージョニング（MAJOR.MINOR.PATCH）または単純な数字（1.25.3, 18.2.0, 5.4）
  - 理由: バージョン範囲比較の精度保証

資産名:
  - ルール: 1文字以上200文字以下
  - 理由: 可読性とDB容量のバランス
```

---

## 5. CPEコード生成仕様

### 5.1 CPE 2.3形式の構造
```
cpe:2.3:part:vendor:product:version:update:edition:language:sw_edition:target_sw:target_hw:other

例: cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*

part: a (application), o (operating system), h (hardware)
vendor: ベンダー名（小文字）
product: 製品名（小文字）
version: バージョン（セマンティックバージョニング）
update: パッチ番号（通常は*）
edition: エディション（通常は*）
language: 言語（通常は*）
sw_edition: ソフトウェアエディション（通常は*）
target_sw: ターゲットソフトウェア（通常は*）
target_hw: ターゲットハードウェア（通常は*）
other: その他（通常は*）
```

**Phase 2では最初の7要素のみを使用**:
- `cpe:2.3:a:vendor:product:version:*:*:*` （以降の3要素は省略可能）

### 5.2 資産側のCPEコード生成ルール

#### 手動登録時
```python
# 入力: ベンダー="Nginx", 製品名="Nginx", バージョン="1.25.3"
# 出力: cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*

def generate_cpe_from_manual(vendor: str, product: str, version: str) -> str:
    """
    手動入力からCPEコードを生成する。

    Args:
        vendor: ベンダー名（例: "Nginx"）
        product: 製品名（例: "Nginx"）
        version: バージョン（例: "1.25.3"）

    Returns:
        CPE 2.3形式のコード（例: "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"）
    """
    vendor_normalized = vendor.lower().replace(" ", "_")
    product_normalized = product.lower().replace(" ", "_")
    version_normalized = version.strip()

    return f"cpe:2.3:a:{vendor_normalized}:{product_normalized}:{version_normalized}:*:*:*:*:*:*:*"
```

#### Composer（PHP）からの抽出
```json
// composer.json
{
  "require": {
    "symfony/console": "^5.4",
    "guzzlehttp/guzzle": "^7.5"
  }
}
```

```python
def generate_cpe_from_composer(package_name: str, version: str) -> str:
    """
    composer.jsonからCPEコードを生成する。

    Args:
        package_name: パッケージ名（例: "symfony/console"）
        version: バージョン（例: "^5.4" → "5.4"に正規化）

    Returns:
        CPE 2.3形式のコード（例: "cpe:2.3:a:symfony:console:5.4:*:*:*:*:*:*:*"）
    """
    # パッケージ名をベンダー/製品名に分割
    vendor, product = package_name.split("/", 1)

    # バージョン正規化（^5.4 → 5.4、~7.5 → 7.5）
    version_normalized = version.lstrip("^~>=<")

    return f"cpe:2.3:a:{vendor}:{product}:{version_normalized}:*:*:*:*:*:*:*"
```

#### NPM（JavaScript）からの抽出
```json
// package.json
{
  "dependencies": {
    "react": "^18.2.0",
    "express": "^4.18.2"
  }
}
```

```python
# NPMパッケージのベンダーマッピング（主要パッケージのみ）
NPM_VENDOR_MAP = {
    "react": "facebook",
    "vue": "vuejs",
    "angular": "angular",
    "express": "expressjs",
    # その他は "npmjs" を使用
}

def generate_cpe_from_npm(package_name: str, version: str) -> str:
    """
    package.jsonからCPEコードを生成する。

    Args:
        package_name: パッケージ名（例: "react"）
        version: バージョン（例: "^18.2.0" → "18.2.0"に正規化）

    Returns:
        CPE 2.3形式のコード（例: "cpe:2.3:a:facebook:react:18.2.0:*:*:*:*:*:*:*"）
    """
    vendor = NPM_VENDOR_MAP.get(package_name, "npmjs")
    version_normalized = version.lstrip("^~>=<")

    return f"cpe:2.3:a:{vendor}:{package_name}:{version_normalized}:*:*:*:*:*:*:*"
```

#### Docker（Dockerfile）からの抽出
```dockerfile
# Dockerfile
FROM nginx:1.25.3-alpine
RUN apt-get update && apt-get install -y curl
```

```python
# Dockerイメージのベンダーマッピング
DOCKER_VENDOR_MAP = {
    "nginx": "nginx",
    "postgres": "postgresql",
    "redis": "redis",
    "mysql": "mysql",
    # その他は "docker" を使用
}

def generate_cpe_from_docker(image_name: str, image_tag: str) -> str:
    """
    Dockerfileからベースイメージ・パッケージのCPEコードを生成する。

    Args:
        image_name: イメージ名（例: "nginx"）
        image_tag: イメージタグ（例: "1.25.3-alpine" → "1.25.3"に正規化）

    Returns:
        CPE 2.3形式のコード（例: "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"）
    """
    vendor = DOCKER_VENDOR_MAP.get(image_name, "docker")

    # バージョン正規化（1.25.3-alpine → 1.25.3）
    version = image_tag.split("-")[0] if "-" in image_tag else image_tag

    return f"cpe:2.3:a:{vendor}:{image_name}:{version}:*:*:*:*:*:*:*"
```

### 5.3 脆弱性側のCPE情報抽出

JVN iPedia APIの`affected_products`フィールド（JSON）から抽出する。

**既存のVulnerabilityモデル（affected_products）の構造例**:
```json
{
  "cpe": [
    "cpe:2.3:a:nginx:nginx:1.25.2:*:*:*:*:*:*:*",
    "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"
  ],
  "version_ranges": {
    "nginx": {
      "versionStartIncluding": "1.25.0",
      "versionEndExcluding": "1.25.4"
    }
  }
}
```

**抽出ロジック**:
```python
def extract_cpe_from_vulnerability(vulnerability: Vulnerability) -> List[str]:
    """
    脆弱性情報からCPEコードのリストを抽出する。

    Args:
        vulnerability: Vulnerabilityモデルインスタンス

    Returns:
        CPEコードのリスト（例: ["cpe:2.3:a:nginx:nginx:1.25.2:*:*:*:*:*:*:*", ...]）
    """
    affected_products = vulnerability.affected_products or {}

    # CPEリストを取得（存在しない場合は空リスト）
    cpe_list = affected_products.get("cpe", [])

    return cpe_list
```

---

## 6. マッチングアルゴリズム仕様

### 6.1 マッチングの基本方針
1. **完全一致マッチング**（優先度: 高）
2. **バージョン範囲マッチング**（優先度: 中）
3. **ワイルドカードマッチング**（優先度: 低）

### 6.2 完全一致マッチング

**条件**: 資産のCPEコードと脆弱性のCPEコードが完全に一致（最初の7要素を比較）

```python
def match_exact(asset_cpe: str, vulnerability_cpe: str) -> bool:
    """
    CPEコードの完全一致判定。

    Args:
        asset_cpe: 資産のCPEコード（例: "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"）
        vulnerability_cpe: 脆弱性のCPEコード（例: "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"）

    Returns:
        True（一致）またはFalse（不一致）
    """
    # 最初の7要素を抽出（cpe:2.3:part:vendor:product:version:update:edition:language）
    asset_parts = asset_cpe.split(":")[:8]  # cpe, 2.3, a, vendor, product, version, update, edition
    vuln_parts = vulnerability_cpe.split(":")[:8]

    return asset_parts == vuln_parts
```

**例**:
- 資産: `cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*`
- 脆弱性: `cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*`
- **結果**: マッチング成功（完全一致）

### 6.3 バージョン範囲マッチング

**条件**: ベンダー・製品名が一致し、資産のバージョンが脆弱性のバージョン範囲内に含まれる

**脆弱性側のバージョン範囲情報（affected_products.version_ranges）**:
```json
{
  "nginx": {
    "versionStartIncluding": "1.25.0",
    "versionEndExcluding": "1.25.4"
  }
}
```

**バージョン比較ロジック**:
```python
from packaging import version

def match_version_range(
    asset_vendor: str,
    asset_product: str,
    asset_version: str,
    vulnerability_ranges: dict
) -> bool:
    """
    バージョン範囲マッチング判定。

    Args:
        asset_vendor: 資産のベンダー名（例: "nginx"）
        asset_product: 資産の製品名（例: "nginx"）
        asset_version: 資産のバージョン（例: "1.25.3"）
        vulnerability_ranges: 脆弱性のバージョン範囲（例: {"nginx": {"versionStartIncluding": "1.25.0", ...}}）

    Returns:
        True（範囲内）またはFalse（範囲外）
    """
    # 製品名でバージョン範囲を検索（ベンダー/製品名の両方をチェック）
    product_ranges = vulnerability_ranges.get(asset_product) or vulnerability_ranges.get(f"{asset_vendor}:{asset_product}")

    if not product_ranges:
        return False

    asset_ver = version.parse(asset_version)

    # versionStartIncluding（以上）
    if "versionStartIncluding" in product_ranges:
        start_ver = version.parse(product_ranges["versionStartIncluding"])
        if asset_ver < start_ver:
            return False

    # versionStartExcluding（より大きい）
    if "versionStartExcluding" in product_ranges:
        start_ver = version.parse(product_ranges["versionStartExcluding"])
        if asset_ver <= start_ver:
            return False

    # versionEndIncluding（以下）
    if "versionEndIncluding" in product_ranges:
        end_ver = version.parse(product_ranges["versionEndIncluding"])
        if asset_ver > end_ver:
            return False

    # versionEndExcluding（より小さい）
    if "versionEndExcluding" in product_ranges:
        end_ver = version.parse(product_ranges["versionEndExcluding"])
        if asset_ver >= end_ver:
            return False

    return True
```

**例**:
- 資産: `nginx:nginx:1.25.3`
- 脆弱性範囲: `versionStartIncluding=1.25.0, versionEndExcluding=1.25.4`
- **結果**: マッチング成功（1.25.0 <= 1.25.3 < 1.25.4）

### 6.4 ワイルドカードマッチング

**条件**: CPEコードの`*`（任意）や`-`（未定義）を考慮したマッチング

**Phase 2では最小限の実装**:
- ワイルドカード（`*`）は「任意の値」として扱う
- ベンダー・製品名が一致し、バージョン以外が`*`の場合は部分一致とみなす

```python
def match_wildcard(asset_cpe: str, vulnerability_cpe: str) -> bool:
    """
    ワイルドカードマッチング判定。

    Args:
        asset_cpe: 資産のCPEコード
        vulnerability_cpe: 脆弱性のCPEコード

    Returns:
        True（一致）またはFalse（不一致）
    """
    asset_parts = asset_cpe.split(":")
    vuln_parts = vulnerability_cpe.split(":")

    # part, vendor, productが一致し、それ以外が*の場合はマッチング
    if (asset_parts[2] == vuln_parts[2] and  # part
        asset_parts[3] == vuln_parts[3] and  # vendor
        asset_parts[4] == vuln_parts[4]):    # product

        # バージョン以降が全て*の場合はマッチング
        if all(p == "*" for p in vuln_parts[5:8]):
            return True

    return False
```

**例**:
- 資産: `cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*`
- 脆弱性: `cpe:2.3:a:nginx:nginx:*:*:*:*:*:*:*:*`
- **結果**: マッチング成功（ワイルドカード一致）

### 6.5 マッチング実行フロー

```python
def execute_matching(asset: Asset, vulnerability: Vulnerability) -> Optional[str]:
    """
    1つの資産と1つの脆弱性のマッチング判定。

    Args:
        asset: Assetモデルインスタンス
        vulnerability: Vulnerabilityモデルインスタンス

    Returns:
        マッチング理由（"exact_match" / "version_range" / "wildcard_match"）またはNone（不一致）
    """
    # 1. 完全一致マッチング
    vuln_cpe_list = extract_cpe_from_vulnerability(vulnerability)
    for vuln_cpe in vuln_cpe_list:
        if match_exact(asset.cpe_code, vuln_cpe):
            return "exact_match"

    # 2. バージョン範囲マッチング
    version_ranges = vulnerability.affected_products.get("version_ranges", {})
    if version_ranges:
        asset_parts = asset.cpe_code.split(":")
        asset_vendor = asset_parts[3]
        asset_product = asset_parts[4]
        asset_version = asset_parts[5]

        if match_version_range(asset_vendor, asset_product, asset_version, version_ranges):
            return "version_range"

    # 3. ワイルドカードマッチング
    for vuln_cpe in vuln_cpe_list:
        if match_wildcard(asset.cpe_code, vuln_cpe):
            return "wildcard_match"

    return None  # マッチング失敗
```

**全資産・全脆弱性のマッチング実行**:
```python
def execute_full_matching():
    """
    全資産と全脆弱性のマッチング実行（バッチ処理）。

    Returns:
        マッチング結果の統計（総マッチング数、完全一致数、バージョン範囲数、ワイルドカード数）
    """
    assets = db.query(Asset).all()
    vulnerabilities = db.query(Vulnerability).all()

    matches = []
    for asset in assets:
        for vulnerability in vulnerabilities:
            match_reason = execute_matching(asset, vulnerability)
            if match_reason:
                matches.append({
                    "asset_id": asset.asset_id,
                    "cve_id": vulnerability.cve_id,
                    "match_reason": match_reason,
                    "matched_at": datetime.now()
                })

    # UPSERT処理（既存のマッチング結果は更新、新規は挿入）
    for match in matches:
        db.execute(
            """
            INSERT INTO asset_vulnerability_matches (asset_id, cve_id, match_reason, matched_at)
            VALUES (:asset_id, :cve_id, :match_reason, :matched_at)
            ON CONFLICT (asset_id, cve_id)
            DO UPDATE SET match_reason = EXCLUDED.match_reason, matched_at = EXCLUDED.matched_at
            """,
            match
        )

    db.commit()

    return {
        "total_matches": len(matches),
        "exact_matches": sum(1 for m in matches if m["match_reason"] == "exact_match"),
        "version_range_matches": sum(1 for m in matches if m["match_reason"] == "version_range"),
        "wildcard_matches": sum(1 for m in matches if m["match_reason"] == "wildcard_match"),
    }
```

---

## 7. API仕様

### 7.1 資産管理API

#### POST /api/assets - 資産登録（手動）
```yaml
エンドポイント: POST /api/assets
リクエストボディ:
  {
    "asset_name": "本番APIサーバー - Nginx",
    "vendor": "nginx",
    "product": "nginx",
    "version": "1.25.3"
  }
レスポンス:
  成功（201 Created）:
    {
      "asset_id": "550e8400-e29b-41d4-a716-446655440000",
      "asset_name": "本番APIサーバー - Nginx",
      "vendor": "nginx",
      "product": "nginx",
      "version": "1.25.3",
      "cpe_code": "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*",
      "source": "manual",
      "created_at": "2026-01-26T12:00:00Z"
    }
  失敗（400 Bad Request）:
    {
      "error": "Invalid version format"
    }
```

#### GET /api/assets - 資産一覧取得
```yaml
エンドポイント: GET /api/assets?page=1&limit=50&source=composer
クエリパラメータ:
  - page: ページ番号（デフォルト: 1）
  - limit: 1ページあたりの件数（デフォルト: 50）
  - source: 取得元フィルタ（manual/composer/npm/docker、任意）
レスポンス:
  成功（200 OK）:
    {
      "items": [
        {
          "asset_id": "550e8400-e29b-41d4-a716-446655440000",
          "asset_name": "Symfony Console",
          "vendor": "symfony",
          "product": "console",
          "version": "5.4",
          "cpe_code": "cpe:2.3:a:symfony:console:5.4:*:*:*:*:*:*:*",
          "source": "composer",
          "created_at": "2026-01-26T12:00:00Z"
        }
      ],
      "total": 150,
      "page": 1,
      "limit": 50
    }
```

#### PUT /api/assets/{asset_id} - 資産更新
```yaml
エンドポイント: PUT /api/assets/{asset_id}
リクエストボディ:
  {
    "asset_name": "本番APIサーバー - Nginx（更新）",
    "version": "1.25.4"
  }
レスポンス:
  成功（200 OK）:
    {
      "asset_id": "550e8400-e29b-41d4-a716-446655440000",
      "asset_name": "本番APIサーバー - Nginx（更新）",
      "vendor": "nginx",
      "product": "nginx",
      "version": "1.25.4",
      "cpe_code": "cpe:2.3:a:nginx:nginx:1.25.4:*:*:*:*:*:*:*",
      "source": "manual",
      "updated_at": "2026-01-26T13:00:00Z"
    }
```

#### DELETE /api/assets/{asset_id} - 資産削除
```yaml
エンドポイント: DELETE /api/assets/{asset_id}
レスポンス:
  成功（204 No Content）: （レスポンスボディなし）
  失敗（404 Not Found）:
    {
      "error": "Asset not found"
    }
```

### 7.2 ファイルインポートAPI

#### POST /api/assets/import/composer - Composerファイルアップロード
```yaml
エンドポイント: POST /api/assets/import/composer
リクエスト: multipart/form-data
  - file: composer.json または composer.lock
レスポンス:
  成功（201 Created）:
    {
      "imported_count": 25,
      "skipped_count": 3,
      "errors": []
    }
  失敗（400 Bad Request）:
    {
      "error": "Invalid composer.json format",
      "details": "JSON parse error at line 5"
    }
```

#### POST /api/assets/import/npm - NPMファイルアップロード
```yaml
エンドポイント: POST /api/assets/import/npm
リクエスト: multipart/form-data
  - file: package.json または package-lock.json
レスポンス:
  成功（201 Created）:
    {
      "imported_count": 42,
      "skipped_count": 5,
      "errors": []
    }
```

#### POST /api/assets/import/docker - Dockerfileアップロード
```yaml
エンドポイント: POST /api/assets/import/docker
リクエスト: multipart/form-data
  - file: Dockerfile
レスポンス:
  成功（201 Created）:
    {
      "imported_count": 8,
      "skipped_count": 1,
      "errors": []
    }
```

### 7.3 マッチング実行API

#### POST /api/matching/execute - マッチング実行
```yaml
エンドポイント: POST /api/matching/execute
リクエストボディ: （なし、全資産・全脆弱性を対象）
レスポンス:
  成功（200 OK）:
    {
      "total_assets": 150,
      "total_vulnerabilities": 963,
      "total_matches": 42,
      "exact_matches": 15,
      "version_range_matches": 20,
      "wildcard_matches": 7,
      "execution_time_seconds": 12.5
    }
  失敗（500 Internal Server Error）:
    {
      "error": "Matching execution failed",
      "details": "Database connection timeout"
    }
```

#### GET /api/matching/results - マッチング結果取得
```yaml
エンドポイント: GET /api/matching/results?page=1&limit=50&severity=Critical
クエリパラメータ:
  - page: ページ番号（デフォルト: 1）
  - limit: 1ページあたりの件数（デフォルト: 50）
  - severity: 重要度フィルタ（Critical/High/Medium/Low、任意）
  - source: 資産タイプフィルタ（manual/composer/npm/docker、任意）
レスポンス:
  成功（200 OK）:
    {
      "items": [
        {
          "match_id": "650e8400-e29b-41d4-a716-446655440000",
          "asset_id": "550e8400-e29b-41d4-a716-446655440000",
          "asset_name": "本番APIサーバー - Nginx",
          "cve_id": "CVE-2024-0001",
          "vulnerability_title": "Nginx HTTP/2 Buffer Overflow",
          "severity": "Critical",
          "cvss_score": 9.8,
          "match_reason": "exact_match",
          "matched_at": "2026-01-26T12:00:00Z"
        }
      ],
      "total": 42,
      "page": 1,
      "limit": 50
    }
```

#### GET /api/assets/{asset_id}/vulnerabilities - 資産別脆弱性一覧
```yaml
エンドポイント: GET /api/assets/{asset_id}/vulnerabilities
レスポンス:
  成功（200 OK）:
    {
      "asset_id": "550e8400-e29b-41d4-a716-446655440000",
      "asset_name": "本番APIサーバー - Nginx",
      "vulnerabilities": [
        {
          "cve_id": "CVE-2024-0001",
          "title": "Nginx HTTP/2 Buffer Overflow",
          "severity": "Critical",
          "cvss_score": 9.8,
          "match_reason": "exact_match",
          "matched_at": "2026-01-26T12:00:00Z"
        }
      ],
      "total_vulnerabilities": 3
    }
```

#### GET /api/matching/dashboard - 統計情報取得
```yaml
エンドポイント: GET /api/matching/dashboard
レスポンス:
  成功（200 OK）:
    {
      "affected_assets_count": 35,
      "total_matches": 42,
      "critical_vulnerabilities": 8,
      "high_vulnerabilities": 15,
      "medium_vulnerabilities": 12,
      "low_vulnerabilities": 7,
      "last_matching_at": "2026-01-26T12:00:00Z"
    }
```

---

## 8. UI仕様

### 8.1 P-002: 資産管理ページ

#### レイアウト
```
┌────────────────────────────────────────────────────────────┐
│ 資産管理                                          [ログアウト] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ [新規登録] [Composerアップロード] [NPMアップロード] [Dockerアップロード] │
│                                                            │
│ ┌──────────────────────────────────────────────────┐      │
│ │ 資産一覧（150件）                                 │      │
│ ├──────────────────────────────────────────────────┤      │
│ │ 資産名 │ ベンダー │ 製品名 │ バージョン │ CPEコード │ 取得元 │ 登録日 │ 操作 │      │
│ ├──────────────────────────────────────────────────┤      │
│ │ 本番APIサーバー - Nginx │ nginx │ nginx │ 1.25.3 │ cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:* │ manual │ 2026-01-26 │ [編集] [削除] │      │
│ │ Symfony Console │ symfony │ console │ 5.4 │ cpe:2.3:a:symfony:console:5.4:*:*:*:*:*:*:* │ composer │ 2026-01-26 │ [編集] [削除] │      │
│ └──────────────────────────────────────────────────┘      │
│                                                            │
│ [← 前へ] [1] [2] [3] ... [10] [次へ →]                    │
└────────────────────────────────────────────────────────────┘
```

#### 新規登録モーダル
```
┌────────────────────────────────────────┐
│ 資産の新規登録                    [×]   │
├────────────────────────────────────────┤
│                                        │
│ 資産名: [                            ] │
│ ベンダー: [                          ] │
│ 製品名: [                            ] │
│ バージョン: [                        ] │
│                                        │
│          [キャンセル]  [登録]         │
└────────────────────────────────────────┘
```

#### ファイルアップロードモーダル（Composer）
```
┌────────────────────────────────────────┐
│ Composerファイルのアップロード    [×]  │
├────────────────────────────────────────┤
│                                        │
│ ファイル: [ファイルを選択]  composer.json または composer.lock │
│                                        │
│ [ドラッグ&ドロップでアップロード]      │
│                                        │
│          [キャンセル]  [アップロード]  │
└────────────────────────────────────────┘
```

### 8.2 P-003: マッチング結果ページ

#### レイアウト
```
┌────────────────────────────────────────────────────────────┐
│ マッチング結果                                    [マッチング実行] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ ┌────────────────────────────────────────────────────┐   │
│ │ 統計ダッシュボード                                  │   │
│ ├────────────────────────────────────────────────────┤   │
│ │ 影響資産数: 35件 │ Critical: 8件 │ High: 15件 │ Medium: 12件 │ Low: 7件 │   │
│ │ 最終マッチング: 2026-01-26 12:00                   │   │
│ └────────────────────────────────────────────────────┘   │
│                                                            │
│ フィルタ: [重要度: 全て ▼] [資産タイプ: 全て ▼]          │
│                                                            │
│ ┌──────────────────────────────────────────────────┐      │
│ │ マッチング結果（42件）                            │      │
│ ├──────────────────────────────────────────────────┤      │
│ │ 資産名 │ CVE ID │ タイトル │ 重要度 │ CVSS │ マッチング理由 │ マッチング日時 │      │
│ ├──────────────────────────────────────────────────┤      │
│ │ 本番APIサーバー - Nginx │ CVE-2024-0001 │ Nginx HTTP/2 Buffer Overflow │ Critical │ 9.8 │ exact_match │ 2026-01-26 12:00 │      │
│ └──────────────────────────────────────────────────┘      │
│                                                            │
│ [← 前へ] [1] [2] [次へ →]                                │
└────────────────────────────────────────────────────────────┘
```

---

## 9. 非機能要件

### 9.1 パフォーマンス
- **マッチング処理時間**: 1,000資産 × 1,000脆弱性を5分以内
  - 実装方法: バッチ処理、インデックス最適化（vendor, product, versionにINDEX）
- **ファイルアップロード**: 10MBまでのファイルを10秒以内に処理
- **API応答時間**: 95パーセンタイルで2秒以内

### 9.2 データ整合性
- **マッチング結果の冪等性**: 同一データで3回実行してデータ不整合ゼロ
  - 実装方法: UPSERT処理（ON CONFLICT DO UPDATE）、UNIQUE制約
- **外部キー制約**: 資産削除時にマッチング結果も自動削除（CASCADE）

### 9.3 拡張性
- **NVD API統合**: Phase 3で実装予定（affected_productsのJSON構造を拡張）
- **CISA KEV統合**: Phase 3で実装予定（悪用実績フラグを追加）
- **認証機能**: Phase 4で実装予定（ユーザー管理、権限設定）

### 9.4 運用性
- **定期的なマッチング実行**: GitHub Actionsで新規脆弱性取得後に自動実行
  - 実装方法: daily_fetch.ymlにマッチングステップを追加
- **マッチング履歴の保存**: matched_atカラムで履歴管理

---

## 10. 制約事項

### 10.1 技術的制約
- **CPEコード生成精度**: 90%以上（Composer/NPM/Dockerファイルから）
  - 制約: パッケージ名とCPEベンダー名のマッピングは主要パッケージのみ
  - 対応: 未知のパッケージは`npmjs`、`docker`などのデフォルトベンダーを使用
- **バージョン範囲マッチング**: セマンティックバージョニング（MAJOR.MINOR.PATCH）のみ対応
  - 制約: 日付ベースのバージョン（20231225）は非対応
  - 対応: Phase 3で拡張予定
- **マッチング処理時間**: 1,000資産 × 1,000脆弱性を5分以内
  - 制約: PostgreSQLのクエリパフォーマンスに依存
  - 対応: インデックス最適化、バッチ処理の最適化

### 10.2 データ制約
- **脆弱性側のCPE情報**: JVN iPedia APIから取得した`affected_products`に依存
  - 制約: CPE情報が存在しない脆弱性はマッチング不可
  - 対応: Phase 3でNVD API統合時にCPE情報を補完

---

## 11. セキュリティ要件

### 11.1 基本方針
本プロジェクトは **CVSS 3.1（Common Vulnerability Scoring System）** に準拠したセキュリティ要件を満たすこと。

CVSS 3.1の評価観点:
- **機密性（Confidentiality）**: 資産情報の不正アクセス防止
- **完全性（Integrity）**: データ改ざん防止、入力検証
- **可用性（Availability）**: DoS対策、マッチング処理の安定性

### 11.2 プロジェクト固有の必須要件

**認証機能がない場合（Phase 2）**:
- ✅ HTTPSの強制（本番環境）
- ✅ セキュリティヘッダー設定（本番環境）
- ✅ 入力値のサニタイゼーション（ファイルアップロード時のJSONパース）
- ✅ エラーメッセージでの情報漏洩防止

**ファイルアップロード時のセキュリティ**:
- ✅ ファイルサイズ制限（10MB）
- ✅ MIMEタイプ検証（application/json, text/plain）
- ✅ ファイル名のサニタイゼーション（パストラバーサル攻撃防止）
- ✅ アップロード先ディレクトリの権限制限

---

## 12. 複合API処理（バックエンド内部処理）

### 複合処理-003: CPEマッチング実行
**トリガー**: ユーザーがマッチング実行ボタンをクリック、またはGitHub Actions定期実行
**フロントエンドAPI**: POST /api/matching/execute
**バックエンド内部処理**:
1. 全資産をassetsテーブルから取得
2. 全脆弱性をvulnerabilitiesテーブルから取得
3. 各資産・脆弱性ペアでマッチング判定（完全一致 → バージョン範囲 → ワイルドカード）
4. マッチング結果をasset_vulnerability_matchesテーブルにUPSERT
5. マッチング統計を計算（総マッチング数、完全一致数、バージョン範囲数、ワイルドカード数）
6. 処理結果をJSON形式で応答
**結果**: マッチング統計、実行時間
**外部サービス依存**: なし

### 複合処理-004: Composerファイルインポート
**トリガー**: ユーザーがComposerファイルをアップロード
**フロントエンドAPI**: POST /api/assets/import/composer
**バックエンド内部処理**:
1. ファイルアップロード検証（サイズ、MIMEタイプ、ファイル名）
2. JSONパース（composer.jsonまたはcomposer.lock）
3. dependenciesとdev-dependenciesを抽出
4. 各パッケージをCPEコードに変換（ベンダー/製品名/バージョン正規化）
5. assetsテーブルに一括UPSERT（重複はスキップ）
6. インポート結果を応答（登録件数、スキップ件数、エラー）
**結果**: インポート統計
**外部サービス依存**: なし

---

## 13. 実装フェーズ計画

### Phase 2-1: データモデル実装（推定工数: 4時間）
- [ ] Assetモデル作成（src/models/asset.py）
- [ ] AssetVulnerabilityMatchモデル作成（src/models/asset_vulnerability_match.py）
- [ ] テーブル作成スクリプト（Alembicマイグレーション、またはinit_db()拡張）
- [ ] インデックス作成（vendor, product, versionにINDEX）

### Phase 2-2: CPEコード生成機能（推定工数: 12時間）
- [ ] CPEコード生成ユーティリティ（src/utils/cpe_generator.py）
  - [ ] generate_cpe_from_manual()
  - [ ] generate_cpe_from_composer()
  - [ ] generate_cpe_from_npm()
  - [ ] generate_cpe_from_docker()
- [ ] ベンダーマッピング（NPM_VENDOR_MAP, DOCKER_VENDOR_MAP）
- [ ] バージョン正規化ロジック（^5.4 → 5.4、1.25.3-alpine → 1.25.3）

### Phase 2-3: マッチングアルゴリズム実装（推定工数: 16時間）
- [ ] マッチングサービス（src/services/matching_service.py）
  - [ ] match_exact()
  - [ ] match_version_range()
  - [ ] match_wildcard()
  - [ ] execute_matching()（1資産・1脆弱性）
  - [ ] execute_full_matching()（全資産・全脆弱性）
- [ ] バージョン比較ロジック（packaging.versionを使用）

### Phase 2-4: API実装（推定工数: 16時間）
- [ ] 資産管理API（src/api/assets.py）
  - [ ] POST /api/assets（手動登録）
  - [ ] GET /api/assets（一覧取得）
  - [ ] PUT /api/assets/{asset_id}（更新）
  - [ ] DELETE /api/assets/{asset_id}（削除）
- [ ] ファイルインポートAPI（src/api/assets.py）
  - [ ] POST /api/assets/import/composer
  - [ ] POST /api/assets/import/npm
  - [ ] POST /api/assets/import/docker
- [ ] マッチング実行API（src/api/matching.py）
  - [ ] POST /api/matching/execute
  - [ ] GET /api/matching/results
  - [ ] GET /api/assets/{asset_id}/vulnerabilities
  - [ ] GET /api/matching/dashboard

### Phase 2-5: UI実装（推定工数: 16時間）
- [ ] 資産管理ページ（src/templates/assets.html）
  - [ ] 資産一覧表示
  - [ ] 新規登録モーダル
  - [ ] ファイルアップロードモーダル（Composer/NPM/Docker）
  - [ ] 編集・削除機能
- [ ] マッチング結果ページ（src/templates/matching_results.html）
  - [ ] マッチング結果一覧
  - [ ] 統計ダッシュボード
  - [ ] フィルタリング機能
- [ ] JavaScript実装（src/static/js/assets.js, matching.js）
  - [ ] ファイルアップロード処理
  - [ ] モーダル制御
  - [ ] フィルタリング処理

### Phase 2-6: テスト・統合（推定工数: 12時間）
- [ ] 単体テスト（tests/unit/）
  - [ ] test_cpe_generator.py
  - [ ] test_matching_service.py
- [ ] 統合テスト（tests/integration/）
  - [ ] test_asset_api.py
  - [ ] test_matching_api.py
  - [ ] test_file_import.py
- [ ] E2Eテスト（tests/e2e/）
  - [ ] test_asset_management.py
  - [ ] test_matching_flow.py
- [ ] カバレッジ目標: 80%以上

**合計工数**: 76時間（約9.5日）

---

## 14. 参考資料

### 14.1 CPE仕様
- **CPE 2.3公式仕様**: https://nvd.nist.gov/products/cpe
- **CPE Dictionary**: https://nvd.nist.gov/products/cpe/search（既存のCPEコードを検索可能）

### 14.2 外部API
- **JVN iPedia API**: https://jvndb.jvn.jp/apis/myjvn/（既存実装で使用中）
- **NVD API 2.0**: https://services.nvd.nist.gov/rest/json/cves/2.0（Phase 3で統合予定）
- **CISA KEV**: https://www.cisa.gov/known-exploited-vulnerabilities-catalog（Phase 3で統合予定）

### 14.3 バージョン比較ライブラリ
- **Python packaging**: https://packaging.pypa.io/en/stable/version.html（セマンティックバージョニング対応）

---

**要件定義書 作成日**: 2026-01-26
**最終更新日**: 2026-01-26
**作成者**: BlueLamp 要件定義エージェント（Phase 2）
**対象フェーズ**: Phase 2 CPEマッチング機能実装
**前提条件**: Phase 1完了（脆弱性情報取得基盤、PostgreSQL、FastAPI + Jinja2）
