import React, { useEffect, useMemo, useState } from 'react';
import { toast } from 'react-toastify';
import { Calculator, Calendar, TrendingDown, TrendingUp, Wallet } from 'lucide-react';
import { finance } from '../services/api';

const money = (value) => `R$ ${(value || 0).toFixed(2)}`;

const todayIso = () => new Date().toISOString().slice(0, 10);

const firstDayOfMonth = () => {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
};

export default function CashBook() {
  const [startDate, setStartDate] = useState(firstDayOfMonth());
  const [endDate, setEndDate] = useState(todayIso());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const summary = data?.summary || {};
  const entries = data?.entries || [];

  const loadLedger = async () => {
    setLoading(true);
    try {
      const res = await finance.ledger({ start_date: startDate, end_date: endDate });
      setData(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao carregar livro caixa');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadLedger(); }, []);

  const cards = useMemo(() => [
    { label: 'Entradas Recebidas', value: summary.received_total, icon: TrendingUp, color: 'text-green-700 bg-green-50' },
    { label: 'Contas a Receber', value: summary.receivable_total, icon: Wallet, color: 'text-blue-700 bg-blue-50' },
    { label: 'Saídas', value: summary.outflow_total, icon: TrendingDown, color: 'text-red-700 bg-red-50' },
    { label: 'Resultado Caixa', value: summary.cash_result, icon: Calculator, color: summary.cash_result >= 0 ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50' },
    { label: 'Resultado Projetado', value: summary.projected_result, icon: Calculator, color: summary.projected_result >= 0 ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50' },
    { label: 'Valor em Estoque', value: summary.stock_value, icon: Wallet, color: 'text-purple-700 bg-purple-50' },
  ], [summary]);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Livro Caixa</h1>
          <p className="text-gray-500 text-sm mt-1">Entradas, saídas, contas a receber e balanço de estoque.</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Início</label>
            <input type="date" className="input-field" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Fim</label>
            <input type="date" className="input-field" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
          <button type="button" onClick={loadLedger} className="btn-primary flex items-center gap-2 sm:self-end">
            <Calendar size={16} />
            Atualizar
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.label} className="card">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm text-gray-500">{card.label}</p>
                  <p className="text-2xl font-bold text-gray-800 mt-1">{money(card.value)}</p>
                </div>
                <div className={`p-3 rounded-xl ${card.color}`}>
                  <Icon size={22} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="card">
        <h2 className="font-semibold text-gray-800 mb-3">Balanço do período</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          <div className="rounded-lg bg-gray-50 p-3">
            <p className="text-gray-500">Recebido - Saídas</p>
            <p className={`font-semibold text-lg ${summary.cash_result >= 0 ? 'text-green-700' : 'text-red-700'}`}>{money(summary.cash_result)}</p>
          </div>
          <div className="rounded-lg bg-gray-50 p-3">
            <p className="text-gray-500">Recebido + A receber - Saídas</p>
            <p className={`font-semibold text-lg ${summary.projected_result >= 0 ? 'text-green-700' : 'text-red-700'}`}>{money(summary.projected_result)}</p>
          </div>
          <div className="rounded-lg bg-gray-50 p-3">
            <p className="text-gray-500">Contas a receber total em aberto</p>
            <p className="font-semibold text-lg text-blue-700">{money(summary.receivable_total_all)}</p>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 bg-white">
          <thead className="bg-gray-50">
            <tr>
              <th className="table-header">Data</th>
              <th className="table-header">Tipo</th>
              <th className="table-header">Categoria</th>
              <th className="table-header">Descrição</th>
              <th className="table-header text-right">Valor</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {entries.map((entry, index) => (
              <tr key={`${entry.reference_type}-${entry.reference_id}-${index}`} className="hover:bg-gray-50">
                <td className="table-cell">{new Date(entry.date).toLocaleDateString('pt-BR')}</td>
                <td className="table-cell">
                  <span className={
                    entry.kind === 'entrada' ? 'badge-green' :
                    entry.kind === 'saida' ? 'badge-red' :
                    'badge-blue'
                  }>
                    {entry.kind === 'entrada' ? 'Entrada' : entry.kind === 'saida' ? 'Saída' : 'A receber'}
                  </span>
                </td>
                <td className="table-cell">{entry.category.replaceAll('_', ' ')}</td>
                <td className="table-cell">{entry.description}</td>
                <td className={`table-cell text-right font-semibold ${entry.amount >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {money(entry.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && entries.length === 0 && <div className="bg-white p-8 text-center text-gray-500">Nenhum lançamento no período.</div>}
      </div>
    </div>
  );
}
