import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { VulnerabilityListPage } from './pages/VulnerabilityListPage';
import { AssetManagementPage } from './pages/AssetManagementPage';
import { MatchingResultsPage } from './pages/MatchingResultsPage';

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
