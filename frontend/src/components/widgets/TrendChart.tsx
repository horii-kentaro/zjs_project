import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { TrendDataPoint } from '../../types';

interface TrendChartProps {
  dataPoints: TrendDataPoint[];
}

export function TrendChart({ dataPoints }: TrendChartProps) {
  return (
    <div className="bg-surface-0 border border-surface-1 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-text mb-4">検出数推移（過去30日）</h3>

      {dataPoints.length === 0 ? (
        <div className="h-[300px] flex items-center justify-center text-subtext-0">
          データがありません
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={dataPoints}>
            <CartesianGrid strokeDasharray="3 3" stroke="#45475a" />
            <XAxis
              dataKey="date"
              stroke="#a6adc8"
              tick={{ fill: '#a6adc8' }}
              tickFormatter={(value) => {
                // YYYY-MM-DD → MM/DD
                const date = new Date(value);
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }}
            />
            <YAxis stroke="#a6adc8" tick={{ fill: '#a6adc8' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#313244',
                border: '1px solid #45475a',
                borderRadius: '8px',
                color: '#cdd6f4',
              }}
              labelStyle={{ color: '#cdd6f4' }}
            />
            <Legend
              wrapperStyle={{ color: '#cdd6f4' }}
              iconType="line"
            />
            <Line
              type="monotone"
              dataKey="detected"
              name="検出数"
              stroke="#89b4fa"
              strokeWidth={2}
              dot={{ fill: '#89b4fa', r: 4 }}
              activeDot={{ r: 6 }}
            />
            {dataPoints.some((d) => d.resolved !== undefined) && (
              <Line
                type="monotone"
                dataKey="resolved"
                name="解決数"
                stroke="#a6e3a1"
                strokeWidth={2}
                dot={{ fill: '#a6e3a1', r: 4 }}
                activeDot={{ r: 6 }}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
