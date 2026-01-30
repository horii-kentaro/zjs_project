import { useState } from 'react';
import { Play, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import { useMatchingResults, useMatchingDashboard, useExecuteMatching } from '../hooks/useMatching';
import { MatchingDashboard } from '../components/MatchingDashboard';
import { MatchingTable } from '../components/MatchingTable';
import { Button } from '../components/ui/Button';

export function MatchingResultsPage() {
  // State管理
  const [currentPage, setCurrentPage] = useState(1);
  const [severityFilter, setSeverityFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const limit = 50;

  // データ取得
  const { data: dashboardData, isLoading: isDashboardLoading } = useMatchingDashboard();
  const {
    data: resultsData,
    isLoading: isResultsLoading,
    error: resultsError,
  } = useMatchingResults({
    page: currentPage,
    limit,
    severity: severityFilter,
    source: sourceFilter,
  });

  // マッチング実行
  const executeMatchingMutation = useExecuteMatching();

  // マッチング実行ボタン
  const handleExecuteMatching = async () => {
    try {
      await executeMatchingMutation.mutateAsync();
      setCurrentPage(1); // 実行後は1ページ目に戻る
    } catch (err) {
      console.error('マッチング実行エラー:', err);
    }
  };

  // フィルター変更
  const handleSeverityFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSeverityFilter(e.target.value);
    setCurrentPage(1);
  };

  const handleSourceFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSourceFilter(e.target.value);
    setCurrentPage(1);
  };

  // ページネーション
  const totalPages = resultsData ? Math.ceil(resultsData.total / limit) : 0;
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
          <h1 className="text-3xl font-bold text-text">マッチング結果</h1>
          <Button
            variant="primary"
            onClick={handleExecuteMatching}
            isLoading={executeMatchingMutation.isPending}
            disabled={executeMatchingMutation.isPending}
          >
            <Play size={16} />
            {executeMatchingMutation.isPending ? 'マッチング実行中...' : 'マッチング実行'}
          </Button>
        </div>

        {/* マッチング実行成功メッセージ */}
        {executeMatchingMutation.isSuccess && executeMatchingMutation.data && (
          <div className="bg-green/20 border border-green/30 rounded-lg p-4">
            <p className="text-green text-sm">
              ✓ マッチング完了: {executeMatchingMutation.data.total_matches}件のマッチング
              （完全一致: {executeMatchingMutation.data.exact_matches}、
              バージョン範囲: {executeMatchingMutation.data.version_range_matches}、
              ワイルドカード: {executeMatchingMutation.data.wildcard_matches}）
              {executeMatchingMutation.data.execution_time_seconds && (
                <span> | 実行時間: {executeMatchingMutation.data.execution_time_seconds.toFixed(2)}秒</span>
              )}
            </p>
          </div>
        )}

        {/* マッチング実行エラーメッセージ */}
        {executeMatchingMutation.isError && (
          <div className="bg-red/20 border border-red/30 rounded-lg p-4">
            <p className="text-red text-sm">
              ✗ マッチング実行エラー:{' '}
              {executeMatchingMutation.error instanceof Error
                ? executeMatchingMutation.error.message
                : '不明なエラー'}
            </p>
          </div>
        )}

        {/* ダッシュボード */}
        {isDashboardLoading && (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="animate-spin text-blue" size={40} />
          </div>
        )}

        {!isDashboardLoading && dashboardData && <MatchingDashboard data={dashboardData} />}

        {/* フィルター */}
        <div className="flex gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-text">重要度:</label>
            <select
              value={severityFilter}
              onChange={handleSeverityFilterChange}
              className="px-3 py-2 bg-surface-0 border border-surface-1 rounded-lg text-text focus:outline-none focus:ring-2 focus:ring-blue"
            >
              <option value="">全て</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-text">資産タイプ:</label>
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
        </div>

        {/* 検索結果サマリー */}
        {resultsData && (
          <div className="flex items-center justify-between text-sm text-subtext-0">
            <p>
              全{resultsData.total.toLocaleString()}件中{' '}
              {((currentPage - 1) * limit + 1).toLocaleString()}〜
              {Math.min(currentPage * limit, resultsData.total).toLocaleString()}件を表示
            </p>
            <p>
              ページ {currentPage} / {totalPages}
            </p>
          </div>
        )}

        {/* ローディング状態 */}
        {isResultsLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="animate-spin text-blue" size={40} />
          </div>
        )}

        {/* エラー状態 */}
        {resultsError && (
          <div className="bg-red/20 border border-red/30 rounded-lg p-6 text-center">
            <p className="text-red">
              エラーが発生しました:{' '}
              {resultsError instanceof Error ? resultsError.message : '不明なエラー'}
            </p>
          </div>
        )}

        {/* テーブル */}
        {!isResultsLoading && !resultsError && resultsData && (
          <MatchingTable results={resultsData.items} />
        )}

        {/* ページネーション */}
        {!isResultsLoading && !resultsError && resultsData && totalPages > 1 && (
          <div className="flex items-center justify-center gap-4">
            <Button variant="secondary" size="sm" onClick={goToPrevPage} disabled={!canGoPrev}>
              <ChevronLeft size={16} />
              前へ
            </Button>
            <span className="text-text">
              {currentPage} / {totalPages}
            </span>
            <Button variant="secondary" size="sm" onClick={goToNextPage} disabled={!canGoNext}>
              次へ
              <ChevronRight size={16} />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
