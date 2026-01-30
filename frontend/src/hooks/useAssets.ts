import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, post, put, del, uploadFile } from '../lib/api';
import type {
  Asset,
  AssetListResponse,
  AssetCreateInput,
  AssetUpdateInput,
  FileImportResponse,
} from '../types';

/**
 * 資産一覧を取得するカスタムフック
 */
export function useAssets(params: {
  page?: number;
  limit?: number;
  source?: string;
}) {
  return useQuery({
    queryKey: ['assets', params],
    queryFn: () =>
      get<AssetListResponse>('/api/assets', {
        page: params.page || 1,
        limit: params.limit || 50,
        source: params.source || '',
      }),
  });
}

/**
 * 資産詳細を取得するカスタムフック
 */
export function useAssetDetail(assetId: string | null) {
  return useQuery({
    queryKey: ['asset', assetId],
    queryFn: () => get<Asset>(`/api/assets/${assetId}`),
    enabled: !!assetId,
  });
}

/**
 * 資産を新規登録するカスタムフック
 */
export function useCreateAsset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AssetCreateInput) => post<Asset>('/api/assets', data),
    onSuccess: () => {
      // キャッシュを無効化して再取得
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
  });
}

/**
 * 資産を更新するカスタムフック
 */
export function useUpdateAsset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ assetId, data }: { assetId: string; data: AssetUpdateInput }) =>
      put<Asset>(`/api/assets/${assetId}`, data),
    onSuccess: () => {
      // キャッシュを無効化して再取得
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      queryClient.invalidateQueries({ queryKey: ['asset'] });
    },
  });
}

/**
 * 資産を削除するカスタムフック
 */
export function useDeleteAsset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (assetId: string) => del(`/api/assets/${assetId}`),
    onSuccess: () => {
      // キャッシュを無効化して再取得
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
  });
}

/**
 * ファイルをアップロードして一括登録するカスタムフック
 */
export function useFileImport(type: 'composer' | 'npm' | 'docker') {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => {
      return uploadFile<FileImportResponse>(`/api/assets/import/${type}`, file);
    },
    onSuccess: () => {
      // キャッシュを無効化して再取得
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
  });
}
