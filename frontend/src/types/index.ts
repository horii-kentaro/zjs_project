// ========================================
// 脆弱性関連の型定義
// ========================================

export interface Vulnerability {
  cve_id: string;
  jvn_id?: string;
  title: string;
  description?: string;
  severity?: 'Critical' | 'High' | 'Medium' | 'Low';
  cvss_score?: number;
  published_date: string;
  modified_date: string;
  affected_products?: Record<string, any>;
  vendor_info?: Record<string, any>;
  references?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface VulnerabilityListResponse {
  total: number;
  page: number;
  limit: number;
  vulnerabilities: Vulnerability[];
}

// ========================================
// 資産関連の型定義
// ========================================

export interface Asset {
  asset_id: string;
  asset_name: string;
  vendor: string;
  product: string;
  version: string;
  cpe_code: string;
  source: 'manual' | 'composer' | 'npm' | 'docker';
  created_at: string;
  updated_at: string;
}

export interface AssetListResponse {
  total: number;
  page: number;
  limit: number;
  assets: Asset[];
}

export interface AssetCreateInput {
  asset_name: string;
  vendor: string;
  product: string;
  version: string;
}

export interface AssetUpdateInput extends Partial<AssetCreateInput> {}

export interface FileImportResponse {
  success: boolean;
  inserted: number;
  skipped: number;
  errors: string[];
}

// ========================================
// マッチング関連の型定義
// ========================================

export interface MatchingResult {
  match_id: string;
  asset_id: string;
  cve_id: string;
  match_reason: 'exact_match' | 'version_range' | 'wildcard_match';
  matched_at: string;
  // 結合データ
  asset?: Asset;
  vulnerability?: Vulnerability;
}

export interface MatchingResultListResponse {
  total: number;
  page: number;
  limit: number;
  results: MatchingResult[];
}

export interface MatchingExecutionResponse {
  success: boolean;
  total_matches: number;
  exact_matches: number;
  version_range_matches: number;
  wildcard_matches: number;
  execution_time: number;
}

export interface DashboardResponse {
  total_assets: number;
  critical_vulnerabilities: number;
  high_vulnerabilities: number;
  latest_matching_date: string | null;
}

// ========================================
// ダッシュボード関連の型定義
// ========================================

export interface DashboardSummary {
  severityCounts: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  prevSeverityCounts: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  statusCounts?: {
    open: number;
    in_progress: number;
    resolved: number;
  };
}

export interface TrendDataPoint {
  date: string; // YYYY-MM-DD
  detected: number;
  resolved?: number;
}

export interface TrendData {
  dataPoints: TrendDataPoint[];
}

export interface SeverityDistribution {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface AssetRankingItem {
  asset_id: string;
  asset_name: string;
  vulnerability_count: number;
  critical_count: number;
  high_count: number;
}

export interface AssetRankingResponse {
  ranking: AssetRankingItem[];
}

// ========================================
// ウィジェット関連の型定義
// ========================================

export type WidgetType =
  | 'summary'
  | 'trend_chart'
  | 'severity_pie'
  | 'vuln_list'
  | 'asset_ranking'
  | 'kev_alert'
  | 'activity_feed';

export type WidgetSize = 'small' | 'medium' | 'wide' | 'full';

export interface WidgetConfig {
  id: string;
  type: WidgetType;
  title: string;
  enabled: boolean;
  position: number;
  size: WidgetSize;
  settings?: Record<string, any>;
}

export interface DashboardConfig {
  widgets: WidgetConfig[];
  refreshInterval: number; // 秒
}

// ========================================
// APIレスポンスの共通型
// ========================================

export interface ApiError {
  detail: string;
  status?: number;
}

export interface HealthCheckResponse {
  status: string;
  database: string;
  timestamp: string;
}
