import { AlertTriangle } from 'lucide-react';
import type { AssetRankingItem } from '../../types';

interface AssetRankingWidgetProps {
  ranking: AssetRankingItem[];
}

export function AssetRankingWidget({ ranking }: AssetRankingWidgetProps) {
  return (
    <div className="bg-surface-0 border border-surface-1 rounded-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle size={20} className="text-yellow" />
        <h3 className="text-lg font-semibold text-text">脆弱性が多い資産 TOP10</h3>
      </div>

      {ranking.length === 0 ? (
        <div className="py-8 text-center text-subtext-0">データがありません</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-1">
                <th className="text-left py-3 px-2 text-subtext-0 font-medium">順位</th>
                <th className="text-left py-3 px-2 text-subtext-0 font-medium">資産名</th>
                <th className="text-right py-3 px-2 text-subtext-0 font-medium">総数</th>
                <th className="text-right py-3 px-2 text-subtext-0 font-medium">Critical</th>
                <th className="text-right py-3 px-2 text-subtext-0 font-medium">High</th>
              </tr>
            </thead>
            <tbody>
              {ranking.map((item, index) => (
                <tr key={item.asset_id} className="border-b border-surface-1 hover:bg-surface-1/50">
                  <td className="py-3 px-2 text-text font-semibold">{index + 1}</td>
                  <td className="py-3 px-2 text-text truncate max-w-[200px]" title={item.asset_name}>
                    {item.asset_name}
                  </td>
                  <td className="py-3 px-2 text-right text-text font-semibold">
                    {item.vulnerability_count.toLocaleString()}
                  </td>
                  <td className="py-3 px-2 text-right">
                    {item.critical_count > 0 ? (
                      <span className="text-red font-semibold">{item.critical_count}</span>
                    ) : (
                      <span className="text-subtext-0">0</span>
                    )}
                  </td>
                  <td className="py-3 px-2 text-right">
                    {item.high_count > 0 ? (
                      <span className="text-peach font-semibold">{item.high_count}</span>
                    ) : (
                      <span className="text-subtext-0">0</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
