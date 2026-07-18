import React, { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, ChefHat, Clock3, RefreshCw, Truck, XCircle } from 'lucide-react';
import { toast } from 'react-toastify';
import { orders as ordersApi } from '../services/api';

const columns = [
  { key: 'confirmed', label: 'Recebidos', icon: Clock3, tone: 'blue', next: 'invoiced' },
  { key: 'invoiced', label: 'Em preparo', icon: ChefHat, tone: 'amber', next: 'paid' },
  { key: 'paid', label: 'Prontos', icon: CheckCircle2, tone: 'emerald', next: null },
];

const toneClasses = {
  blue: 'border-blue-200 bg-blue-50 text-blue-700',
  amber: 'border-amber-200 bg-amber-50 text-amber-700',
  emerald: 'border-emerald-200 bg-emerald-50 text-emerald-700',
};

export default function Operations() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const response = await ordersApi.list({ limit: 200 });
      setOrders(response.data.filter((order) => ['confirmed', 'invoiced', 'paid'].includes(order.status)));
    } catch {
      toast.error('Erro ao carregar a central de operação.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const grouped = useMemo(() => Object.fromEntries(columns.map((column) => [column.key, orders.filter((order) => order.status === column.key)])), [orders]);

  const advance = async (order, next) => {
    try {
      await ordersApi.update(order.id, { status: next });
      toast.success(`Pedido #${order.id} avançou para ${columns.find((column) => column.key === next)?.label || next}.`);
      await load();
    } catch {
      toast.error('Não foi possível atualizar o pedido.');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div><p className="text-sm font-medium text-primary-600">Operação em tempo real</p><h1 className="text-2xl font-bold text-gray-900">Central de Operação</h1><p className="mt-1 text-sm text-gray-500">Acompanhe pedidos recebidos, preparo e pedidos prontos em uma única tela.</p></div>
        <button onClick={load} className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"><RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Atualizar</button>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {columns.map((column) => { const Icon = column.icon; return <div key={column.key} className={`rounded-xl border px-4 py-3 ${toneClasses[column.tone]}`}><div className="flex items-center justify-between"><span className="flex items-center gap-2 text-sm font-semibold"><Icon size={17} /> {column.label}</span><strong>{grouped[column.key]?.length || 0}</strong></div></div>; })}
      </div>
      {loading ? <div className="py-16 text-center text-sm text-gray-500">Carregando pedidos...</div> : <div className="grid gap-5 xl:grid-cols-3">
        {columns.map((column) => { const Icon = column.icon; return <section key={column.key} className="min-h-[320px] rounded-2xl border border-gray-200 bg-gray-50 p-3"><div className="mb-3 flex items-center gap-2 px-2 text-sm font-semibold text-gray-700"><Icon size={17} /> {column.label}</div><div className="space-y-3">{(grouped[column.key] || []).map((order) => <article key={order.id} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm"><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-bold text-gray-400">PEDIDO #{order.id}</p><h3 className="mt-1 font-semibold text-gray-800">{order.client_name || 'Cliente'}</h3><p className="mt-1 text-xs text-gray-500">{new Date(order.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} · {order.items?.length || 0} item(ns)</p></div><span className="font-bold text-gray-800">R$ {Number(order.total || 0).toFixed(2)}</span></div><div className="mt-3 border-t border-gray-100 pt-3 text-xs text-gray-600">{order.items?.slice(0, 3).map((item) => <p key={item.id}>{item.quantity}x {item.product_name}</p>)}{order.items?.length > 3 && <p className="mt-1 text-gray-400">+ {order.items.length - 3} item(ns)</p>}</div>{column.next && <button onClick={() => advance(order, column.next)} className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-gray-900 px-3 py-2 text-xs font-semibold text-white hover:bg-gray-700">{column.next === 'invoiced' ? <ChefHat size={14} /> : <Truck size={14} />} Avançar pedido</button>}</article>)}{grouped[column.key]?.length === 0 && <div className="rounded-xl border border-dashed border-gray-300 px-4 py-10 text-center text-xs text-gray-400">Nenhum pedido nesta etapa</div>}</div></section>; })}
      </div>}
      <div className="flex items-center gap-2 text-xs text-gray-400"><XCircle size={14} /> Cancelamentos e detalhes completos continuam disponíveis em Pedidos.</div>
    </div>
  );
}
