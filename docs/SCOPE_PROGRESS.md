# 脆弱性管理システム 開発進捗状況

## 1. 基本情報

- **プロジェクト名**: 脆弱性管理システム（Phase 1: 脆弱性情報取得基盤）
- **ステータス**: Phase 4 完了 → Phase 5 バックエンドAPI実装へ
- **完了フェーズ**: Phase 1（要件定義）、Phase 2（Git/GitHub）、Phase 3（スキップ）、Phase 4（ページ実装）
- **進捗率**: Phase 4まで完了（4/10フェーズ、40%）
- **次のマイルストーン**: Phase 5 バックエンドAPI実装（JVN iPedia API統合 + PostgreSQL）
- **最終更新日**: 2026-01-08

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

### Phase 5: 環境構築（次のフェーズ）

**実装予定内容**:
- [ ] PostgreSQL（Neon）セットアップ
  - Neonアカウント作成
  - データベース作成
  - 接続文字列取得と.env設定
- [ ] データベース初期化
  - Alembicマイグレーション設定
  - テーブル作成（Vulnerabilityテーブル）
  - 接続確認
- [ ] 環境変数の最終確認
  - DATABASE_URL設定
  - JVN_API_ENDPOINT設定

### Phase 6以降（予定）

- [ ] Phase 6: バックエンド計画（JVN iPedia API統合設計）
- [ ] Phase 7: バックエンドAPI実装
- [ ] Phase 8: テスト実装（pytest + カバレッジ80%以上）
- [ ] Phase 9: CI/CD構築（GitHub Actions定期実行）
- [ ] Phase 10: Docker環境構築
- [ ] Phase 11: ドキュメント整備
- [ ] Phase 12: リリース準備

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
- ✅ JVN iPedia API統合
- ✅ PostgreSQL永続化（SQLAlchemy）
- ✅ 差分取得ロジック
- ✅ リトライ処理（3回）
- ✅ エラーハンドリング・詳細ログ
- ✅ 簡易Web UI（FastAPI）
- ✅ GitHub Actions定期実行
- ✅ Docker Compose環境
- ✅ pytest + カバレッジ80%以上
- ✅ README・セットアップ手順

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
