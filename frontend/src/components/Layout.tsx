import { Outlet, Link, useLocation } from 'react-router-dom';
import { Home, FileText, Package, GitMerge } from 'lucide-react';

export function Layout() {
  const location = useLocation();

  const navItems = [
    { path: '/dashboard', label: 'ダッシュボード', icon: Home },
    { path: '/dashboard/vulnerabilities', label: '脆弱性一覧', icon: FileText },
    { path: '/dashboard/assets', label: '資産管理', icon: Package },
    { path: '/dashboard/matching', label: 'マッチング結果', icon: GitMerge },
  ];

  return (
    <div className="min-h-screen bg-base">
      {/* ナビゲーションバー */}
      <nav className="bg-surface-0 border-b border-surface-1">
        <div className="mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-text">
                🛡️ 脆弱性管理システム
              </h1>
            </div>

            <div className="flex space-x-4">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;

                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`
                      flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors
                      ${
                        isActive
                          ? 'bg-blue text-base'
                          : 'text-subtext-0 hover:bg-surface-1 hover:text-text'
                      }
                    `}
                  >
                    <Icon size={18} />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </nav>

      {/* メインコンテンツ */}
      <main>
        <Outlet />
      </main>
    </div>
  );
}
