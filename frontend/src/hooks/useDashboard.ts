import { useQuery } from '@tanstack/react-query';
import { get } from '../lib/api';
import type {
  DashboardSummary,
  TrendData,
  SeverityDistribution,
  AssetRankingResponse,
  VulnerabilityListResponse,
} from '../types';

/**
 * ダッシュボードサマリーデータを取得するカスタムフック
 */
export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => get<DashboardSummary>('/api/dashboard/summary'),
  });
}

/**
 * トレンドデータを取得するカスタムフック
 */
export function useDashboardTrend(days: number = 30) {
  return useQuery({
    queryKey: ['dashboard', 'trend', days],
    queryFn: () => get<TrendData>('/api/dashboard/trend', { days }),
  });
}

/**
 * 重要度分布を取得するカスタムフック
 */
export function useSeverityDistribution() {
  return useQuery({
    queryKey: ['dashboard', 'severity-distribution'],
    queryFn: () => get<SeverityDistribution>('/api/dashboard/severity-distribution'),
  });
}

/**
 * 資産ランキングを取得するカスタムフック
 */
export function useAssetRanking() {
  return useQuery({
    queryKey: ['dashboard', 'asset-ranking'],
    queryFn: () => get<AssetRankingResponse>('/api/dashboard/asset-ranking'),
  });
}

/**
 * Critical/High脆弱性TOP10を取得するカスタムフック
 */
export function useCriticalHighVulnerabilities() {
  return useQuery({
    queryKey: ['dashboard', 'critical-high-vulnerabilities'],
    queryFn: () =>
      get<VulnerabilityListResponse>('/api/vulnerabilities', {
        page: 1,
        limit: 10,
        severity: 'Critical,High',
        sort_by: 'cvss_score',
        sort_order: 'desc',
      }),
  });
}
