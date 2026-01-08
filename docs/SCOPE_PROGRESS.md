# 脆弱性管理システム 開発進捗状況

## 1. 基本情報

- **プロジェクト名**: 脆弱性管理システム（Phase 1: 脆弱性情報取得基盤）
- **ステータス**: Phase 9 完了 → Phase 10 本番運用準備へ
- **完了フェーズ**: Phase 1（要件定義）、Phase 2（Git/GitHub）、Phase 3（スキップ）、Phase 4（ページ実装）、Phase 5（環境構築）、Phase 6（バックエンド計画）、Phase 7（バックエンド実装）、Phase 8（スキップ）、Phase 9（テスト・Docker環境）
- **進捗率**: Phase 9まで完了（9/11フェーズ、82%）
- **次のマイルストーン**: Phase 10 本番運用保障
- **最終更新日**: 2026-01-09

## 2. Phase 1 開発フロー

BlueLampでの開発は以下のフローに沿って進行します。

### Phase 1: 要件定義（完了）

- [x] Step#1: 成果目標と成功指標の明確化
- [x] Step#2: 実現可能性調査（JVN iPedia API、NVD API、CISA KEV）
- [x] Step#2.5: 開発アプローチの選択（MVP or 通常版）→ MVPルート選択
- [x] Step#3: 認証・権限設計（スキップ - MVPルートのため不要）
- [x] Step#4: ページリストの作成（簡易UI設計）→ P-001: 脆弱性一覧ページ
- [x] Step#5: 技術スタック最終決定 → Python + FastAPI + PostgreSQL(Neon)
- [x] Step#6: 外部API最終決定 → JVN iPedia API（必須）、NVD/CISA KEV（推奨）
- [x] Step#7: 要件定義書の書き出し（docs/requirements.md）
- [x] Step#7.5: 品質基準設定（Lint設定ファイル生成 - .flake8, pyproject.toml）
- [x] Step#8: SCOPE_PROGRESS更新（統合ページ管理表追加）
- [x] Step#9: CLAUDE.md生成
- [x] Step#10: ページの深掘り（検索機能、詳細表示モーダル追加）

### Phase 2: Git/GitHub管理（完了）

- [x] Git hooks設定（pre-commit: 構文・型・Lint・フォーマット・テスト）
- [x] GitHub Actions CI/CD設定
- [x] 脆弱性情報定期取得ワークフロー設定（日本時間午前3時）

### Phase 3: フロントエンド基盤（スキップ）

- [x] **Phase 3 スキップ理由**: FastAPI + Jinja2による簡易UI実装のため、React + Vite + MUI基盤は不要

### Phase 4: ページ実装（完了 ✅ 2026-01-08）

- [x] HTMLモックアップ作成（mockups/VulnerabilityList.html）
- [x] ユーザーフィードバック収集と反映
- [x] データモデリング（SQLAlchemy + Pydantic）
  - src/models/vulnerability.py - Vulnerabilityモデル
  - src/schemas/vulnerability.py - Pydanticスキーマ
  - src/database.py - DB接続設定
  - src/config.py - 環境変数管理
- [x] FastAPI + Jinja2実装（P-001ページ）
  - src/main.py - FastAPIアプリケーション
  - src/api/vulnerabilities.py - APIエンドポイント
  - src/services/mock_vulnerability_service.py - モックサービス（@MOCK_TO_APIマーク付き）
  - src/templates/ - Jinja2テンプレート
  - src/static/ - CSS/JavaScript
- [x] API統合準備
  - docs/api-specs/vulnerability-list-api.md - API仕様書生成
  - @MOCK_TO_APIマーク配置（9箇所）
- [x] ドキュメント整備
  - SETUP_GUIDE.md - セットアップ手順（WSL環境対応）
  - IMPLEMENTATION_SUMMARY.md - 実装サマリー
  - DATA_MODELS.md - データモデル仕様書
- [x] バグ修正
  - ソート機能のパラメータ解析エラー修正（src/static/js/main.js）

**成果物**: 25ファイル、3,761行のコード
**コミット**:
  - `2486e48` Phase 4完了: FastAPI + Jinja2による脆弱性一覧ページ実装
  - `b8e2220` バグ修正: ソート機能のパラメータ解析エラーを修正

### Phase 5: 環境構築（完了 ✅ 2026-01-08）

**完了内容**:
- [x] PostgreSQL（Neon）セットアップ
  - Neonアカウント作成
  - データベース作成（リージョン: AWS ap-southeast-1 シンガポール）
  - 接続文字列取得と.env設定
- [x] データベース初期化
  - テーブル作成（Vulnerabilityテーブル）
  - 接続確認（PostgreSQL 17.7）
  - インデックス作成（cve_id、published_date、modified_date、severity）
- [x] 環境変数の最終確認
  - DATABASE_URL設定（Neon接続文字列）
  - JVN_API_ENDPOINT設定
  - その他の設定（LOG_LEVEL、DEBUG、PORT、FETCH_ALL_DATA）

**成果物**:
- データベース: neondb（Neon PostgreSQL 17.7）
- テーブル: vulnerabilities（12カラム、4インデックス）
- 環境変数設定完了（.env）

### Phase 6: バックエンド実装計画（完了 ✅ 2026-01-08）

#### 6.1 実装マイルストーン

このプロジェクトは認証なしの公開APIで、エンドポイント数が少ないため、レイヤー別実装マイルストーン方式で進めます。

| マイルストーン | 主要タスク | 依存関係 | 並列実装 | 完了 |
|--------------|----------|---------|---------|------|
| M1: JVN API統合基盤 | JVN iPedia API Fetcherクラス実装、XML解析、差分取得ロジック | なし | 不可 | [x] |
| M2: データ永続化 | DatabaseVulnerabilityService実装、UPSERT処理、トランザクション管理 | M1（テストデータ取得に必要） | 不可 | [x] |
| M3: API統合 | モックサービス置き換え、エラーハンドリング | M1, M2 | 不可 | [x] |
| M4: リトライ・冪等性 | リトライロジック、冪等性テスト（3回実行） | M1, M2, M3 | 不可 | [x] |
| M5: ヘルスチェック拡張 | DB接続確認、応答時間保証 | M2 | 可能（M4と並列） | [x] |
| M6: 自動化 | GitHub Actions定期実行、エラー通知 | M1, M2, M3, M4 | 不可 | [x] |

**注記**: このプロジェクトは単純なデータ取得・保存フローのため、並列実装の余地は限定的です。

---

#### 6.2 エンドポイント実装タスクリスト

##### M1: JVN API統合基盤

| タスク | ファイル | 実装内容 | 完了 |
|--------|---------|---------|------|
| M1.1 | src/fetchers/jvn_fetcher.py | JVNFetcherServiceクラス作成 | [x] |
| M1.2 | src/fetchers/jvn_fetcher.py | XML応答パース処理（xml.etree.ElementTree） | [x] |
| M1.3 | src/fetchers/jvn_fetcher.py | 差分取得ロジック（lastModStartDate/lastModEndDate） | [x] |
| M1.4 | src/fetchers/jvn_fetcher.py | ページネーション処理（50件/リクエスト） | [x] |
| M1.5 | src/fetchers/jvn_fetcher.py | タイムアウト設定（30秒） | [x] |
| M1.6 | src/fetchers/jvn_fetcher.py | レート制限対応（秒間2-3リクエスト） | [x] |

##### M2: データ永続化

| タスク | ファイル | 実装内容 | 完了 |
|--------|---------|---------|------|
| M2.1 | src/services/database_vulnerability_service.py | DatabaseVulnerabilityServiceクラス作成 | [x] |
| M2.2 | src/services/database_vulnerability_service.py | search_vulnerabilities()実装（SQLAlchemyクエリ） | [x] |
| M2.3 | src/services/database_vulnerability_service.py | ソート機能（重要度のカスタムソート含む） | [x] |
| M2.4 | src/services/database_vulnerability_service.py | get_vulnerability_by_cve_id()実装 | [x] |
| M2.5 | src/services/database_vulnerability_service.py | UPSERT処理（ON CONFLICT DO UPDATE） | [x] |
| M2.6 | src/services/database_vulnerability_service.py | トランザクション管理 | [x] |

##### M3: API統合

| タスク | ファイル | 実装内容 | 完了 |
|--------|---------|---------|------|
| M3.1 | src/api/vulnerabilities.py | list_vulnerabilities()のモックサービス置き換え | [x] |
| M3.2 | src/api/vulnerabilities.py | get_vulnerability_detail()のモックサービス置き換え | [x] |
| M3.3 | src/api/vulnerabilities.py | エラーハンドリング（DB接続エラー、クエリエラー） | [x] |

##### M4: リトライ・冪等性

| タスク | ファイル | 実装内容 | 完了 |
|--------|---------|---------|------|
| M4.1 | src/fetchers/jvn_fetcher.py | リトライロジック（最大3回、指数バックオフ） | [x] |
| M4.2 | tests/integration/test_idempotency.py | 冪等性テスト（同一処理3回実行でデータ不整合ゼロ） | [x] |

**M4実装詳細**:
- M4.1: リトライロジックはM1で既に実装済み（最大3回、指数バックオフ 5s→10s→20s）
- M4.2: 統合テスト `test_idempotency.py` を新規作成
  - エンドツーエンド冪等性検証（JVN API取得 → DB保存 3回実行）
  - バッチUPSERT冪等性検証
  - データ再取得時の冪等性検証
  - 全テスト合格（5 passed in 26.01s）
  - 検証結果: データ不整合ゼロ（要件達成）

##### M5: ヘルスチェック拡張

| タスク | ファイル | 実装内容 | 完了 |
|--------|---------|---------|------|
| M5.1 | src/main.py | health_check()にDB接続確認追加 | [x] |
| M5.2 | src/main.py | 応答時間5秒以内保証 | [x] |
| M5.3 | src/main.py | エラー時の適切なステータスコード返却 | [x] |

##### M6: 自動化

| タスク | ファイル | 実装内容 | 完了 |
|--------|---------|---------|------|
| M6.1 | .github/workflows/daily_fetch.yml | 定期実行ワークフロー（毎日午前3時） | [x] |
| M6.2 | .github/workflows/daily_fetch.yml | 手動実行トリガー（workflow_dispatch） | [x] |
| M6.3 | .github/workflows/daily_fetch.yml | エラー通知設定（GitHub Issues作成） | [x] |
| M6.4 | scripts/fetch_vulnerabilities.py | データ取得スクリプト（JVNFetcher + DatabaseService統合） | [x] |

---

#### 6.3 @MOCK_TO_API置き換えタスク

| # | ファイル | 行番号 | 現在の実装 | Phase 7での実装 | 完了 |
|---|---------|-------|-----------|----------------|------|
| 1 | src/services/mock_vulnerability_service.py | 5 | モッククラス全体 | DatabaseVulnerabilityServiceで置き換え | [x] |
| 2 | src/services/mock_vulnerability_service.py | 33 | _generate_mock_data() | JVNFetcherServiceで実データ取得 | [x] |
| 3 | src/services/mock_vulnerability_service.py | 183 | search_vulnerabilities() | SQLAlchemyクエリで実装 | [x] |
| 4 | src/api/vulnerabilities.py | 88 | MockVulnerabilityService() | DatabaseVulnerabilityService(db)に置き換え | [x] |
| 5 | src/api/vulnerabilities.py | 134 | mock_service.get_vulnerability_by_cve_id() | db.query(Vulnerability).filter()に置き換え | [x] |
| 6 | src/main.py | 53 | 簡易ヘルスチェック | DB接続確認を追加 | [x] |

---

#### 6.4 実装スケジュール

```
Week 1:
  Day 1-2: |====== M1: JVN API統合基盤 ======|
  Day 3-4: |==== M2: データ永続化 ====|
  Day 5:   |== M3: API統合 ==|

Week 2:
  Day 1-2: |=== M4: リトライ・冪等性 ===|
  Day 1-2: |== M5: ヘルスチェック ==|  ← M4と並列可能
  Day 3-4: |==== M6: 自動化 ====|
  Day 5:   |= 総合テスト =|
```

**推定工数**:
- M1: 16時間（JVN API統合基盤）
- M2: 12時間（データ永続化）
- M3: 4時間（API統合）
- M4: 8時間（リトライ・冪等性）
- M5: 4時間（ヘルスチェック拡張）
- M6: 8時間（自動化）
- **合計**: 52時間（約6.5日）

---

#### 6.5 テスト戦略

| テスト種別 | 対象 | カバレッジ目標 | 実施タイミング |
|----------|------|--------------|-------------|
| 単体テスト | 各サービスクラス | 80%以上 | 各マイルストーン完了時 |
| 統合テスト | JVN API + DB | 100%（主要パス） | M2完了時 |
| 冪等性テスト | データ取得処理 | 3回実行でデータ不整合ゼロ | M4完了時 |
| E2Eテスト | 全エンドポイント | 100%（全API） | M6完了時 |

---

### Phase 7: バックエンド実装（完了 ✅ 2026-01-08）

**完了内容**:
- [x] M1: JVN API統合基盤（JVNFetcherService実装）
- [x] M2: データ永続化（DatabaseVulnerabilityService実装）
- [x] M3: API統合（モックサービス置き換え）
- [x] M4: リトライ・冪等性（リトライロジック、冪等性テスト）
- [x] M5: ヘルスチェック拡張（DB接続確認、応答時間保証）
- [x] M6: 自動化（GitHub Actions定期実行、エラー通知）

**統合テスト結果**:
- **PASSED**: 49/49 (100%)
- **FAILED**: 0/49 (0%)
- **実行時間**: 78.52秒
- **実データベース接続**: Neon PostgreSQL
- **実JVN iPedia API接続**: https://jvndb.jvn.jp/myjvn
- **モック使用**: なし（全統合テスト）

**成果物**:
- src/fetchers/jvn_fetcher.py（JVN iPedia API統合）
- src/services/database_vulnerability_service.py（データ永続化）
- src/api/vulnerabilities.py（モックサービス置き換え完了）
- tests/integration/（5ファイル、49テストケース）
- scripts/fetch_vulnerabilities.py（データ取得スクリプト）
- .github/workflows/daily_fetch.yml（定期実行ワークフロー）

**初期データ取得**:
- 取得期間: 2023-01-09 ～ 2026-01-08（過去3年分）
- 総レコード数: 963件
- 重要度別内訳:
  - Critical: 243件 (25%)
  - High: 359件 (37%)
  - Medium: 295件 (31%)
  - Low: 32件 (3%)
  - 不明: 34件 (4%)

**GitHub Actions設定**:
- [x] DATABASE_URL をGitHub Secretsに登録
- [x] ワークフローのエラー修正（PYTHONPATH設定、Issue作成権限追加）
- [x] 手動実行テスト成功（1件取得・更新、エラー0件）
- [ ] 定期実行の動作確認（翌日午前3時に自動実行予定）

**最終動作確認**:
- [x] ローカルAPI動作確認（ヘルスチェック: healthy、DB接続: OK）
- [x] データベース統計確認（963件、Critical 25.2%、High 37.3%）
- [x] GitHub Actions手動実行確認（差分取得モード: 1件更新、3.28秒）

**コミット情報**:
- ca1741b: Phase 7完了（20ファイル、4,025行追加）
- 1cc46e0: GitHub Actionsエラー修正（権限とPYTHONPATH）
- 317d833: ドキュメント更新（初期データ取得結果、GitHub Actions設定）

**Phase 7完了日**: 2026-01-08
**次のフェーズ**: Phase 9 テスト・Docker環境

### Phase 8: API統合（スキップ ✅ 2026-01-08）

- [x] **Phase 8 スキップ理由**: API統合はPhase 7のM3（マイルストーン3）で完了済み。モックサービスを実データベース統合に置き換え済み。

### Phase 9: テスト実装・Docker環境（完了 ✅ 2026-01-09）

**完了内容**:
- [x] テストカバレッジ67%→81%達成（目標: 80%以上）
- [x] エラーハンドリングテスト追加（13テストケース）
- [x] Web UIのE2Eテスト実装（11テストケース）
- [x] Docker Compose環境整備
- [x] モックサービス削除（クリーンアップ）

**テスト結果**:
- **総テスト数**: 73テスト（全合格 ✅）
  - 統合テスト: 62テスト
  - エラーハンドリングテスト: 13テスト
  - E2Eテスト: 11テスト
- **テストカバレッジ**: 81%（目標: 80%以上を達成）
- **実行時間**: 約2分

**成果物**:
- tests/integration/test_error_handling.py（285行）
- tests/e2e/test_web_ui.py（283行）
- docker-compose.yml（PostgreSQL + API）
- Dockerfile（マルチステージビルド）
- .dockerignore

**削除ファイル**:
- src/services/mock_vulnerability_service.py（54行、Phase 7で置き換え済み）

**更新ファイル**:
- requirements.txt（+beautifulsoup4）
- CLAUDE.md（セクション13追加: E2Eテスト自律実行の原則）

**コミット情報**:
- 予定: Phase 9完了（7ファイル追加、3ファイル更新、1ファイル削除）

**Phase 9完了日**: 2026-01-09
**次のフェーズ**: Phase 10 本番運用保障

### Phase 10以降（予定）

- [ ] Phase 10: 本番運用保障
- [ ] Phase 11: デプロイメント

## 3. 成果目標（Step#1で確定）

### 最終成果
JVN iPedia APIから脆弱性情報（直近3年分、全期間対応可能）を自動取得し、PostgreSQLに永続化する堅牢なデータ基盤。GitHub Actionsで定期実行（毎日午前3時）、簡易UIで動作確認可能、Phase 2以降の拡張を阻害しない設計。

### 定量的指標
1. データ取得成功率: 99.9%以上（JVN iPedia APIに適用、リトライ3回、API完全障害のみ許容）
2. 差分取得精度: 100%（新規・更新分を漏れなく取得）
3. 処理時間: 1,000件を10分以内
4. コードカバレッジ: 80%以上
5. 冪等性: 同一処理3回実行でデータ不整合ゼロ

### 定性的指標
1. 保守性: 新規メンバーが1時間以内にコード構造を理解可能
2. 拡張性: 設定変更のみで「3年分→全期間」に拡張可能
3. 運用性: エラー発生時、ログから5分以内に原因特定可能
4. 堅牢性: API障害時もデータ損失・DB破損なし
5. 視認性: 簡易UIで取得データの正常性を即座に確認可能

## 4. スコープ定義

### 必須実装（Phase 1）
- ✅ JVN iPedia API統合（Phase 7完了）
- ✅ PostgreSQL永続化（SQLAlchemy）（Phase 7完了）
- ✅ 差分取得ロジック（Phase 7完了）
- ✅ リトライ処理（3回）（Phase 7完了）
- ✅ エラーハンドリング・詳細ログ（Phase 7完了）
- ✅ 簡易Web UI（FastAPI）（Phase 4完了）
- ✅ GitHub Actions定期実行（Phase 7完了）
- ✅ Docker Compose環境（Phase 9完了）
- ✅ pytest + カバレッジ81%（目標: 80%以上）（Phase 9完了）
- ✅ README・セットアップ手順（Phase 4完了）

### 推奨実装（時間があれば）
- 🔵 CISA KEV統合（優先度: 高 - 実装が容易で優先度判定に有用）
- 🔵 NVD API統合（優先度: 中 - 最新性が必要な場合）
- 🔵 取得期間の全期間対応（優先度: 低 - 設定変更で対応可能）

## 5. 技術スタック（仮）

- 言語: Python 3.11+
- DB: PostgreSQL 15+ (推奨: Neon - https://neon.tech)
- ORM: SQLAlchemy
- HTTPクライアント: httpx または requests
- テスト: pytest
- Web UI: FastAPI + Jinja2
- CI/CD: GitHub Actions（毎日午前3時実行）

## 6. 外部API調査結果（Step#2で完了）

### JVN iPedia API（必須）
- **エンドポイント**: https://jvndb.jvn.jp/myjvn
- **認証**: 不要
- **レート制限**: 明示的制限なし（推奨: 秒間2-3リクエスト）
- **データ形式**: XML
- **最大取得件数**: 50件/リクエスト（ページネーション必須）
- **差分取得**: 日付範囲指定で可能
- **コスト**: 無料

### NVD API 2.0（推奨・時間があれば）
- **エンドポイント**: https://services.nvd.nist.gov/rest/json/cves/2.0
- **認証**: APIキー推奨（無料取得、50req/30s）
- **レート制限**: APIキーなし（5req/30s）、あり（50req/30s）
- **データ形式**: JSON
- **最大取得件数**: 2,000件/リクエスト
- **差分取得**: lastModStartDate/lastModEndDateで可能
- **注意点**: エンリッチメント遅延あり、日付範囲最大120日間
- **コスト**: 無料

### CISA KEV（推奨・時間があれば）
- **エンドポイント**: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
- **認証**: 不要
- **レート制限**: なし
- **データ形式**: JSON/CSV
- **取得方法**: ファイルダウンロード
- **更新頻度**: 継続的（平日営業時間内）
- **コスト**: 無料
- **特徴**: 悪用実績フラグ、対応期限、ランサムウェア情報あり

## 7. 開発アプローチ（Step#2.5で確定）

**選択: アプローチA - 究極のMVP（1ページ）**

### Phase 1実装範囲
- バックエンド: JVN iPedia API統合、PostgreSQL、差分取得、リトライ処理、GitHub Actions
- 簡易UI: 1ページ（脆弱性一覧表示）
- 認証: 不要（公開ページ）

### Phase 5以降で実装
- 本格的なダッシュボード（React + MUI v6）
- 高度なフィルタリング、グラフ・統計表示
- CPEマッチング結果の可視化

---

## 8. 統合ページ管理表

| ID | ページ名 | ルート | 権限レベル | 統合機能 | 着手 | 完了 |
|----|---------|-------|----------|---------|------|------|
| P-001 | 脆弱性一覧ページ | `/` | 公開 | 脆弱性一覧表示、検索（CVE ID+タイトル）、詳細表示（モーダル）、ページネーション、ソート機能 | [x] | [x] |

**注記**: Phase 1はMVPルートのため1ページのみ。Phase 2以降で詳細ページや高度な機能を追加予定。
