import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { X } from 'lucide-react';
import { Button } from './ui/Button';
import type { Asset, AssetCreateInput } from '../types';

// バリデーションスキーマ
const assetSchema = z.object({
  asset_name: z.string().min(1, '資産名を入力してください').max(200, '資産名は200文字以内で入力してください'),
  vendor: z.string().min(1, 'ベンダーを入力してください').max(100, 'ベンダーは100文字以内で入力してください'),
  product: z.string().min(1, '製品名を入力してください').max(100, '製品名は100文字以内で入力してください'),
  version: z.string().min(1, 'バージョンを入力してください').max(50, 'バージョンは50文字以内で入力してください'),
});

type AssetFormData = z.infer<typeof assetSchema>;

interface AssetFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: AssetCreateInput) => Promise<void>;
  asset?: Asset | null;
  isSubmitting?: boolean;
}

export function AssetFormModal({ isOpen, onClose, onSubmit, asset, isSubmitting }: AssetFormModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<AssetFormData>({
    resolver: zodResolver(assetSchema),
  });

  // モーダルが開かれたとき、編集モードなら既存データを設定
  useEffect(() => {
    if (isOpen && asset) {
      reset({
        asset_name: asset.asset_name,
        vendor: asset.vendor,
        product: asset.product,
        version: asset.version,
      });
    } else if (isOpen && !asset) {
      reset({
        asset_name: '',
        vendor: '',
        product: '',
        version: '',
      });
    }
  }, [isOpen, asset, reset]);

  const handleFormSubmit = async (data: AssetFormData) => {
    await onSubmit(data);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-crust/80 backdrop-blur-sm">
      <div className="bg-base border border-surface-1 rounded-lg shadow-lg w-full max-w-md">
        {/* ヘッダー */}
        <div className="flex items-center justify-between p-4 border-b border-surface-1">
          <h2 className="text-xl font-bold text-text">
            {asset ? '資産の編集' : '資産の新規登録'}
          </h2>
          <button
            onClick={onClose}
            className="text-subtext-0 hover:text-text transition-colors"
            disabled={isSubmitting}
          >
            <X size={24} />
          </button>
        </div>

        {/* フォーム */}
        <form onSubmit={handleSubmit(handleFormSubmit)} className="p-4 space-y-4">
          {/* 資産名 */}
          <div>
            <label className="block text-sm font-medium text-text mb-1">
              資産名 <span className="text-red">*</span>
            </label>
            <input
              type="text"
              {...register('asset_name')}
              className="w-full px-3 py-2 bg-surface-0 border border-surface-1 rounded-lg text-text placeholder:text-subtext-0 focus:outline-none focus:ring-2 focus:ring-blue"
              placeholder="例: Laravel Application"
              disabled={isSubmitting}
            />
            {errors.asset_name && (
              <p className="mt-1 text-sm text-red">{errors.asset_name.message}</p>
            )}
          </div>

          {/* ベンダー */}
          <div>
            <label className="block text-sm font-medium text-text mb-1">
              ベンダー <span className="text-red">*</span>
              {asset && <span className="ml-2 text-xs text-subtext-0">(編集不可)</span>}
            </label>
            <input
              type="text"
              {...register('vendor')}
              className={`w-full px-3 py-2 border border-surface-1 rounded-lg text-text placeholder:text-subtext-0 focus:outline-none focus:ring-2 focus:ring-blue ${
                asset ? 'bg-surface-1 opacity-60 cursor-not-allowed' : 'bg-surface-0'
              }`}
              placeholder="例: laravel"
              disabled={isSubmitting || !!asset}
            />
            {errors.vendor && (
              <p className="mt-1 text-sm text-red">{errors.vendor.message}</p>
            )}
          </div>

          {/* 製品名 */}
          <div>
            <label className="block text-sm font-medium text-text mb-1">
              製品名 <span className="text-red">*</span>
              {asset && <span className="ml-2 text-xs text-subtext-0">(編集不可)</span>}
            </label>
            <input
              type="text"
              {...register('product')}
              className={`w-full px-3 py-2 border border-surface-1 rounded-lg text-text placeholder:text-subtext-0 focus:outline-none focus:ring-2 focus:ring-blue ${
                asset ? 'bg-surface-1 opacity-60 cursor-not-allowed' : 'bg-surface-0'
              }`}
              placeholder="例: laravel"
              disabled={isSubmitting || !!asset}
            />
            {errors.product && (
              <p className="mt-1 text-sm text-red">{errors.product.message}</p>
            )}
          </div>

          {/* バージョン */}
          <div>
            <label className="block text-sm font-medium text-text mb-1">
              バージョン <span className="text-red">*</span>
            </label>
            <input
              type="text"
              {...register('version')}
              className="w-full px-3 py-2 bg-surface-0 border border-surface-1 rounded-lg text-text placeholder:text-subtext-0 focus:outline-none focus:ring-2 focus:ring-blue"
              placeholder="例: 9.52.16"
              disabled={isSubmitting}
            />
            {errors.version && (
              <p className="mt-1 text-sm text-red">{errors.version.message}</p>
            )}
          </div>

          {/* アクションボタン */}
          <div className="flex gap-2 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              className="flex-1"
              disabled={isSubmitting}
            >
              キャンセル
            </Button>
            <Button
              type="submit"
              variant="primary"
              className="flex-1"
              isLoading={isSubmitting}
              disabled={isSubmitting}
            >
              {asset ? '更新' : '登録'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
