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
  page_size: number;
  total_pages: number;
  items: Vulnerability[];
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
  items: Asset[];
}

export interface AssetCreateInput {
  asset_name: string;
  vendor: string;
  product: string;
  version: string;
}

export interface AssetUpdateInput extends Partial<AssetCreateInput> {}

export interface FileImportResponse {
  imported_count: number;
  skipped_count: number;
  errors: string[];
}

// ========================================
// マッチング関連の型定義
// ========================================

export interface MatchingResult {
  match_id: string;
  asset_id: string;
  asset_name: string;
  cve_id: string;
  vulnerability_title: string;
  severity?: 'Critical' | 'High' | 'Medium' | 'Low';
  cvss_score?: number;
  match_reason: 'exact_match' | 'version_range' | 'wildcard_match';
  matched_at: string;
}

export interface MatchingResultListResponse {
  total: number;
  page: number;
  limit: number;
  items: MatchingResult[];
}

export interface MatchingExecutionResponse {
  total_assets: number;
  total_vulnerabilities: number;
  total_matches: number;
  exact_matches: number;
  version_range_matches: number;
  wildcard_matches: number;
  execution_time_seconds?: number;
}

export interface MatchingDashboardResponse {
  affected_assets_count: number;
  total_matches: number;
  critical_vulnerabilities: number;
  high_vulnerabilities: number;
  medium_vulnerabilities: number;
  low_vulnerabilities: number;
  last_matching_at: string | null;
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
