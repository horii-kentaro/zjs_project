import { useState } from 'react';
import { Loader2, RefreshCw } from 'lucide-react';
import {
  useDashboardSummary,
  useDashboardTrend,
  useSeverityDistribution,
  useAssetRanking,
  useCriticalHighVulnerabilities,
} from '../hooks/useDashboard';
import { SummaryCard } from '../components/widgets/SummaryCard';
import { TrendChart } from '../components/widgets/TrendChart';
import { SeverityPieChart } from '../components/widgets/SeverityPieChart';
import { AssetRankingWidget } from '../components/widgets/AssetRankingWidget';
import { VulnerabilityTable } from '../components/VulnerabilityTable';
import { VulnerabilityDetailModal } from '../components/VulnerabilityDetailModal';
import { Button } from '../components/ui/Button';

export function DashboardPage() {
  const [selectedCveId, setSelectedCveId] = useState<string | null>(null);

  // データ取得
  const summaryQuery = useDashboardSummary();
  const trendQuery = useDashboardTrend(30);
  const distributionQuery = useSeverityDistribution();
  const rankingQuery = useAssetRanking();
  const vulnerabilitiesQuery = useCriticalHighVulnerabilities();

  // ローディング状態
  const isLoading =
    summaryQuery.isLoading ||
    trendQuery.isLoading ||
    distributionQuery.isLoading ||
    rankingQuery.isLoading ||
    vulnerabilitiesQuery.isLoading;

  // エラー状態
  const hasError =
    summaryQuery.isError ||
    trendQuery.isError ||
    distributionQuery.isError ||
    rankingQuery.isError ||
    vulnerabilitiesQuery.isError;

  // 全データをリフレッシュ
  const handleRefresh = () => {
    summaryQuery.refetch();
    trendQuery.refetch();
    distributionQuery.refetch();
    rankingQuery.refetch();
    vulnerabilitiesQuery.refetch();
  };

  // ダミーソート処理（ダッシュボードでは使用しない）
  const handleSort = () => {
    // ダッシュボードではソート不要
  };

  return (
    <div className="min-h-screen bg-base p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* ヘッダー */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-text">ダッシュボード</h1>
          <Button variant="secondary" onClick={handleRefresh} disabled={isLoading}>
            <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
            更新
          </Button>
        </div>

        {/* 全体ローディング */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="animate-spin text-blue" size={40} />
          </div>
        )}

        {/* 全体エラー */}
        {hasError && !isLoading && (
          <div className="bg-red/20 border border-red/30 rounded-lg p-6 text-center">
            <p className="text-red">データの取得に失敗しました。再読み込みしてください。</p>
          </div>
        )}

        {/* ダッシュボードコンテンツ */}
        {!isLoading && !hasError && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* サマリーカード（4枚） */}
            {summaryQuery.data && (
              <>
                <SummaryCard
                  severity="Critical"
                  count={summaryQuery.data.severityCounts.critical}
                  prevCount={summaryQuery.data.prevSeverityCounts.critical}
                  color="red"
                />
                <SummaryCard
                  severity="High"
                  count={summaryQuery.data.severityCounts.high}
                  prevCount={summaryQuery.data.prevSeverityCounts.high}
                  color="peach"
                />
                <SummaryCard
                  severity="Medium"
                  count={summaryQuery.data.severityCounts.medium}
                  prevCount={summaryQuery.data.prevSeverityCounts.medium}
                  color="blue"
                />
                <SummaryCard
                  severity="Low"
                  count={summaryQuery.data.severityCounts.low}
                  prevCount={summaryQuery.data.prevSeverityCounts.low}
                  color="green"
                />
              </>
            )}

            {/* トレンドチャート（2カラム） */}
            {trendQuery.data?.dataPoints && (
              <div className="col-span-1 md:col-span-2">
                <TrendChart dataPoints={trendQuery.data.dataPoints} />
              </div>
            )}

            {/* 重要度分布（2カラム） */}
            {distributionQuery.data && (
              <div className="col-span-1 md:col-span-2">
                <SeverityPieChart distribution={distributionQuery.data} />
              </div>
            )}

            {/* 資産ランキング（2カラム） */}
            {rankingQuery.data?.ranking && (
              <div className="col-span-1 md:col-span-2">
                <AssetRankingWidget ranking={rankingQuery.data.ranking} />
              </div>
            )}

            {/* 脆弱性一覧（4カラム・フルワイド） */}
            {vulnerabilitiesQuery.data?.vulnerabilities && (
              <div className="col-span-1 md:col-span-2 lg:col-span-4">
                <div className="bg-surface-0 border border-surface-1 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-text mb-4">
                    Critical/High脆弱性 TOP10
                  </h3>
                  {vulnerabilitiesQuery.data.vulnerabilities.length === 0 ? (
                    <div className="py-8 text-center text-subtext-0">
                      Critical/High脆弱性はありません
                    </div>
                  ) : (
                    <VulnerabilityTable
                      vulnerabilities={vulnerabilitiesQuery.data.vulnerabilities}
                      sortBy="cvss_score"
                      sortOrder="desc"
                      onSort={handleSort}
                      onViewDetail={setSelectedCveId}
                    />
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 詳細モーダル */}
      <VulnerabilityDetailModal cveId={selectedCveId} onClose={() => setSelectedCveId(null)} />
    </div>
  );
}
