# 脆弱性管理システム 開発進捗状況

## 1. 基本情報

- **プロジェクト名**: 脆弱性管理システム（Phase 1: 脆弱性情報取得基盤）
- **ステータス**: Phase 1 要件定義中
- **完了タスク数**: 6/11
- **進捗率**: 55%
- **次のマイルストーン**: Phase 1 要件定義完了
- **最終更新日**: 2026-01-05

## 2. Phase 1 開発フロー

BlueLampでの開発は以下のフローに沿って進行します。

### Phase 1: 要件定義（進行中）

- [x] Step#1: 成果目標と成功指標の明確化
- [x] Step#2: 実現可能性調査（JVN iPedia API、NVD API、CISA KEV）
- [x] Step#2.5: 開発アプローチの選択（MVP or 通常版）→ MVPルート選択
- [x] Step#3: 認証・権限設計（スキップ - MVPルートのため不要）
- [x] Step#4: ページリストの作成（簡易UI設計）→ P-001: 脆弱性一覧ページ
- [x] Step#5: 技術スタック最終決定 → Python + FastAPI + PostgreSQL(Neon)
- [x] Step#6: 外部API最終決定 → JVN iPedia API（必須）、NVD/CISA KEV（推奨）
- [ ] Step#7: 要件定義書の書き出し（docs/requirements.md）
- [ ] Step#7.5: 品質基準設定（Lint設定ファイル生成）
- [ ] Step#8: SCOPE_PROGRESS更新（統合ページ管理表追加）
- [ ] Step#9: CLAUDE.md生成
- [ ] Step#10: ページの深掘り

### Phase 2以降（予定）

- Phase 2: Git/GitHub管理
- Phase 3: フロントエンド基盤
- Phase 4: ページ実装
- Phase 5: バックエンドAPI実装
- ...

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
