# 脆弱性管理システム - 要件定義書（Phase 1 & Phase 2）

## 要件定義の作成原則
- **「あったらいいな」は絶対に作らない**
- **拡張可能性のための余分な要素は一切追加しない**
- **将来の「もしかして」のための準備は禁止**
- **今、ここで必要な最小限の要素のみ**

---

## 1. プロジェクト概要

### 1.1 Phase 1: 脆弱性情報取得基盤
JVN iPedia APIから脆弱性情報（直近3年分、全期間対応可能）を自動取得し、PostgreSQLに永続化する堅牢なデータ基盤。GitHub Actionsで定期実行（毎日午前3時）、簡易UIで動作確認可能、Phase 2以降の拡張を阻害しない設計。

### 1.2 Phase 2: CPEマッチング機能
既存の脆弱性情報（JVN iPedia APIから取得したPostgreSQLデータ）と、自社の資産情報（ソフトウェア、ライブラリ、コンテナ）をCPE（Common Platform Enumeration）コードで自動マッチングし、「どの脆弱性が自社システムに影響するか」を即座に判定できるシステム。

### 1.3 成功指標

#### Phase 1: 脆弱性情報取得基盤
**定量的指標**:
- データ取得成功率: 99.9%以上（JVN iPedia APIに適用、リトライ3回、API完全障害のみ許容）
- 差分取得精度: 100%（新規・更新分を漏れなく取得）
- 処理時間: 1,000件を10分以内
- コードカバレッジ: 80%以上
- 冪等性: 同一処理3回実行でデータ不整合ゼロ

**定性的指標**:
- 保守性: 新規メンバーが1時間以内にコード構造を理解可能
- 拡張性: 設定変更のみで「3年分→全期間」に拡張可能
- 運用性: エラー発生時、ログから5分以内に原因特定可能
- 堅牢性: API障害時もデータ損失・DB破損なし
- 視認性: 簡易UIで取得データの正常性を即座に確認可能

#### Phase 2: CPEマッチング機能
**定量的指標**:
- マッチング精度: 95%以上（既知のテストケースで検証）
- マッチング処理時間: 1,000資産 × 1,000脆弱性を5分以内
- CPEコード生成成功率: 90%以上（Composer/NPM/Dockerファイルから）
- マッチング結果の冪等性: 同一データで3回実行してデータ不整合ゼロ

**定性的指標**:
- 運用性: エンジニアが10分以内に資産登録からマッチング結果確認まで完了可能
- 視認性: ダッシュボードで影響資産数・重要度を即座に把握可能
- 拡張性: 将来的なNVD API、CISA KEVデータとの統合を阻害しない設計

---

## 2. システム全体像

### 2.1 主要機能一覧
- **脆弱性情報取得**: JVN iPedia APIから脆弱性情報を自動取得
- **データ永続化**: PostgreSQLへの安全な保存、差分取得、冪等性保証
- **定期実行**: GitHub Actionsで毎日午前3時に自動実行
- **簡易UI**: FastAPIベースの脆弱性一覧表示

### 2.2 ユーザーロールと権限
**MVPルートのため認証機能なし**
- ゲスト（全ユーザー）: 脆弱性一覧ページの閲覧

### 2.3 認証・認可要件
- 認証方式: なし（公開ページ）
- セキュリティレベル: 公開情報
- 管理機能: 不要

---

## 3. ページ詳細仕様

### 3.1 P-001: 脆弱性一覧ページ

#### 目的
取得した脆弱性情報をテーブル形式で表示し、データ取得の正常性を即座に確認可能にする。

#### 主要機能
- 脆弱性情報の一覧表示（CVE ID、タイトル、重要度、公開日、更新日、詳細表示ボタン）
- 検索機能（CVE ID + タイトルで部分一致検索）
- 詳細表示機能（モーダルウィンドウで概要、CVSS基本値、影響を受ける製品、ベンダー情報、参照情報を表示）
- ページネーション（50件/ページ）
- 基本的なソート機能（公開日、更新日、重要度）

#### 必要な操作
| 操作種別 | 操作内容 | 必要な入力 | 期待される出力 |
|---------|---------|-----------|---------------|
| 取得 | 脆弱性一覧を取得 | ページ番号、ソート条件、検索キーワード（任意） | 脆弱性情報のリスト（50件） |
| 取得 | 脆弱性詳細を取得 | CVE ID | 脆弱性の詳細情報（モーダル表示用） |
| 検索 | CVE ID/タイトルで検索 | 検索キーワード | 検索条件に一致する脆弱性リスト |
| 表示 | 詳細表示モーダルを開く | 詳細表示ボタンクリック、CVE ID | モーダルウィンドウで詳細情報を表示 |

#### 処理フロー

**基本フロー（一覧表示）**:
1. ユーザーがページにアクセス
2. バックエンドがPostgreSQLから脆弱性データを取得
3. 一覧をテーブル形式で表示（デフォルト: 更新日降順）
4. ユーザーがソート条件やページ番号を変更可能

**検索フロー**:
1. ユーザーが検索ボックスにキーワードを入力（CVE IDまたはタイトル）
2. バックエンドがCVE ID・タイトルの両方で部分一致検索
3. 検索結果を一覧表示（ページネーション、ソート機能は維持）
4. 検索キーワードをクリアすると全件表示に戻る

**詳細表示フロー**:
1. ユーザーが一覧の「詳細表示ボタン」をクリック
2. バックエンドがCVE IDで詳細情報を取得
3. モーダルウィンドウを表示（以下の情報を含む）:
   - CVE ID、タイトル、重要度、公開日、更新日（一覧と同じ）
   - 概要（説明文）
   - CVSS基本値
   - 影響を受ける製品
   - ベンダー情報
   - 参照情報（JVN iPedia公式リンク、CWE、CVSS等）
4. モーダル外クリックまたは閉じるボタンでモーダルを閉じる

#### データ構造（概念）
```yaml
Vulnerability:
  識別子: CVE ID（一意）
  基本情報:
    - タイトル（必須）
    - 概要（必須）
    - CVSS基本値（任意）
    - 重要度（任意）
    - 公開日（必須）
    - 更新日（必須）
  詳細情報:
    - 影響を受ける製品（任意）
    - ベンダー情報（任意）
    - 参照情報（任意）
  メタ情報:
    - DB登録日時
    - DB更新日時
  関連:
    - なし（Phase 1では単一エンティティ）
```

---

## 4. データ設計概要

### 4.1 主要エンティティ

```yaml
Vulnerability（脆弱性情報）:
  概要: JVN iPedia APIから取得した脆弱性情報
  主要属性:
    - 識別情報: CVE ID（一意キー）、JVN ID
    - 基本情報: タイトル、概要、公開日、更新日
    - 評価情報: CVSS基本値、重要度、深刻度
    - 詳細情報: 影響を受ける製品、ベンダー情報、参照情報
  関連:
    - なし（Phase 1では単一テーブル）
```

### 4.2 エンティティ関係図
```
Vulnerability（単一エンティティ、Phase 1）

※ Phase 2以降で以下を追加予定:
  - Product（影響を受ける製品）
  - Vendor（ベンダー情報）
  - Reference（参照情報）
```

### 4.3 バリデーションルール
```yaml
CVE ID:
  - ルール: CVE-YYYY-NNNNN形式
  - 理由: 国際標準形式の遵守、一意キー

公開日・更新日:
  - ルール: ISO 8601形式（YYYY-MM-DDTHH:MM:SSZ）
  - 理由: タイムゾーン問題の回避、差分取得の精度保証

CVSS基本値:
  - ルール: 0.0〜10.0の範囲
  - 理由: CVSSスコアの仕様に準拠
```

---

## 5. 制約事項

### 外部API制限
- **JVN iPedia API**: 最大取得件数50件/リクエスト（ページネーション必須）、明示的レート制限なし（推奨: 秒間2-3リクエスト）
- **NVD API 2.0**（推奨実装）: APIキーなし（5req/30s）、APIキーあり（50req/30s）、日付範囲最大120日間
- **CISA KEV**（推奨実装）: 制限なし、ファイルダウンロード方式

### 技術的制約
- **データ取得期間**: Phase 1では直近3年分（設定変更で全期間対応可）
- **処理時間**: 1,000件を10分以内（JVN iPedia APIのレスポンス速度に依存）
- **同時実行**: GitHub Actionsは1日1回実行（並列実行なし）

---

## 5.1 セキュリティ要件

### 基本方針
本プロジェクトは **CVSS 3.1（Common Vulnerability Scoring System）** に準拠したセキュリティ要件を満たすこと。

CVSS 3.1の評価観点:
- **機密性（Confidentiality）**: 不正アクセス防止、データ暗号化
- **完全性（Integrity）**: データ改ざん防止、入力検証
- **可用性（Availability）**: DoS対策、冗長化

詳細な診断と改善は、Phase 11（本番運用診断）で @本番運用診断オーケストレーター が実施します。

---

### プロジェクト固有の必須要件

**認証機能がない場合（本プロジェクト）**:
- ✅ HTTPSの強制（本番環境）
- ✅ セキュリティヘッダー設定（本番環境）
- ✅ 入力値のサニタイゼーション（API応答のXMLパース時）
- ✅ エラーメッセージでの情報漏洩防止

**その他の一般要件**:
- ✅ APIキー・DB接続情報の環境変数管理
- ✅ ログへの機密情報出力禁止
- ✅ 外部API呼び出し時のタイムアウト設定

---

### 運用要件：可用性とヘルスチェック

**ヘルスチェックエンドポイント（全プロジェクト必須）**:
- エンドポイント: `/api/health`
- 目的: Cloud Run/Kubernetesでのliveness/readinessプローブ
- 要件: データベース接続確認、5秒以内の応答

**グレースフルシャットダウン（全プロジェクト必須）**:
- SIGTERMシグナルハンドラーの実装
- 進行中のリクエスト完了まで待機
- タイムアウト: 8秒（Cloud Runの10秒制限に対応）

---

## 6. 複合API処理（バックエンド内部処理）

### 複合処理-001: JVN iPedia 脆弱性情報の差分取得・永続化
**トリガー**: GitHub Actions定期実行（毎日午前3時）または手動実行
**フロントエンドAPI**: なし（バックエンド単独処理）
**バックエンド内部処理**:
1. DB最終更新日時の取得（差分取得の起点決定）
2. JVN iPedia APIへのリクエスト送信（日付範囲指定、ページネーション）
3. XML応答のパース・バリデーション
4. 冪等性を保証したDB保存（UPSERT処理）
5. エラー時のリトライ処理（最大3回）
6. 処理結果のログ出力
**結果**: 取得件数、成功/失敗、エラー詳細をログに記録
**外部サービス依存**: JVN iPedia API

### 複合処理-002: 脆弱性一覧の取得（簡易UI）
**トリガー**: ユーザーが脆弱性一覧ページにアクセス
**フロントエンドAPI**: GET /api/vulnerabilities
**バックエンド内部処理**:
1. クエリパラメータの検証（ページ番号、ソート条件）
2. PostgreSQLからの脆弱性一覧取得（LIMIT/OFFSET）
3. JSON形式での応答生成
**結果**: 脆弱性一覧（50件/ページ）、総件数
**外部サービス依存**: なし

---

## 7. 技術スタック

### フロントエンド（簡易UI）
- フレームワーク: FastAPI + Jinja2
- 言語: Python 3.11+
- UIスタイル: 最小限のCSS（テーブル表示のみ）

### バックエンド
- 言語: Python 3.11+
- フレームワーク: FastAPI
- ORM: SQLAlchemy
- HTTPクライアント: httpx
- XMLパース: xml.etree.ElementTree（標準ライブラリ）

### データベース
- メインDB: PostgreSQL 15+ (Neon推奨 - https://neon.tech)
  - サーバーレスで管理不要
  - 無料枠で十分な容量
  - 自動スケーリング
  - ブランチ機能で開発/本番分離可能

### インフラ
- ホスティング: 未定（Phase 2以降で決定）
- CI/CD: GitHub Actions（定期実行、テスト自動化）

### テスト
- テストフレームワーク: pytest
- カバレッジ: pytest-cov
- 目標カバレッジ: 80%以上

### 開発環境
- コンテナ: Docker Compose（PostgreSQL、Python環境）
- バージョン管理: Git + GitHub

---

## 8. 必要な外部サービス・アカウント

### 必須サービス
| サービス名 | 用途 | 取得先 | 備考 |
|-----------|------|--------|------|
| JVN iPedia API | 脆弱性情報の取得（日本語） | https://jvndb.jvn.jp/apis/myjvn/ | 認証不要、無料、レート制限なし |
| PostgreSQL (Neon) | 脆弱性データの永続化 | https://neon.tech | 無料枠あり、アカウント登録必要（Phase 5で実施） |
| GitHub | リポジトリ管理、Actions実行 | https://github.com | 既存リポジトリ使用 |

### 推奨サービス（Phase 2以降で実装）
| サービス名 | 用途 | 取得先 | 備考 |
|-----------|------|--------|------|
| NVD API 2.0 | 脆弱性情報の取得（英語・最新性） | https://nvd.nist.gov/developers/request-an-api-key | 認証推奨（APIキー無料）、50req/30s |
| CISA KEV | 悪用実績のある脆弱性情報 | https://www.cisa.gov/known-exploited-vulnerabilities-catalog | 認証不要、無料、JSON/CSV |

---

## 9. 今後の拡張予定

**原則**: 拡張予定があっても、必要最小限の実装のみを行う

- 「あったらいいな」は実装しない
- 拡張可能性のための余分な要素は追加しない
- 将来の「もしかして」のための準備は禁止
- 今、ここで必要な最小限の要素のみを実装

拡張が必要になった時点で、Phase 11: 機能拡張オーケストレーターを使用して追加実装を行います。

### 拡張候補（Phase 2以降）
- NVD API統合（最新性・詳細情報の強化）
- CISA KEV統合（悪用実績フラグ、優先度判定）
- 本格的なダッシュボード（React + MUI v6）
- 高度なフィルタリング（製品名、ベンダー、重要度）
- グラフ・統計表示（月別件数、重要度分布）
- CPEマッチング（自社製品への影響評価）
- アラート機能（高重要度脆弱性の通知）
- 認証機能（ユーザー管理、権限設定）

---

**要件定義書 作成日**: 2026-01-07
**最終更新日**: 2026-01-07
**作成者**: BlueLamp 要件定義エージェント

---

# Phase 2: CPEマッチング機能

## 10. システム全体像（Phase 2）

### 10.1 主要機能一覧
- **資産管理**: 手動登録、ファイルアップロード（Composer/NPM/Docker）、CPEコード自動生成
- **CPEマッチング**: 資産情報と脆弱性情報の自動マッチング、バージョン範囲判定
- **結果表示**: 影響を受ける資産と脆弱性の一覧、フィルタリング、統計ダッシュボード
- **定期実行**: GitHub Actionsで新規脆弱性取得後に自動マッチング実行

### 10.2 ユーザーロールと権限
**Phase 2では認証機能なし（Phase 1同様）**
- ゲスト（全ユーザー）: 資産管理、マッチング実行、結果閲覧

### 10.3 認証・認可要件
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

## 7. API仕様（Phase 2）

### 7.1 資産管理API

#### POST /api/assets - 資産登録（手動）
- **機能**: CPEコードを自動生成して資産を登録
- **成功レスポンス**: 201 Created、資産情報とCPEコード
- **失敗レスポンス**: 400 Bad Request（バリデーションエラー）

#### GET /api/assets - 資産一覧取得
- **機能**: ページネーション、フィルタリング（取得元）
- **成功レスポンス**: 200 OK、資産リスト
- **クエリパラメータ**: page, limit, source

#### PUT /api/assets/{asset_id} - 資産更新
- **機能**: 資産情報を更新、CPEコードを再生成
- **成功レスポンス**: 200 OK、更新された資産情報

#### DELETE /api/assets/{asset_id} - 資産削除
- **機能**: 資産とマッチング結果をCASCADE削除
- **成功レスポンス**: 204 No Content

#### POST /api/assets/import/composer - Composerファイルアップロード
- **機能**: composer.json/composer.lockから一括登録
- **成功レスポンス**: 201 Created、登録件数、スキップ件数

#### POST /api/assets/import/npm - NPMファイルアップロード
- **機能**: package.json/package-lock.jsonから一括登録
- **成功レスポンス**: 201 Created、登録件数、スキップ件数

#### POST /api/assets/import/docker - Dockerfileアップロード
- **機能**: Dockerfileから一括登録
- **成功レスポンス**: 201 Created、登録件数、スキップ件数

### 7.2 マッチング実行API

#### POST /api/matching/execute - マッチング実行
- **機能**: 全資産・全脆弱性のマッチング実行
- **成功レスポンス**: 200 OK、マッチング統計、実行時間

#### GET /api/matching/results - マッチング結果一覧
- **機能**: ページネーション、フィルタリング（重要度、資産タイプ）
- **成功レスポンス**: 200 OK、マッチング結果リスト

#### GET /api/matching/assets/{asset_id}/vulnerabilities - 資産別脆弱性一覧
- **機能**: 特定資産に影響する脆弱性リスト
- **成功レスポンス**: 200 OK、脆弱性リスト

#### GET /api/matching/dashboard - 統計情報取得
- **機能**: 影響資産数、重要度別件数、最終マッチング日時
- **成功レスポンス**: 200 OK、統計情報

---

## 8. 実装フェーズ計画（Phase 2）

### Phase 2-1: データモデル実装（完了 ✅）
- Assetモデル作成（src/models/asset.py）
- AssetVulnerabilityMatchモデル作成
- テーブル作成、インデックス作成

### Phase 2-2: CPEコード生成機能（完了 ✅）
- CPEコード生成ユーティリティ（src/utils/cpe_generator.py）
- ベンダーマッピング（NPM_VENDOR_MAP, DOCKER_VENDOR_MAP）
- バージョン正規化ロジック

### Phase 2-3: マッチングアルゴリズム実装（完了 ✅）
- マッチングサービス（src/services/matching_service.py）
- バージョン比較ロジック（packaging.versionを使用）

### Phase 2-4: API実装（完了 ✅）
- 資産管理API（src/api/assets.py）
- ファイルインポートAPI
- マッチング実行API（src/api/matching.py）

### Phase 2-5: UI実装（完了 ✅）
- 資産管理ページ（src/templates/assets.html）
- マッチング結果ページ（src/templates/matching_results.html）
- JavaScript実装（src/static/js/assets.js, matching.js）

### Phase 2-6: テスト・統合（予定）
- 単体テスト（tests/unit/）
- 統合テスト（tests/integration/）
- E2Eテスト（tests/e2e/）
- カバレッジ目標: 80%以上

---

## 9. 非機能要件（Phase 2追加）

### 9.1 パフォーマンス
- **マッチング処理時間**: 1,000資産 × 1,000脆弱性を5分以内
- **ファイルアップロード**: 10MBまでのファイルを10秒以内に処理
- **API応答時間**: 95パーセンタイルで2秒以内

### 9.2 データ整合性
- **マッチング結果の冪等性**: 同一データで3回実行してデータ不整合ゼロ
- **外部キー制約**: 資産削除時にマッチング結果も自動削除（CASCADE）

### 9.3 セキュリティ要件（Phase 2追加）

**ファイルアップロード時のセキュリティ**:
- ✅ ファイルサイズ制限（10MB）
- ✅ MIMEタイプ検証（application/json, text/plain）
- ✅ ファイル名のサニタイゼーション（パストラバーサル攻撃防止）
- ✅ アップロード先ディレクトリの権限制限

---

# Phase 3: Reactダッシュボード機能

## 10. システム全体像（Phase 3）

### 10.1 Phase 3の目的
既存のFastAPI + Jinja2ベースの3ページ（脆弱性一覧、資産管理、マッチング結果）をReact + TypeScriptで完全に書き換え、ウィジェット方式のモダンなダッシュボードUIを実装する。すべての既存機能を維持しながら、一貫したUI/UX、高速なSPA体験、柔軟なウィジェット管理を実現する。

### 10.2 主要機能一覧
- **Reactアプリケーション**: Vite + React + TypeScriptによるモダンなSPA
- **既存3ページのReact化**: 脆弱性一覧、資産管理、マッチング結果を完全にReactコンポーネント化
- **ウィジェット方式ダッシュボード**: サマリーカード、トレンドチャート、重要度分布などの独立したウィジェット
- **設定ファイル方式**: JSON/DBでウィジェットの追加・削除・並び替えを管理
- **統一されたUI/UX**: Catppuccin風ダークテーマ、一貫したデザインシステム
- **状態管理**: Zustandによるグローバル状態管理
- **ルーティング**: React Router v6によるクライアントサイドルーティング

### 10.3 成功指標

#### 定量的指標
- **パフォーマンス**: Lighthouseスコア90以上（Performance、Accessibility、Best Practices）
- **バンドルサイズ**: 初期ロード500KB以下（gzip圧縮後）
- **レスポンス時間**: 画面遷移200ms以内
- **テストカバレッジ**: 80%以上（既存テストを全てパス）
- **既存機能の互換性**: 100%（既存の226テストを全てパス）

#### 定性的指標
- **保守性**: 新規メンバーがコンポーネント構造を1時間以内に理解可能
- **拡張性**: 新しいウィジェット追加がコンポーネント作成+レジストリ登録のみで完結
- **一貫性**: 全ページで統一されたデザインシステム（色、タイポグラフィ、スペーシング）
- **視認性**: ダークテーマでの視認性向上、アクセシビリティ対応

---

## 3. ページ詳細仕様（Phase 3）

### 3.4 P-004: ダッシュボードホームページ

#### 目的
脆弱性管理システムの全体像を即座に把握可能な、ウィジェット方式のダッシュボード。重要度別の脆弱性件数、トレンド、資産ランキング、最近のアクティビティを1画面で確認できる。

#### 主要機能
- **ウィジェットグリッド**: 4カラムのレスポンシブグリッドレイアウト
- **サマリーカード**: Critical/High/Medium/Lowの件数表示（前週比の増減表示）
- **トレンドチャート**: 過去30日間の検出数推移（折れ線グラフ）
- **重要度分布**: 円グラフ/ドーナツチャートで重要度割合を可視化
- **脆弱性一覧**: Critical/High脆弱性のTOP10をテーブル表示
- **資産ランキング**: 脆弱性の多い資産TOP10
- **KEVアラート**: CISA KEV登録の脆弱性一覧（将来実装）
- **期間選択**: 直近7日/30日/90日/全期間のフィルタリング
- **ウィジェット管理**: 追加・削除・並び替え（設定ファイルで管理）

#### 必要な操作
| 操作種別 | 操作内容 | 必要な入力 | 期待される出力 |
|---------|---------|-----------|---------------|
| 取得 | ダッシュボードサマリーを取得 | 期間（任意） | 重要度別件数、前週比、ステータス別件数 |
| 取得 | トレンドデータを取得 | 日数（7/30/90/全期間） | 日別の検出数・対応完了数 |
| 取得 | 重要度分布を取得 | なし | Critical/High/Medium/Lowの割合 |
| 取得 | 脆弱性TOP10を取得 | 重要度フィルタ（任意） | 最新のCritical/High脆弱性リスト |
| 取得 | 資産ランキングを取得 | なし | 脆弱性が多い資産TOP10 |
| 更新 | ウィジェット設定を保存 | ウィジェット配置・表示設定 | 設定保存完了 |

#### 処理フロー

**ダッシュボード表示フロー**:
1. ユーザーが `/dashboard` にアクセス
2. バックエンドから以下のデータを並列取得:
   - サマリーデータ（GET /api/dashboard/summary）
   - トレンドデータ（GET /api/dashboard/trend）
   - 重要度分布（GET /api/dashboard/severity-distribution）
   - 脆弱性TOP10（GET /api/vulnerabilities?severity=Critical,High&limit=10）
   - 資産ランキング（GET /api/dashboard/asset-ranking）
3. 各ウィジェットにデータを配信
4. レスポンシブグリッドでレイアウト表示
5. ローディング状態の管理（Suspense/ErrorBoundary）

**ウィジェット管理フロー**:
1. ユーザーが「+ ウィジェット追加」ボタンをクリック
2. ウィジェットカタログモーダルを表示
3. ユーザーがウィジェットを選択
4. 新しいウィジェットをグリッドに追加
5. 設定をローカルストレージ/DBに保存

**ウィジェット削除フロー**:
1. ユーザーがウィジェット右上の「⋮」メニューをクリック
2. 「削除」を選択
3. 確認ダイアログ表示
4. ウィジェットを削除
5. 設定を更新

#### データ構造（概念）
```yaml
DashboardSummary:
  重要度別件数:
    - Critical: 整数
    - High: 整数
    - Medium: 整数
    - Low: 整数
  前週比:
    - Critical: 整数（差分）
    - High: 整数（差分）
    - Medium: 整数（差分）
    - Low: 整数（差分）
  ステータス別件数:
    - 未対応: 整数
    - 対応中: 整数
    - 対応完了: 整数

TrendData:
  データポイント:
    - 日付: 日付型（YYYY-MM-DD）
    - 検出数: 整数
    - 対応完了数: 整数

WidgetConfig:
  ウィジェット設定:
    - id: 文字列（一意識別子）
    - type: 文字列（summary/trend_chart/severity_pie等）
    - title: 文字列（表示タイトル）
    - enabled: ブール値（表示/非表示）
    - position: 整数（表示順序）
    - size: 文字列（small/medium/wide/full）
    - settings: オブジェクト（ウィジェット固有設定）
```

### 3.5 既存ページのReact化

#### P-001（React版）: 脆弱性一覧ページ
**目的**: 既存のJinja2版と同じ機能をReactで実装。検索、ソート、ページネーション、詳細表示モーダルを提供。

**主要機能**:
- 脆弱性一覧表示（テーブル形式）
- 検索機能（CVE ID + タイトルで部分一致検索）
- ソート機能（公開日、更新日、重要度）
- ページネーション（50件/ページ）
- 詳細表示モーダル（概要、CVSS、影響製品、ベンダー情報、参照情報）
- リアルタイム取得ボタン（JVN iPedia APIから即座に取得）

**React実装の特徴**:
- `useVulnerabilities` カスタムフックでデータ取得・状態管理
- `VulnerabilityTable` コンポーネントでテーブル表示
- `VulnerabilityDetailModal` でモーダル表示
- React Query（TanStack Query）によるキャッシング・リフェッチ

#### P-002（React版）: 資産管理ページ
**目的**: 既存のJinja2版と同じ機能をReactで実装。資産の登録、編集、削除、ファイルインポートを提供。

**主要機能**:
- 資産一覧表示（テーブル形式）
- 新規登録モーダル（手動入力フォーム）
- ファイルアップロードモーダル（Composer/NPM/Docker、ドラッグ&ドロップ対応）
- 編集・削除機能
- ページネーション（50件/ページ）
- フィルタリング（取得元: manual/composer/npm/docker）

**React実装の特徴**:
- `useAssets` カスタムフックでデータ取得・状態管理
- `AssetTable` コンポーネントでテーブル表示
- `AssetFormModal` で新規登録・編集
- `FileUploadModal` でファイルアップロード
- React Hook Form によるフォームバリデーション

#### P-003（React版）: マッチング結果ページ
**目的**: 既存のJinja2版と同じ機能をReactで実装。マッチング結果一覧、統計ダッシュボード、マッチング実行を提供。

**主要機能**:
- マッチング結果一覧表示（テーブル形式）
- 統計ダッシュボード（影響資産数、Critical/High脆弱性数、最新マッチング日時）
- マッチング実行ボタン
- フィルタリング（重要度、資産タイプ）
- ページネーション（50件/ページ）

**React実装の特徴**:
- `useMatching` カスタムフックでデータ取得・状態管理
- `MatchingDashboard` コンポーネントで統計表示
- `MatchingTable` コンポーネントでテーブル表示
- `executeMatching` による非同期マッチング実行

---

## 4. ウィジェットカタログ（Phase 3）

### 4.1 利用可能なウィジェット

| ウィジェットID | 名称 | サイズ | 説明 | 必要API |
|-------------|------|-------|------|--------|
| `summary-critical` | 🔴 Critical サマリー | small | Critical脆弱性件数、前週比 | GET /api/dashboard/summary |
| `summary-high` | 🟠 High サマリー | small | High脆弱性件数、前週比 | GET /api/dashboard/summary |
| `summary-medium` | 🔵 Medium サマリー | small | Medium脆弱性件数、前週比 | GET /api/dashboard/summary |
| `summary-low` | 🟢 Low サマリー | small | Low脆弱性件数、前週比 | GET /api/dashboard/summary |
| `trend-chart` | 📈 トレンドチャート | wide | 過去30日の検出数推移 | GET /api/dashboard/trend |
| `severity-pie` | 📊 重要度分布 | wide | 円グラフで重要度割合 | GET /api/dashboard/severity-distribution |
| `vuln-list` | 📋 脆弱性一覧 | full | Critical/High TOP10 | GET /api/vulnerabilities |
| `asset-ranking` | 🖥️ 資産ランキング | wide | 脆弱性の多い資産TOP10 | GET /api/dashboard/asset-ranking |
| `kev-alert` | ⚠️ KEVアラート | wide | CISA KEV登録脆弱性 | GET /api/kev/alerts（将来実装） |
| `activity-feed` | 🔔 アクティビティ | medium | 最近の検出・対応履歴 | GET /api/dashboard/activity（将来実装） |

### 4.2 ウィジェットサイズ仕様

| サイズ | グリッド幅 | 用途 | 例 |
|------|----------|------|-----|
| `small` | 1カラム | 単一の数値表示 | サマリーカード |
| `medium` | 2カラム | 中規模のチャート・リスト | アクティビティフィード |
| `wide` | 2カラム | 横長のチャート | トレンドチャート、重要度分布 |
| `full` | 4カラム | テーブル表示 | 脆弱性一覧 |

---

## 7. 技術スタック（Phase 3）

### フロントエンド
- **フレームワーク**: React 18+ + TypeScript 5+
- **ビルドツール**: Vite 5+
- **ルーティング**: React Router v6
- **状態管理**: Zustand 4+
- **データフェッチング**: TanStack Query v5（React Query）
- **フォーム**: React Hook Form + Zod
- **UIライブラリ**: Tailwind CSS 3+ + shadcn/ui
- **チャート**: Recharts 2+
- **アイコン**: Lucide React
- **ドラッグ&ドロップ**: dnd-kit（将来実装）

### バックエンド（変更なし）
- **言語**: Python 3.11+
- **フレームワーク**: FastAPI
- **ORM**: SQLAlchemy
- **データベース**: PostgreSQL 15+ (Neon)

### 新規APIエンドポイント（Phase 3）

| エンドポイント | メソッド | 機能 |
|-------------|---------|------|
| `/api/dashboard/summary` | GET | サマリーデータ取得（重要度別件数、前週比） |
| `/api/dashboard/trend` | GET | トレンドデータ取得（日別検出数・対応完了数） |
| `/api/dashboard/severity-distribution` | GET | 重要度分布取得 |
| `/api/dashboard/asset-ranking` | GET | 資産ランキング取得 |
| `/api/dashboard/config` | GET | ユーザーのダッシュボード設定取得 |
| `/api/dashboard/config` | PUT | ダッシュボード設定保存 |

---

## 8. 実装フェーズ計画（Phase 3）

### Phase 3-1: React プロジェクトセットアップ（完了予定）
- Vite + React + TypeScript プロジェクト作成
- Tailwind CSS + shadcn/ui セットアップ
- React Router v6 セットアップ
- Zustand、TanStack Query セットアップ
- ESLint、Prettier 設定

### Phase 3-2: 既存3ページのReact化 - 脆弱性一覧（完了予定）
- `VulnerabilityListPage` コンポーネント作成
- `useVulnerabilities` カスタムフック実装
- `VulnerabilityTable` コンポーネント実装
- `VulnerabilityDetailModal` 実装
- 検索、ソート、ページネーション実装

### Phase 3-3: 既存3ページのReact化 - 資産管理（完了予定）
- `AssetManagementPage` コンポーネント作成
- `useAssets` カスタムフック実装
- `AssetTable` コンポーネント実装
- `AssetFormModal` 実装（新規登録・編集）
- `FileUploadModal` 実装（ドラッグ&ドロップ対応）

### Phase 3-4: 既存3ページのReact化 - マッチング結果（完了予定）
- `MatchingResultsPage` コンポーネント作成
- `useMatching` カスタムフック実装
- `MatchingDashboard` コンポーネント実装
- `MatchingTable` コンポーネント実装
- マッチング実行機能実装

### Phase 3-5: ウィジェット方式ダッシュボード実装（完了予定）
- `Dashboard` コンポーネント作成
- `WidgetWrapper` 共通ラッパー実装
- ウィジェットレジストリ実装
- サマリーカード実装（Critical/High/Medium/Low）
- トレンドチャート実装（Recharts）
- 重要度分布チャート実装
- 脆弱性一覧ウィジェット実装
- 資産ランキングウィジェット実装

### Phase 3-6: ウィジェット管理機能（完了予定）
- `useWidgetConfig` カスタムフック実装
- ウィジェット追加・削除機能
- 設定ファイル（JSON）による管理
- ローカルストレージ連携

### Phase 3-7: バックエンドAPI実装（完了予定）
- `/api/dashboard/summary` 実装
- `/api/dashboard/trend` 実装
- `/api/dashboard/severity-distribution` 実装
- `/api/dashboard/asset-ranking` 実装
- `/api/dashboard/config` 実装（GET/PUT）

### Phase 3-8: テスト・統合（完了予定）
- 既存の226テストを全てパス
- 新規Reactコンポーネントのテスト
- E2Eテスト（Playwright）
- パフォーマンステスト（Lighthouse）
- カバレッジ目標: 80%以上

---

## 9. 非機能要件（Phase 3追加）

### 9.1 パフォーマンス
- **初期ロード時間**: 3秒以内（3G回線）
- **バンドルサイズ**: 500KB以下（gzip圧縮後）
- **Lighthouseスコア**: 90以上（Performance、Accessibility、Best Practices）
- **画面遷移**: 200ms以内
- **APIレスポンス**: 95パーセンタイルで2秒以内

### 9.2 アクセシビリティ
- **WCAG 2.1 レベルAA**: 準拠
- **キーボードナビゲーション**: 全機能で対応
- **スクリーンリーダー**: ARIA属性による対応
- **色覚異常対応**: カラーブラインドモード対応

### 9.3 セキュリティ要件（Phase 3追加）
- **HTTPS強制**: 本番環境で必須
- **CSP（Content Security Policy）**: 設定済み
- **XSS対策**: React標準のエスケープ処理
- **CSRF対策**: FastAPI標準のCSRF保護

---

**要件定義書 作成日**: 2026-01-07
**最終更新日**: 2026-01-30
**作成者**: BlueLamp 要件定義エージェント
**Phase 1実装完了**: 2026-01-08
**Phase 2実装完了**: 2026-01-27
**Phase 3実装予定**: 2026-01-30〜（Reactダッシュボード）
