import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  LayoutDashboard, Users, ShoppingBag, ClipboardList, FileText,
  Fingerprint, Truck, BarChart3, History, LogOut, Menu, X, Package, Calculator,
  UtensilsCrossed, Bell, Building2, TrendingUp
} from 'lucide-react';

const navItems = [
  { section: 'Visão geral', label: 'Dashboard', icon: LayoutDashboard, path: '/' },
  { section: 'Operação', label: 'Central de Operação', icon: UtensilsCrossed, path: '/operations' },
  { section: 'Operação', label: 'Pedidos', icon: ClipboardList, path: '/orders' },
  { section: 'Operação', label: 'Entrega', icon: Truck, path: '/delivery' },
  { section: 'Cadastros', label: 'Clientes', icon: Users, path: '/clients' },
  { section: 'Cadastros', label: 'Empresas', icon: Building2, path: '/companies' },
  { section: 'Cadastros', label: 'Produtos', icon: ShoppingBag, path: '/products' },
  { section: 'Cadastros', label: 'Ingredientes', icon: Package, path: '/ingredients' },
  { section: 'Cadastros', label: 'Fichas Técnicas', icon: ClipboardList, path: '/recipes' },
  { section: 'Financeiro', label: 'Contas Mensais', icon: FileText, path: '/monthly-accounts' },
  { section: 'Financeiro', label: 'Livro Caixa', icon: Calculator, path: '/cash-book' },
  { section: 'Financeiro', label: 'Pagamentos', icon: Calculator, path: '/payment-methods' },
  { section: 'Gestão', label: 'Margem e Alertas', icon: TrendingUp, path: '/management' },
  { section: 'Gestão', label: 'Biometria', icon: Fingerprint, path: '/biometric' },
  { section: 'Gestão', label: 'Relatórios', icon: BarChart3, path: '/reports' },
  { section: 'Gestão', label: 'Auditoria', icon: History, path: '/audit' },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 lg:translate-x-0 lg:static lg:z-auto flex flex-col ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-100">
          <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center">
            <UtensilsCrossed className="text-white" size={20} />
          </div>
          <div>
            <h1 className="font-bold text-gray-800 text-lg leading-tight">Restaurante</h1>
            <p className="text-xs text-gray-500">Conta Mensal</p>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item, index) => {
            const isActive = location.pathname === item.path ||
              (item.path !== '/' && location.pathname.startsWith(item.path));
            const Icon = item.icon;
            return (
              <React.Fragment key={item.path}>
                {(index === 0 || navItems[index - 1].section !== item.section) && (
                  <p className="px-4 pt-4 pb-1 text-[10px] font-bold uppercase tracking-wider text-gray-400">{item.section}</p>
                )}
                <Link
                  key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-primary-50 text-primary-700 border border-primary-100'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-800'
                }`}
              >
                <Icon size={18} className={isActive ? 'text-primary-600' : 'text-gray-400'} />
                {item.label}
                </Link>
              </React.Fragment>
            );
          })}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <div className="flex items-center justify-between mb-2 px-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                <span className="text-primary-700 font-semibold text-sm">
                  {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
                </span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700 leading-tight">{user?.full_name}</p>
                <p className="text-xs text-gray-400 capitalize">{user?.role_name}</p>
              </div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut size={16} />
            Sair
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Top bar */}
        <header className="bg-white border-b border-gray-200 px-4 lg:px-8 py-3 flex items-center justify-between lg:justify-end sticky top-0 z-10">
          <button
            className="lg:hidden p-2 hover:bg-gray-100 rounded-lg"
            onClick={() => setSidebarOpen(true)}
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          <div className="flex items-center gap-4">
            <button className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 relative">
              <Bell size={18} />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
