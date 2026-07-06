import React, { useState, useEffect } from 'react';
import { insights as insightsApi, dashboard as dashboardApi } from '../services/api';
import { toast } from 'react-toastify';
import { BarChart3, TrendingUp, Clock, Users, Package, Lightbulb, RefreshCw } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line
} from 'recharts';

const COLORS = ['#f9a30a', '#3b82f6', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];

const SECTION_ICONS = {
  'Produtos por Dia': TrendingUp,
  'Produtos por Mês': BarChart3,
  'Horários de Pico': Clock,
  'Top Clientes': Users,
  'Categorias': Package,
};

export default function Reports() {
  const [activeTab, setActiveTab] = useState('seasonality');
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    topProductsDay: [],
    topProductsMonth: [],
    peakHours: [],
    topClients: [],
    categoryConsumption: [],
    insights: [],
  });
  const [dashData, setDashData] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [day, month, hours, clients, cat, insightsRes, dash] = await Promise.all([
        insightsApi.topProductsDay().catch(() => ({ data: [] })),
        insightsApi.topProductsMonth().catch(() => ({ data: [] })),
        insightsApi.peakHours().catch(() => ({ data: [] })),
        insightsApi.topClients().catch(() => ({ data: [] })),
        insightsApi.categoryConsumption().catch(() => ({ data: [] })),
        insightsApi.active().catch(() => ({ data: [] })),
        dashboardApi.get().catch(() => ({ data: null })),
      ]);
      setData({
        topProductsDay: day.data,
        topProductsMonth: month.data,
        peakHours: hours.data,
        topClients: clients.data,
        categoryConsumption: cat.data,
        insights: insightsRes.data,
      });
      setDashData(dash.data);
    } catch {
      toast.error('Erro ao carregar relatórios');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const refreshInsights = async () => {
    try {
      await insightsApi.refresh();
      toast.success('Insights atualizados!');
      loadData();
    } catch {
      toast.error('Erro ao atualizar insights');
    }
  };

  const tabs = [
    { id: 'seasonality', label: 'Sazonalidade', icon: TrendingUp },
    { id: 'insights', label: 'Insights', icon: Lightbulb },
    { id: 'comparison', label: 'Comparativo', icon: BarChart3 },
  ];

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Relatórios & Insights</h1>
          <p className="text-gray-500 text-sm mt-1">Análise de sazonalidade e inteligência de dados</p>
        </div>
        <button onClick={refreshInsights} className="btn-secondary flex items-center gap-2">
          <RefreshCw size={16} />
          Atualizar
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon size={18} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeTab === 'seasonality' && (
        <div className="space-y-6">
          {/* Top Products by Day */}
          <div className="card">
            <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <TrendingUp size={18} className="text-primary-500" />
              Produtos Mais Vendidos por Dia da Semana
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.topProductsDay.map((dayData) => (
                <div key={dayData.day} className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-700 mb-2">{dayData.day}</p>
                  <div className="space-y-1">
                    {dayData.products?.slice(0, 5).map((p, i) => (
                      <div key={i} className="flex justify-between text-sm">
                        <span className="text-gray-600">{p.product_name}</span>
                        <span className="font-medium">{p.total_quantity}x (R$ {p.total_revenue.toFixed(2)})</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Peak Hours */}
          <div className="card">
            <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Clock size={18} className="text-primary-500" />
              Horários de Pico
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.peakHours}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <Tooltip formatter={(value, name) => [value, name === 'order_count' ? 'Pedidos' : 'R$']} />
                  <Bar dataKey="order_count" fill="#f9a30a" name="Pedidos" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Category Consumption */}
          <div className="card">
            <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Package size={18} className="text-primary-500" />
              Consumo por Categoria
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.categoryConsumption}
                    dataKey="total_revenue"
                    nameKey="category"
                    cx="50%" cy="50%"
                    outerRadius={80}
                    label={({ category, percent }) => `${category} (${(percent * 100).toFixed(0)}%)`}
                  >
                    {data.categoryConsumption.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `R$ ${Number(value).toFixed(2)}`} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top Clients */}
          <div className="card">
            <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Users size={18} className="text-primary-500" />
              Clientes com Maior Consumo
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-left text-xs text-gray-500">
                    <th className="pb-2 font-medium">#</th>
                    <th className="pb-2 font-medium">Cliente</th>
                    <th className="pb-2 font-medium text-right">Pedidos</th>
                    <th className="pb-2 font-medium text-right">Total Consumido</th>
                  </tr>
                </thead>
                <tbody>
                  {data.topClients.map((c, i) => (
                    <tr key={c.client_id} className="border-t border-gray-100">
                      <td className="py-2 text-sm text-gray-400">{i + 1}</td>
                      <td className="py-2 text-sm font-medium text-gray-700">{c.client_name}</td>
                      <td className="py-2 text-sm text-right">{c.order_count}</td>
                      <td className="py-2 text-sm text-right font-medium">R$ {c.total_consumed.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'insights' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">{data.insights.length} insights ativos</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.insights.map((insight) => (
              <div
                key={insight.id}
                className={`p-4 rounded-xl border ${
                  insight.severity === 'alert' ? 'bg-red-50 border-red-200' :
                  insight.severity === 'warning' ? 'bg-yellow-50 border-yellow-200' :
                  'bg-blue-50 border-blue-200'
                }`}
              >
                <div className="flex items-start gap-3">
                  <Lightbulb
                    size={20}
                    className={`flex-shrink-0 ${
                      insight.severity === 'alert' ? 'text-red-500' :
                      insight.severity === 'warning' ? 'text-yellow-500' :
                      'text-blue-500'
                    }`}
                  />
                  <div>
                    <h4 className="font-semibold text-gray-800 text-sm">{insight.title}</h4>
                    {insight.description && (
                      <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
                    )}
                    <span className={`inline-block mt-2 text-xs px-2 py-0.5 rounded-full ${
                      insight.severity === 'alert' ? 'bg-red-100 text-red-700' :
                      insight.severity === 'warning' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {insight.severity === 'alert' ? 'Alerta' : insight.severity === 'warning' ? 'Aviso' : 'Info'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
            {data.insights.length === 0 && (
              <div className="col-span-2 text-center py-12 text-gray-400">
                <Lightbulb className="mx-auto mb-2" size={48} />
                <p>Nenhum insight disponível</p>
                <button onClick={refreshInsights} className="btn-secondary mt-4 inline-flex items-center gap-2">
                  <RefreshCw size={16} />
                  Gerar Insights
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'comparison' && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="font-semibold text-gray-800 mb-4">Comparativo Mensal</h3>
            <div className="text-center py-8">
              <BarChart3 className="mx-auto text-gray-300" size={64} />
              <p className="text-gray-500 mt-4">
                O comparativo mensal é gerado automaticamente nos insights.
              </p>
              <p className="text-sm text-gray-400 mt-1">
                Acesse a aba "Insights" para ver análises de crescimento/queda.
              </p>
            </div>
          </div>

          {dashData && (
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-4">Resumo do Mês Atual</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-xl">
                  <p className="text-2xl font-bold text-blue-600">R$ {dashData.month_revenue_open.toFixed(2)}</p>
                  <p className="text-xs text-blue-600 mt-1">Faturamento</p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-xl">
                  <p className="text-2xl font-bold text-green-600">R$ {dashData.month_revenue_paid.toFixed(2)}</p>
                  <p className="text-xs text-green-600 mt-1">Pago</p>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-xl">
                  <p className="text-2xl font-bold text-yellow-600">R$ {dashData.month_revenue_pending.toFixed(2)}</p>
                  <p className="text-xs text-yellow-600 mt-1">Pendente</p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-xl">
                  <p className="text-2xl font-bold text-purple-600">{dashData.total_orders_month}</p>
                  <p className="text-xs text-purple-600 mt-1">Pedidos</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
