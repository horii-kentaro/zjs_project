import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import type { SeverityDistribution } from '../../types';

interface SeverityPieChartProps {
  distribution: SeverityDistribution;
}

// Catppuccin Mocha colors
const COLORS = {
  Critical: '#f38ba8',
  High: '#fab387',
  Medium: '#89b4fa',
  Low: '#a6e3a1',
};

export function SeverityPieChart({ distribution }: SeverityPieChartProps) {
  // データを配列に変換
  const data = [
    { name: 'Critical', value: distribution.critical },
    { name: 'High', value: distribution.high },
    { name: 'Medium', value: distribution.medium },
    { name: 'Low', value: distribution.low },
  ].filter((item) => item.value > 0); // 0件の項目は除外

  const total = distribution.critical + distribution.high + distribution.medium + distribution.low;

  return (
    <div className="bg-surface-0 border border-surface-1 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-text mb-4">重要度分布</h3>

      {total === 0 ? (
        <div className="h-[300px] flex items-center justify-center text-subtext-0">
          データがありません
        </div>
      ) : (
        <div className="flex flex-col items-center">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {data.map((entry) => (
                  <Cell
                    key={`cell-${entry.name}`}
                    fill={COLORS[entry.name as keyof typeof COLORS]}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#313244',
                  border: '1px solid #45475a',
                  borderRadius: '8px',
                  color: '#cdd6f4',
                }}
              />
              <Legend
                wrapperStyle={{ color: '#cdd6f4' }}
                iconType="circle"
              />
            </PieChart>
          </ResponsiveContainer>

          {/* Summary Stats */}
          <div className="mt-4 grid grid-cols-2 gap-4 w-full">
            {data.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-sm">
                <span className="text-subtext-0">{item.name}</span>
                <span className="font-semibold text-text">{item.value.toLocaleString()}件</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
