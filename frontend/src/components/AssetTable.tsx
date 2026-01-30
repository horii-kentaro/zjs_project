import { Edit, Trash2 } from 'lucide-react';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import type { Asset } from '../types';

interface AssetTableProps {
  assets: Asset[];
  onEdit: (assetId: string) => void;
  onDelete: (assetId: string, assetName: string) => void;
}

export function AssetTable({ assets, onEdit, onDelete }: AssetTableProps) {
  // 取得元バッジの色分け
  const getSourceVariant = (source: Asset['source']) => {
    const variants = {
      manual: 'low' as const,
      composer: 'medium' as const,
      npm: 'high' as const,
      docker: 'critical' as const,
    };
    return variants[source] || 'default' as const;
  };

  // 取得元ラベル
  const getSourceLabel = (source: Asset['source']) => {
    const labels = {
      manual: '手動',
      composer: 'Composer',
      npm: 'NPM',
      docker: 'Docker',
    };
    return labels[source] || source;
  };

  // 日付フォーマット
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP');
  };

  if (assets.length === 0) {
    return (
      <div className="bg-surface-0 border border-surface-1 rounded-lg p-12 text-center">
        <p className="text-subtext-0">資産が登録されていません</p>
      </div>
    );
  }

  return (
    <div className="bg-surface-0 border border-surface-1 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-surface-1">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-subtext-0">資産名</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-subtext-0">ベンダー</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-subtext-0">製品名</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-subtext-0">バージョン</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-subtext-0">CPEコード</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-subtext-0">取得元</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-subtext-0">登録日</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-subtext-0">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-1">
            {assets.map((asset) => (
              <tr key={asset.asset_id} className="hover:bg-surface-1/50 transition-colors">
                <td className="px-4 py-3 text-sm text-text">{asset.asset_name}</td>
                <td className="px-4 py-3 text-sm text-text">{asset.vendor}</td>
                <td className="px-4 py-3 text-sm text-text">{asset.product}</td>
                <td className="px-4 py-3 text-sm text-text">{asset.version}</td>
                <td className="px-4 py-3 text-xs text-subtext-0 font-mono">{asset.cpe_code}</td>
                <td className="px-4 py-3">
                  <Badge variant={getSourceVariant(asset.source)}>
                    {getSourceLabel(asset.source)}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-sm text-text">{formatDate(asset.created_at)}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => onEdit(asset.asset_id)}
                      title="編集"
                    >
                      <Edit size={14} />
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => onDelete(asset.asset_id, asset.asset_name)}
                      title="削除"
                    >
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
