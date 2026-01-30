import type { MatchingDashboardResponse } from '../types';

interface MatchingDashboardProps {
  data: MatchingDashboardResponse;
}

export function MatchingDashboard({ data }: MatchingDashboardProps) {
  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return '未実行';
    const date = new Date(dateString);
    return date.toLocaleString('ja-JP');
  };

  return (
    <div className="rounded-lg bg-surface-0 p-6 space-y-4">
      <h2 className="text-xl font-bold text-text">統計ダッシュボード</h2>

      {/* Statistics Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* 影響資産数 */}
        <div className="rounded-lg bg-surface-0 border border-surface-1 p-4">
          <div className="text-3xl font-bold text-text">{data.affected_assets_count}</div>
          <div className="text-sm text-subtext-0">影響資産数</div>
        </div>

        {/* Critical */}
        <div className="rounded-lg bg-red/20 border border-red p-4">
          <div className="text-3xl font-bold text-red">{data.critical_vulnerabilities}</div>
          <div className="text-sm text-subtext-0">Critical</div>
        </div>

        {/* High */}
        <div className="rounded-lg bg-peach/20 border border-peach p-4">
          <div className="text-3xl font-bold text-peach">{data.high_vulnerabilities}</div>
          <div className="text-sm text-subtext-0">High</div>
        </div>

        {/* Medium */}
        <div className="rounded-lg bg-blue/20 border border-blue p-4">
          <div className="text-3xl font-bold text-blue">{data.medium_vulnerabilities}</div>
          <div className="text-sm text-subtext-0">Medium</div>
        </div>

        {/* Low */}
        <div className="rounded-lg bg-green/20 border border-green p-4">
          <div className="text-3xl font-bold text-green">{data.low_vulnerabilities}</div>
          <div className="text-sm text-subtext-0">Low</div>
        </div>

        {/* 総マッチング数 */}
        <div className="rounded-lg bg-surface-0 border border-surface-1 p-4">
          <div className="text-3xl font-bold text-text">{data.total_matches}</div>
          <div className="text-sm text-subtext-0">総マッチング数</div>
        </div>
      </div>

      {/* 最終マッチング日時 */}
      <div className="text-sm text-subtext-0">
        最終マッチング: <span className="text-text">{formatDateTime(data.last_matching_at)}</span>
      </div>
    </div>
  );
}
