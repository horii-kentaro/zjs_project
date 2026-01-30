import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { VulnerabilityListPage } from './pages/VulnerabilityListPage';

// プレースホルダーコンポーネント（後で実装）
const DashboardPage = () => <div className="p-8 text-text">Dashboard (実装予定)</div>;
const AssetManagementPage = () => <div className="p-8 text-text">Asset Management (実装予定)</div>;
const MatchingResultsPage = () => <div className="p-8 text-text">Matching Results (実装予定)</div>;

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        {/* ダッシュボードホーム */}
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />

        {/* 既存3ページのReact版 */}
        <Route path="dashboard/vulnerabilities" element={<VulnerabilityListPage />} />
        <Route path="dashboard/assets" element={<AssetManagementPage />} />
        <Route path="dashboard/matching" element={<MatchingResultsPage />} />

        {/* 404 */}
        <Route path="*" element={<div className="p-8 text-text">404 Not Found</div>} />
      </Route>
    </Routes>
  );
}

export default App;
