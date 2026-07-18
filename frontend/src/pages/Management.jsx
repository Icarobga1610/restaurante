import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, BarChart3, Package, Percent, RefreshCw, Tag, TrendingUp } from 'lucide-react';
import { toast } from 'react-toastify';
import { products, promotions, stock } from '../services/api';

const money = (value) => Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

export default function Management() {
  const [productList, setProductList] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [expiring, setExpiring] = useState([]);
  const [promotionList, setPromotionList] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const [productResult, stockResult, expiringResult, promotionResult] = await Promise.allSettled([
      products.list({ active_only: true, limit: 500 }),
      stock.alerts.lowStock(),
      stock.alerts.expiring({ days: 7 }),
      promotions.list({ active_only: true }),
    ]);
    setProductList(productResult.status === 'fulfilled' ? productResult.value.data : []);
    setLowStock(stockResult.status === 'fulfilled' ? stockResult.value.data : []);
    setExpiring(expiringResult.status === 'fulfilled' ? expiringResult.value.data : []);
    setPromotionList(promotionResult.status === 'fulfilled' ? promotionResult.value.data : []);
    if (productResult.status === 'rejected') toast.error('Não foi possível carregar os indicadores de margem.');
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const marginSummary = useMemo(() => {
    const withCost = productList.filter((product) => product.estimated_cost != null);
    const revenue = withCost.reduce((sum, product) => sum + Number(product.price || 0), 0);
    const cost = withCost.reduce((sum, product) => sum + Number(product.estimated_cost || 0), 0);
    return { count: withCost.length, margin: revenue ? ((revenue - cost) / revenue) * 100 : 0, revenue, cost };
  }, [productList]);

  return <div className="space-y-6 animate-fade-in">
    <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between"><div><p className="text-sm font-medium text-primary-600">Gestão avançada</p><h1 className="text-2xl font-bold text-gray-900">Margem, estoque e oportunidades</h1><p className="mt-1 text-sm text-gray-500">Use custo estimado, fichas técnicas e alertas para decidir antes do problema chegar ao caixa.</p></div><button onClick={load} className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"><RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Atualizar</button></div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><div className="card"><div className="flex items-center justify-between"><span className="text-sm text-gray-500">Produtos com custo</span><BarChart3 className="text-primary-600" size={20} /></div><p className="mt-2 text-2xl font-bold text-gray-900">{marginSummary.count}</p></div><div className="card"><div className="flex items-center justify-between"><span className="text-sm text-gray-500">Margem média estimada</span><TrendingUp className="text-emerald-600" size={20} /></div><p className="mt-2 text-2xl font-bold text-emerald-600">{marginSummary.margin.toFixed(1)}%</p></div><div className="card"><div className="flex items-center justify-between"><span className="text-sm text-gray-500">Alertas de estoque</span><Package className="text-amber-600" size={20} /></div><p className="mt-2 text-2xl font-bold text-amber-600">{lowStock.length}</p></div><div className="card"><div className="flex items-center justify-between"><span className="text-sm text-gray-500">Promoções ativas</span><Tag className="text-purple-600" size={20} /></div><p className="mt-2 text-2xl font-bold text-purple-600">{promotionList.length}</p></div></div>
    <div className="grid gap-6 lg:grid-cols-2"><section className="card"><div className="mb-4 flex items-center justify-between"><h2 className="flex items-center gap-2 font-semibold text-gray-800"><Percent size={18} className="text-primary-600" /> Produtos e margem</h2><span className="text-xs text-gray-400">Preço total {money(marginSummary.revenue)}</span></div><div className="max-h-80 space-y-2 overflow-y-auto">{productList.slice(0, 20).map((product) => { const margin = product.price ? ((product.price - (product.estimated_cost || 0)) / product.price) * 100 : 0; return <div key={product.id} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm"><span className="truncate pr-3 font-medium text-gray-700">{product.name}</span><span className={margin < 30 ? 'font-semibold text-red-600' : 'font-semibold text-emerald-600'}>{margin.toFixed(1)}%</span></div>; })}{productList.length === 0 && <p className="py-8 text-center text-sm text-gray-400">Cadastre custos estimados nos produtos para acompanhar margem.</p>}</div></section><section className="card"><div className="mb-4 flex items-center justify-between"><h2 className="flex items-center gap-2 font-semibold text-gray-800"><AlertTriangle size={18} className="text-amber-600" /> Alertas operacionais</h2><span className="text-xs text-gray-400">Próximos 7 dias</span></div><div className="space-y-2">{lowStock.slice(0, 8).map((item) => <div key={`low-${item.id}`} className="flex items-center justify-between rounded-lg bg-amber-50 px-3 py-2 text-sm"><span className="text-amber-800">{item.name || item.ingredient_name}</span><b className="text-amber-700">Estoque baixo</b></div>)}{expiring.slice(0, 8).map((item) => <div key={`exp-${item.id}`} className="flex items-center justify-between rounded-lg bg-red-50 px-3 py-2 text-sm"><span className="text-red-800">{item.name || item.ingredient_name}</span><b className="text-red-700">Vencendo</b></div>)}{lowStock.length === 0 && expiring.length === 0 && <p className="py-8 text-center text-sm text-gray-400">Nenhum alerta de estoque no momento.</p>}</div></section></div>
  </div>;
}
