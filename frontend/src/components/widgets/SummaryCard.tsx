import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

interface SummaryCardProps {
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  count: number;
  prevCount: number;
  color: string;
}

export function SummaryCard({ severity, count, prevCount }: SummaryCardProps) {
  const diff = count - prevCount;
  const diffAbsolute = Math.abs(diff);
  const hasChange = diff !== 0;

  // 色のマッピング（Catppuccin Mocha）
  const colorClasses = {
    Critical: { bg: 'bg-red/20', border: 'border-red/30', text: 'text-red' },
    High: { bg: 'bg-peach/20', border: 'border-peach/30', text: 'text-peach' },
    Medium: { bg: 'bg-blue/20', border: 'border-blue/30', text: 'text-blue' },
    Low: { bg: 'bg-green/20', border: 'border-green/30', text: 'text-green' },
  }[severity];

  return (
    <div className={`${colorClasses.bg} ${colorClasses.border} border rounded-lg p-6`}>
      {/* Severity Label */}
      <div className="flex items-center justify-between mb-4">
        <h3 className={`text-lg font-semibold ${colorClasses.text}`}>{severity}</h3>
      </div>

      {/* Count */}
      <div className={`text-4xl font-bold ${colorClasses.text} mb-2`}>
        {count.toLocaleString()}
      </div>

      {/* Previous Week Comparison */}
      <div className="flex items-center gap-2 text-sm text-subtext-0">
        {hasChange ? (
          <>
            {diff > 0 ? (
              <ArrowUp size={16} className="text-red" />
            ) : (
              <ArrowDown size={16} className="text-green" />
            )}
            <span className={diff > 0 ? 'text-red' : 'text-green'}>
              {diffAbsolute}件
            </span>
            <span>前週比</span>
          </>
        ) : (
          <>
            <Minus size={16} />
            <span>前週から変化なし</span>
          </>
        )}
      </div>
    </div>
  );
}
