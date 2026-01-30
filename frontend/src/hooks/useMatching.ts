import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, post } from '../lib/api';
import type {
  MatchingResultListResponse,
  MatchingExecutionResponse,
  MatchingDashboardResponse,
} from '../types';

/**
 * マッチング結果一覧を取得するカスタムフック
 */
export function useMatchingResults(params: {
  page?: number;
  limit?: number;
  severity?: string;
  source?: string;
}) {
  return useQuery({
    queryKey: ['matching-results', params],
    queryFn: () =>
      get<MatchingResultListResponse>('/api/matching/results', {
        page: params.page || 1,
        limit: params.limit || 50,
        severity: params.severity || '',
        source: params.source || '',
      }),
  });
}

/**
 * マッチングダッシュボード統計を取得するカスタムフック
 */
export function useMatchingDashboard() {
  return useQuery({
    queryKey: ['matching-dashboard'],
    queryFn: () => get<MatchingDashboardResponse>('/api/matching/dashboard'),
  });
}

/**
 * マッチングを実行するカスタムフック
 */
export function useExecuteMatching() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => post<MatchingExecutionResponse>('/api/matching/execute'),
    onSuccess: () => {
      // マッチング実行後、ダッシュボードと結果を再取得
      queryClient.invalidateQueries({ queryKey: ['matching-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['matching-results'] });
    },
  });
}
