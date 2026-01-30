import { useState } from 'react';
import { Plus, Package, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import {
  useAssets,
  useAssetDetail,
  useCreateAsset,
  useUpdateAsset,
  useDeleteAsset,
  useFileImport,
} from '../hooks/useAssets';
import { AssetTable } from '../components/AssetTable';
import { AssetFormModal } from '../components/AssetFormModal';
import { FileUploadModal } from '../components/FileUploadModal';
import { Button } from '../components/ui/Button';
import type { AssetCreateInput, AssetUpdateInput } from '../types';

export function AssetManagementPage() {
  // State管理
  const [currentPage, setCurrentPage] = useState(1);
  const [sourceFilter, setSourceFilter] = useState('');
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadType, setUploadType] = useState<'composer' | 'npm' | 'docker' | null>(null);
  const [editingAssetId, setEditingAssetId] = useState<string | null>(null);
  const [alertMessage, setAlertMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const limit = 50;

  // データ取得
  const { data, isLoading, error } = useAssets({
    page: currentPage,
    limit,
    source: sourceFilter,
  });

  const { data: editingAsset } = useAssetDetail(editingAssetId);

  // Mutations
  const createAssetMutation = useCreateAsset();
  const updateAssetMutation = useUpdateAsset();
  const deleteAssetMutation = useDeleteAsset();
  const fileImportMutation = useFileImport(uploadType || 'composer');

  // アラート表示
  const showAlert = (text: string, type: 'success' | 'error') => {
    setAlertMessage({ text, type });
    setTimeout(() => setAlertMessage(null), 5000);
  };

  // 新規登録モーダルを開く
  const openCreateModal = () => {
    setEditingAssetId(null);
    setIsFormModalOpen(true);
  };

  // 編集モーダルを開く
  const openEditModal = (assetId: string) => {
    setEditingAssetId(assetId);
    setIsFormModalOpen(true);
  };

  // アップロードモーダルを開く
  const openUploadModal = (type: 'composer' | 'npm' | 'docker') => {
    setUploadType(type);
    setIsUploadModalOpen(true);
  };

  // フォーム送信
  const handleFormSubmit = async (formData: AssetCreateInput | AssetUpdateInput) => {
    try {
      if (editingAssetId) {
        // 更新
        await updateAssetMutation.mutateAsync({
          assetId: editingAssetId,
          data: formData,
        });
        showAlert('資産を更新しました', 'success');
      } else {
        // 新規登録
        await createAssetMutation.mutateAsync(formData as AssetCreateInput);
        showAlert('資産を登録しました', 'success');
      }
      setIsFormModalOpen(false);
      setEditingAssetId(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '不明なエラー';
      showAlert(`保存に失敗しました: ${errorMessage}`, 'error');
    }
  };

  // 削除
  const handleDelete = async (assetId: string, assetName: string) => {
    if (!window.confirm(`「${assetName}」を削除しますか?\n関連するマッチング結果も削除されます。`)) {
      return;
    }

    try {
      await deleteAssetMutation.mutateAsync(assetId);
      showAlert('資産を削除しました', 'success');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '不明なエラー';
      showAlert(`削除に失敗しました: ${errorMessage}`, 'error');
    }
  };

  // ファイルアップロード
  const handleFileUpload = async (file: File) => {
    if (!uploadType) return { imported_count: 0, skipped_count: 0, errors: [] };

    const formData = new FormData();
    formData.append('file', file);

    // useFileImportはuploadTypeごとに異なるインスタンスなので、ここで直接APIコール
    const result = await fileImportMutation.mutateAsync(file);
    return result;
  };

  // フィルター変更
  const handleSourceFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSourceFilter(e.target.value);
    setCurrentPage(1);
  };

  // ページネーション
  const totalPages = data ? Math.ceil(data.total / limit) : 0;
  const canGoPrev = currentPage > 1;
  const canGoNext = currentPage < totalPages;

  const goToPrevPage = () => {
    if (canGoPrev) setCurrentPage(currentPage - 1);
  };

  const goToNextPage = () => {
    if (canGoNext) setCurrentPage(currentPage + 1);
  };

  return (
    <div className="min-h-screen bg-base p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* ヘッダー */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Package className="text-blue" size={32} />
            <h1 className="text-3xl font-bold text-text">資産管理</h1>
          </div>
        </div>

        {/* アクションボタン */}
        <div className="flex gap-3 flex-wrap">
          <Button variant="primary" onClick={openCreateModal}>
            <Plus size={16} />
            新規登録
          </Button>
          <Button variant="secondary" onClick={() => openUploadModal('composer')}>
            Composerアップロード
          </Button>
          <Button variant="secondary" onClick={() => openUploadModal('npm')}>
            NPMアップロード
          </Button>
          <Button variant="secondary" onClick={() => openUploadModal('docker')}>
            Dockerアップロード
          </Button>
        </div>

        {/* アラートメッセージ */}
        {alertMessage && (
          <div
            className={`rounded-lg p-4 ${
              alertMessage.type === 'success'
                ? 'bg-green/20 border border-green/30 text-green'
                : 'bg-red/20 border border-red/30 text-red'
            }`}
          >
            <p className="text-sm">{alertMessage.text}</p>
          </div>
        )}

        {/* フィルター */}
        <div className="flex gap-4 items-center">
          <label className="text-sm font-medium text-text">取得元:</label>
          <select
            value={sourceFilter}
            onChange={handleSourceFilterChange}
            className="px-3 py-2 bg-surface-0 border border-surface-1 rounded-lg text-text focus:outline-none focus:ring-2 focus:ring-blue"
          >
            <option value="">全て</option>
            <option value="manual">手動登録</option>
            <option value="composer">Composer</option>
            <option value="npm">NPM</option>
            <option value="docker">Docker</option>
          </select>
        </div>

        {/* 検索結果サマリー */}
        {data && (
          <div className="flex items-center justify-between text-sm text-subtext-0">
            <p>
              全{data.total.toLocaleString()}件中 {((currentPage - 1) * limit + 1).toLocaleString()}〜
              {Math.min(currentPage * limit, data.total).toLocaleString()}件を表示
            </p>
            <p>
              ページ {currentPage} / {totalPages}
            </p>
          </div>
        )}

        {/* ローディング状態 */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="animate-spin text-blue" size={40} />
          </div>
        )}

        {/* エラー状態 */}
        {error && (
          <div className="bg-red/20 border border-red/30 rounded-lg p-6 text-center">
            <p className="text-red">
              エラーが発生しました: {error instanceof Error ? error.message : '不明なエラー'}
            </p>
          </div>
        )}

        {/* テーブル */}
        {!isLoading && !error && data && (
          <AssetTable
            assets={data.items}
            onEdit={openEditModal}
            onDelete={handleDelete}
          />
        )}

        {/* ページネーション */}
        {!isLoading && !error && data && totalPages > 1 && (
          <div className="flex items-center justify-center gap-4">
            <Button
              variant="secondary"
              size="sm"
              onClick={goToPrevPage}
              disabled={!canGoPrev}
            >
              <ChevronLeft size={16} />
              前へ
            </Button>
            <span className="text-text">
              {currentPage} / {totalPages}
            </span>
            <Button
              variant="secondary"
              size="sm"
              onClick={goToNextPage}
              disabled={!canGoNext}
            >
              次へ
              <ChevronRight size={16} />
            </Button>
          </div>
        )}
      </div>

      {/* 新規登録・編集モーダル */}
      <AssetFormModal
        isOpen={isFormModalOpen}
        onClose={() => {
          setIsFormModalOpen(false);
          setEditingAssetId(null);
        }}
        onSubmit={handleFormSubmit}
        asset={editingAsset}
        isSubmitting={createAssetMutation.isPending || updateAssetMutation.isPending}
      />

      {/* ファイルアップロードモーダル */}
      <FileUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => {
          setIsUploadModalOpen(false);
          setUploadType(null);
        }}
        onUpload={handleFileUpload}
        uploadType={uploadType}
        isUploading={fileImportMutation.isPending}
      />
    </div>
  );
}
