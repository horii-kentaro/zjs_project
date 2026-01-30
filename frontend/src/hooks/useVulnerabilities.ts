import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, post } from '../lib/api';
import type {
  Vulnerability,
  VulnerabilityListResponse,
} from '../types';

/**
 * 脆弱性一覧を取得するカスタムフック
 */
export function useVulnerabilities(params: {
  page?: number;
  limit?: number;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}) {
  return useQuery({
    queryKey: ['vulnerabilities', params],
    queryFn: () =>
      get<VulnerabilityListResponse>('/api/vulnerabilities', {
        page: params.page || 1,
        limit: params.limit || 50,
        search: params.search || '',
        sort_by: params.sort_by || 'modified_date',
        sort_order: params.sort_order || 'desc',
      }),
  });
}

/**
 * 脆弱性詳細を取得するカスタムフック
 */
export function useVulnerabilityDetail(cveId: string | null) {
  return useQuery({
    queryKey: ['vulnerability', cveId],
    queryFn: () => get<Vulnerability>(`/api/vulnerabilities/${cveId}`),
    enabled: !!cveId,
  });
}

/**
 * JVN iPedia APIからリアルタイム取得
 */
export function useFetchNow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => post<{ success: boolean; fetched: number; errors: number }>('/api/fetch-now'),
    onSuccess: () => {
      // キャッシュを無効化して再取得
      queryClient.invalidateQueries({ queryKey: ['vulnerabilities'] });
    },
  });
}
