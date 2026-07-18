import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { dashboard as dashboardApi, insights as insightsApi } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'react-toastify';
import {
  DollarSign, TrendingUp, TrendingDown, Users, ShoppingCart,
  AlertTriangle, RefreshCw, BarChart3, Clock, Package, Target,
  ChevronRight, Lightbulb, CreditCard, Ban
} from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';

const COLORS = ['#f9a30a', '#3b82f6', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generatingInsights, setGeneratingInsights] = useState(false);
  const { hasRole } = useAuth();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [dashRes] = await Promise.all([
        dashboardApi.get(),
      ]);
      setData(dashRes.data);
    } catch (err) {
      toast.error('Erro ao carregar dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadInsights = async () => {
    try {
      const res = await insightsApi.active();
      setInsights(res.data);
    } catch {
      // silent
    }
  };

  const generateInsights = async () => {
    setGeneratingInsights(true);
    try {
      const res = await insightsApi.refresh();
      toast.success(`${res.data.message}`);
      loadInsights();
    } catch (err) {
      toast.error('Erro ao gerar insights');
    } finally {
      setGeneratingInsights(false);
    }
  };

  useEffect(() => {
    if (data) {
      loadInsights();
    }
  }, [data]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  const statCards = [
    {
      label: 'Faturamento em Aberto',
      value: `R$ ${(data?.month_revenue_open || 0).toFixed(2)}`,
      icon: DollarSign,
      color: 'bg-blue-50 text-blue-600',
      bg: 'bg-blue-500',
    },
    {
      label: 'Valor Pago',
      value: `R$ ${(data?.month_revenue_paid || 0).toFixed(2)}`,
      icon: CreditCard,
      color: 'bg-green-50 text-green-600',
      bg: 'bg-green-500',
    },
    {
      label: 'Valor Pendente',
      value: `R$ ${(data?.month_revenue_pending || 0).toFixed(2)}`,
      icon: AlertTriangle,
      color: 'bg-yellow-50 text-yellow-600',
      bg: 'bg-yellow-500',
    },
    {
      label: 'Clientes Ativos',
      value: data?.active_clients || 0,
      icon: Users,
      color: 'bg-purple-50 text-purple-600',
      bg: 'bg-purple-500',
    },
    {
      label: 'Pedidos no Mês',
      value: data?.total_orders_month || 0,
      icon: ShoppingCart,
      color: 'bg-indigo-50 text-indigo-600',
      bg: 'bg-indigo-500',
    },
    {
      label: 'Ticket Médio',
      value: `R$ ${(data?.average_ticket || 0).toFixed(2)}`,
      icon: Target,
      color: 'bg-rose-50 text-rose-600',
      bg: 'bg-rose-500',
    },
    {
      label: 'Contas Vencidas',
      value: data?.overdue_accounts || 0,
      icon: Ban,
      color: 'bg-red-50 text-red-600',
      bg: 'bg-red-500',
      alert: data?.overdue_accounts > 0,
    },
    {
      label: 'Sem Biometria',
      value: data?.unsigned_accounts || 0,
      icon: AlertTriangle,
      color: 'bg-orange-50 text-orange-600',
      bg: 'bg-orange-500',
      alert: data?.unsigned_accounts > 0,
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">Visão geral do mês atual</p>
        </div>
        {hasRole('admin', 'financial') && (
          <button
            onClick={generateInsights}
            disabled={generatingInsights}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw size={16} className={generatingInsights ? 'animate-spin' : ''} />
            Atualizar Insights
          </button>
        )}
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={`card animate-slide-in relative overflow-hidden ${card.alert ? 'ring-2 ring-red-200' : ''}`}
              style={{ animationDelay: `${idx * 50}ms` }}
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500 font-medium">{card.label}</p>
                  <p className={`text-2xl font-bold mt-1 ${card.alert ? 'text-red-600' : 'text-gray-800'}`}>
                    {card.value}
                  </p>
                </div>
                <div className={`p-3 rounded-xl ${card.color}`}>
                  <Icon size={24} />
                </div>
              </div>
              {card.alert && (
                <div className="mt-2 flex items-center gap-1 text-xs text-red-600">
                  <AlertTriangle size={12} />
                  <span>Atenção necessária</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="card border-primary-100 bg-gradient-to-r from-primary-50/70 to-white">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-primary-600">Próximas ações</p>
            <h3 className="mt-1 text-lg font-semibold text-gray-800">O que precisa da sua atenção hoje?</h3>
            <p className="mt-1 text-sm text-gray-500">Acesse a operação, o financeiro ou o faturamento corporativo sem procurar no menu.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link to="/operations" className="rounded-lg bg-gray-900 px-3 py-2 text-sm font-semibold text-white hover:bg-gray-700">Central de operação</Link>
            <Link to="/monthly-accounts" className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">Contas mensais</Link>
            <Link to="/companies" className="rounded-lg border border-primary-200 bg-white px-3 py-2 text-sm font-semibold text-primary-700 hover:bg-primary-50">Empresas</Link>
          </div>
        </div>
        <div className="mt-4 grid gap-3 border-t border-primary-100 pt-4 sm:grid-cols-3">
          <div><p className="text-xs text-gray-500">Contas vencidas</p><p className={`mt-1 text-xl font-bold ${data?.overdue_accounts > 0 ? 'text-red-600' : 'text-gray-800'}`}>{data?.overdue_accounts || 0}</p></div>
          <div><p className="text-xs text-gray-500">Contas sem biometria</p><p className={`mt-1 text-xl font-bold ${data?.unsigned_accounts > 0 ? 'text-orange-600' : 'text-gray-800'}`}>{data?.unsigned_accounts || 0}</p></div>
          <div><p className="text-xs text-gray-500">Produtos ativos</p><p className="mt-1 text-xl font-bold text-gray-800">{data?.total_products || 0}</p></div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Consumption by day */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <BarChart3 size={18} className="text-primary-500" />
            Consumo por Dia
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.consumption_by_day || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value) => [`R$ ${value?.toFixed(2)}`, 'Total']}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                />
                <Bar dataKey="total" fill="#f9a30a" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Consumption by category */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <PieChart size={18} className="text-primary-500" />
            Consumo por Categoria
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data?.consumption_by_category || []}
                  dataKey="total"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={50}
                  label={({ category, percent }) => `${category} ${(percent * 100).toFixed(0)}%`}
                >
                  {(data?.consumption_by_category || []).map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`R$ ${value?.toFixed(2)}`, 'Total']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Products */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Package size={18} className="text-primary-500" />
            Produtos Mais Vendidos
          </h3>
          <div className="space-y-3">
            {(data?.top_products || []).slice(0, 8).map((p, idx) => (
              <div key={p.id} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-400 w-6">{idx + 1}.</span>
                  <span className="text-sm text-gray-700">{p.name}</span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-800">{p.quantity}x</p>
                  <p className="text-xs text-gray-400">R$ {p.total?.toFixed(2)}</p>
                </div>
              </div>
            ))}
            {(!data?.top_products || data.top_products.length === 0) && (
              <p className="text-gray-400 text-sm">Nenhum dado disponível</p>
            )}
          </div>
        </div>

        {/* Top Clients */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Users size={18} className="text-primary-500" />
            Clientes com Maior Consumo
          </h3>
          <div className="space-y-3">
            {(data?.top_clients || []).slice(0, 8).map((c, idx) => (
              <div key={c.id} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-400 w-6">{idx + 1}.</span>
                  <span className="text-sm text-gray-700">{c.name}</span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-800">{c.order_count} pedidos</p>
                  <p className="text-xs text-gray-400">R$ {c.total?.toFixed(2)}</p>
                </div>
              </div>
            ))}
            {(!data?.top_clients || data.top_clients.length === 0) && (
              <p className="text-gray-400 text-sm">Nenhum dado disponível</p>
            )}
          </div>
        </div>
      </div>

      {/* Insights */}
      {insights.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Lightbulb size={18} className="text-yellow-500" />
            Insights Inteligentes
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {insights.map((insight, idx) => (
              <div
                key={insight.id}
                className={`p-4 rounded-xl border ${
                  insight.severity === 'alert' ? 'bg-red-50 border-red-200' :
                  insight.severity === 'warning' ? 'bg-yellow-50 border-yellow-200' :
                  'bg-blue-50 border-blue-200'
                }`}
              >
                <div className="flex items-start gap-2">
                  <Lightbulb
                    size={16}
                    className={`mt-0.5 flex-shrink-0 ${
                      insight.severity === 'alert' ? 'text-red-500' :
                      insight.severity === 'warning' ? 'text-yellow-500' :
                      'text-blue-500'
                    }`}
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-800">{insight.title}</p>
                    {insight.description && (
                      <p className="text-xs text-gray-500 mt-1">{insight.description}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
