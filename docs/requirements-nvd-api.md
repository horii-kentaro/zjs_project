# NVD API 2.0 統合要件定義（簡易版）

**作成日**: 2026-01-31
**ステータス**: 実装中
**優先度**: 高（OSSパッケージのマッチング機能に必須）

---

## 1. 目的

JVN iPedia APIだけではカバレッジが不足しているOSSパッケージ（NPM、Composer、Docker等）の脆弱性情報を、NVD（National Vulnerability Database）から取得し、既存のマッチング機能を強化する。

## 2. 背景

### 現状の問題
- JVN iPedia APIは主に日本国内で影響のある脆弱性が中心
- NPM/Composerパッケージ（lodash、jquery、symfony、guzzle等）の脆弱性情報がほとんどない
- アップロードした資産ファイル（composer.json、package.json、Dockerfile）とのマッチングがほぼ0件

### 解決策
- NVD API 2.0を統合し、全世界の脆弱性情報を取得
- 既存のVulnerabilityモデルに保存（データソースフラグで識別）
- マッチングロジックは変更不要（CPE形式は共通）

---

## 3. NVD API 2.0 仕様

### 基本情報
- **エンドポイント**: `https://services.nvd.nist.gov/rest/json/cves/2.0`
- **認証**: APIキー推奨（無料取得、50req/30s）
- **レート制限**:
  - APIキーなし: 5req/30s（6秒/リクエスト）
  - APIキーあり: 50req/30s（0.6秒/リクエスト）
- **データ形式**: JSON
- **最大取得件数**: 2,000件/リクエスト
- **タイムアウト**: 30秒
- **リトライ**: 最大3回（指数バックオフ）

### 差分取得
- パラメータ: `lastModStartDate`、`lastModEndDate`
- 形式: ISO 8601（例: 2024-01-01T00:00:00.000）
- 日付範囲制限: **最大120日間**（重要）
- エンリッチメント遅延: APIからの取得が完全でない場合あり

### ページネーション
- パラメータ: `startIndex`（0ベース）
- 1リクエストで最大2,000件まで取得可能
- `totalResults`で総件数を確認

---

## 4. データモデル設計

### 既存のVulnerabilityモデルを使用（変更なし）

**理由**:
- `affected_products`フィールドは既にJSON型で定義済み
- NVDのCPE情報も同じ構造で保存可能
- データソースは`references`フィールドで識別

### affected_products の保存形式（NVD API 2.0対応）

```json
{
  "cpe": [
    "cpe:2.3:a:lodash:lodash:4.17.11:*:*:*:*:node.js:*:*",
    "cpe:2.3:a:lodash:lodash:4.17.12:*:*:*:*:node.js:*:*"
  ],
  "version_ranges": {
    "lodash": {
      "versionStartIncluding": "4.0.0",
      "versionEndExcluding": "4.17.21"
    }
  }
}
```

### references の拡張（データソース識別）

```json
{
  "nvd": "https://nvd.nist.gov/vuln/detail/CVE-2020-8203",
  "jvn": "https://jvndb.jvn.jp/ja/contents/2020/JVNDB-2020-009463.html",
  "source": "nvd"  // または "jvn"、"both"（両方から取得した場合）
}
```

---

## 5. NVD Fetcher 実装仕様

### クラス設計

```python
class NVDFetcherService:
    """
    NVD API 2.0からの脆弱性情報取得サービス。

    JVNFetcherServiceと類似の構造で実装。
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: NVD APIキー（オプション、推奨）
        """
        self.api_endpoint = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.api_key = api_key or os.getenv("NVD_API_KEY")
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 5

        # レート制限（APIキーの有無で変更）
        if self.api_key:
            self.rate_limit_delay = 0.6  # 50req/30s
        else:
            self.rate_limit_delay = 6.0  # 5req/30s

    async def fetch_vulnerabilities(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> List[VulnerabilityCreate]:
        """
        NVD API 2.0から脆弱性情報を取得。

        Args:
            start_date: 開始日時（ISO 8601、例: 2024-01-01T00:00:00.000）
            end_date: 終了日時（ISO 8601、例: 2024-04-30T23:59:59.999）
            max_items: 最大取得件数（デフォルト: 制限なし）

        Returns:
            VulnerabilityCreateオブジェクトのリスト

        Raises:
            NVDAPIError: API呼び出しエラー
            NVDParseError: JSONパースエラー
        """
        pass

    def _parse_cve_item(self, cve_item: dict) -> VulnerabilityCreate:
        """
        NVD APIのCVEアイテムをVulnerabilityCreateに変換。

        Args:
            cve_item: NVD API 2.0のCVEアイテム（JSON）

        Returns:
            VulnerabilityCreateオブジェクト
        """
        pass

    def _extract_cpe_data(self, configurations: list) -> dict:
        """
        NVD APIのconfigurations配列からCPE情報を抽出。

        Args:
            configurations: NVD API 2.0のconfigurations配列

        Returns:
            affected_products形式の辞書
        """
        pass
```

### データ取得戦略

**初回取得**（過去3年分）:
- 日付範囲制限が120日間のため、複数回に分割して取得
- 例: 2023-01-01〜2023-04-30、2023-05-01〜2023-08-31、...
- 自動的にページネーションと日付分割を処理

**差分取得**（定期実行）:
- 前回の最終更新日時から現在までを取得
- 120日以内であれば1回のリクエストで完了

---

## 6. 統合処理フロー

### 脆弱性情報の取得順序

1. **JVN iPedia API** - 既存処理（優先）
   - 日本語情報、国内での影響度が高い脆弱性

2. **NVD API 2.0** - 新規追加（補完）
   - OSSパッケージ、海外の脆弱性情報
   - JVN iPediaで取得済みのCVE IDは**スキップ**（重複防止）

### データベース保存処理

```python
async def fetch_all_sources():
    """全データソースから脆弱性情報を取得・保存"""

    # 1. JVN iPedia APIから取得
    jvn_fetcher = JVNFetcherService()
    jvn_vulnerabilities = await jvn_fetcher.fetch_since_last_update()
    await save_vulnerabilities(jvn_vulnerabilities, source="jvn")

    # 2. NVD API 2.0から取得（JVNにない情報のみ）
    nvd_fetcher = NVDFetcherService()
    nvd_vulnerabilities = await nvd_fetcher.fetch_since_last_update()

    # 既にDBに存在するCVE IDをフィルタリング
    existing_cve_ids = get_existing_cve_ids()
    new_vulnerabilities = [
        v for v in nvd_vulnerabilities
        if v.cve_id not in existing_cve_ids
    ]

    await save_vulnerabilities(new_vulnerabilities, source="nvd")

    logger.info(f"Total fetched: JVN={len(jvn_vulnerabilities)}, NVD={len(new_vulnerabilities)}")
```

---

## 7. マッチングロジックの拡張

### 既存のマッチングロジックは変更不要

**理由**:
- NVD APIもCPE 2.3形式を使用
- `affected_products`の構造は統一済み
- `match_exact()`、`match_version_range()`、`match_wildcard()`はそのまま使用可能

### 確認すべき点
- NVD APIのCPE情報が正しく`affected_products`に保存されているか
- バージョン範囲情報（versionStartIncluding等）が正しく抽出されているか

---

## 8. APIエンドポイント（拡張不要）

既存のエンドポイントをそのまま使用:
- `POST /api/fetch-now` - JVN iPediaとNVD API 2.0の両方から取得
- `GET /api/vulnerabilities` - データソース問わず全脆弱性を表示
- `POST /api/matching/execute` - NVDデータも含めてマッチング実行

---

## 9. 環境変数

### 新規追加

```bash
# NVD API 2.0設定
NVD_API_KEY=your_api_key_here  # オプション、推奨（50req/30s）
NVD_API_ENDPOINT=https://services.nvd.nist.gov/rest/json/cves/2.0
NVD_API_TIMEOUT=30
NVD_API_MAX_RETRIES=3
NVD_API_RETRY_DELAY=5
```

### .env.exampleに追加

---

## 10. テスト要件

### 単体テスト
- NVDFetcherServiceのJSON解析テスト
- CPE抽出ロジックのテスト
- バージョン範囲抽出のテスト

### 統合テスト
- NVD API 2.0への実接続テスト（テストデータ取得）
- データベース保存のテスト
- JVN + NVD統合取得のテスト

### E2Eテスト
- ファイルアップロード → マッチング実行 → 結果表示
- lodash、jquery、symfony等のマッチング成功を確認

---

## 11. 実装スケジュール

### タスク1: NVD Fetcher実装（4時間）
- src/fetchers/nvd_fetcher.py作成
- JSON解析ロジック実装
- CPE抽出ロジック実装

### タスク2: データベース統合（2時間）
- 既存のsave_vulnerabilities()の拡張
- データソースフラグの追加
- 重複チェックロジック

### タスク3: 統合処理実装（2時間）
- scripts/fetch_vulnerabilities.py拡張
- JVN + NVD統合取得処理

### タスク4: テスト実装（2時間）
- 単体テスト
- 統合テスト
- E2Eテスト

### タスク5: 動作確認（1時間）
- 実データ取得テスト
- マッチング結果確認

**合計推定工数**: 11時間

---

## 12. 成功指標

### 定量的指標
- NVD APIからの取得成功率: 99%以上
- lodash、jquery、symfony等のマッチング成功: 90%以上
- データベースレコード増加数: +10,000件以上（過去3年分のNVDデータ）

### 定性的指標
- ファイルアップロード機能のマッチング率向上
- OSSパッケージの脆弱性検出精度向上

---

## 13. 制約事項

### NVD API 2.0の制約
- 日付範囲: 最大120日間（過去3年分は分割取得が必要）
- レート制限: APIキーなしは5req/30s（取得に時間がかかる）
- エンリッチメント遅延: 最新CVEの詳細情報が不完全な場合あり

### データベースへの影響
- レコード数が大幅に増加（+10,000〜50,000件）
- インデックスの効率を確認
- ストレージ容量の確認（Neon無料枠内か）

---

**要件定義書 作成日**: 2026-01-31
**作成者**: 機能拡張オーケストレーター
