import { Badge } from './ui/Badge';
import type { MatchingResult } from '../types';

interface MatchingTableProps {
  results: MatchingResult[];
}

export function MatchingTable({ results }: MatchingTableProps) {
  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ja-JP');
  };

  const getMatchReasonLabel = (reason: 'exact_match' | 'version_range' | 'wildcard_match') => {
    const labels = {
      exact_match: '完全一致',
      version_range: 'バージョン範囲',
      wildcard_match: 'ワイルドカード',
    };
    return labels[reason] || reason;
  };

  const getSeverityVariant = (severity: string | undefined): 'critical' | 'high' | 'medium' | 'low' | 'default' => {
    if (!severity) return 'default';
    const lower = severity.toLowerCase();
    if (lower === 'critical' || lower === 'high' || lower === 'medium' || lower === 'low') {
      return lower as 'critical' | 'high' | 'medium' | 'low';
    }
    return 'default';
  };

  if (results.length === 0) {
    return (
      <div className="rounded-lg bg-surface-0 border border-surface-1 p-6 text-center text-subtext-0">
        マッチング結果がありません
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-surface-0 border border-surface-1 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-surface-1">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-subtext-0 uppercase tracking-wider">
                資産名
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-subtext-0 uppercase tracking-wider">
                CVE ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-subtext-0 uppercase tracking-wider">
                タイトル
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-subtext-0 uppercase tracking-wider">
                重要度
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-subtext-0 uppercase tracking-wider">
                CVSS
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-subtext-0 uppercase tracking-wider">
                マッチング理由
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-subtext-0 uppercase tracking-wider">
                マッチング日時
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-1">
            {results.map((result) => (
              <tr key={result.match_id} className="hover:bg-surface-1/50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-text">
                  {result.asset_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className="font-mono text-blue">{result.cve_id}</span>
                </td>
                <td className="px-6 py-4 text-sm text-text max-w-md truncate">
                  {result.vulnerability_title}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <Badge variant={getSeverityVariant(result.severity)}>
                    {result.severity || '-'}
                  </Badge>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-text">
                  {result.cvss_score !== undefined && result.cvss_score !== null
                    ? result.cvss_score.toFixed(1)
                    : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-text">
                  {getMatchReasonLabel(result.match_reason)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-subtext-0">
                  {formatDateTime(result.matched_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
