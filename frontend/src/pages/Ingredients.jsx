import React, { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { Package, Plus, RefreshCw } from 'lucide-react';
import { stock } from '../services/api';

const initialForm = {
  name: '',
  category: '',
  unit_measure: 'kg',
  current_quantity: '',
  minimum_stock: '',
  unit_cost: '',
  expiry_date: '',
  notes: '',
};

export default function Ingredients() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(initialForm);
  const [movement, setMovement] = useState({ stock_item_id: '', quantity: '', unit_cost: '', notes: '' });

  const loadItems = async () => {
    try {
      const { data } = await stock.items.list({ limit: 500 });
      setItems(data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao carregar ingredientes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadItems(); }, []);

  const createIngredient = async (e) => {
    e.preventDefault();
    if (!form.name) {
      toast.warning('Informe o nome do ingrediente');
      return;
    }
    try {
      await stock.items.create({
        ...form,
        current_quantity: form.current_quantity ? parseFloat(form.current_quantity) : 0,
        minimum_stock: form.minimum_stock ? parseFloat(form.minimum_stock) : 0,
        unit_cost: form.unit_cost ? parseFloat(form.unit_cost) : 0,
        expiry_date: form.expiry_date || null,
        category: form.category || null,
        notes: form.notes || null,
      });
      toast.success('Ingrediente cadastrado');
      setForm(initialForm);
      loadItems();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao cadastrar ingrediente');
    }
  };

  const addStock = async (e) => {
    e.preventDefault();
    if (!movement.stock_item_id || !movement.quantity) {
      toast.warning('Selecione ingrediente e quantidade');
      return;
    }
    try {
      await stock.movements.create({
        stock_item_id: parseInt(movement.stock_item_id, 10),
        movement_type: 'entrada_compra',
        quantity: parseFloat(movement.quantity),
        unit_cost: movement.unit_cost ? parseFloat(movement.unit_cost) : 0,
        reference_type: 'manual_stock_entry',
        notes: movement.notes || null,
      });
      toast.success('Entrada de estoque registrada');
      setMovement({ stock_item_id: '', quantity: '', unit_cost: '', notes: '' });
      loadItems();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao registrar entrada');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Ingredientes</h1>
        <p className="text-gray-500 text-sm mt-1">Controle de insumos usados nas fichas técnicas dos pratos.</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <form onSubmit={createIngredient} className="card space-y-3">
          <h2 className="font-semibold text-gray-700 flex items-center gap-2"><Plus size={18} />Novo ingrediente</h2>
          <input className="input-field" placeholder="Nome do ingrediente" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <div className="grid grid-cols-2 gap-3">
            <input className="input-field" placeholder="Categoria" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
            <select className="input-field" value={form.unit_measure} onChange={(e) => setForm({ ...form, unit_measure: e.target.value })}>
              {['kg', 'g', 'litro', 'ml', 'unidade', 'pacote', 'caixa'].map((unit) => <option key={unit} value={unit}>{unit}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <input type="number" step="0.001" className="input-field" placeholder="Qtd atual" value={form.current_quantity} onChange={(e) => setForm({ ...form, current_quantity: e.target.value })} />
            <input type="number" step="0.001" className="input-field" placeholder="Mínimo" value={form.minimum_stock} onChange={(e) => setForm({ ...form, minimum_stock: e.target.value })} />
            <input type="number" step="0.01" className="input-field" placeholder="Custo unit." value={form.unit_cost} onChange={(e) => setForm({ ...form, unit_cost: e.target.value })} />
          </div>
          <input type="date" className="input-field" value={form.expiry_date} onChange={(e) => setForm({ ...form, expiry_date: e.target.value })} />
          <textarea className="input-field" rows={2} placeholder="Observações" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          <button type="submit" className="btn-primary">Cadastrar Ingrediente</button>
        </form>

        <form onSubmit={addStock} className="card space-y-3">
          <h2 className="font-semibold text-gray-700 flex items-center gap-2"><RefreshCw size={18} />Entrada de estoque</h2>
          <select className="input-field" value={movement.stock_item_id} onChange={(e) => setMovement({ ...movement, stock_item_id: e.target.value })}>
            <option value="">Selecione o ingrediente...</option>
            {items.map((item) => <option key={item.id} value={item.id}>{item.name} ({item.unit_measure})</option>)}
          </select>
          <div className="grid grid-cols-2 gap-3">
            <input type="number" step="0.001" className="input-field" placeholder="Quantidade" value={movement.quantity} onChange={(e) => setMovement({ ...movement, quantity: e.target.value })} />
            <input type="number" step="0.01" className="input-field" placeholder="Custo unitário" value={movement.unit_cost} onChange={(e) => setMovement({ ...movement, unit_cost: e.target.value })} />
          </div>
          <textarea className="input-field" rows={2} placeholder="Nota/observação" value={movement.notes} onChange={(e) => setMovement({ ...movement, notes: e.target.value })} />
          <button type="submit" className="btn-primary">Registrar Entrada</button>
        </form>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 bg-white">
          <thead className="bg-gray-50">
            <tr>
              <th className="table-header">Código</th>
              <th className="table-header">Ingrediente</th>
              <th className="table-header">Categoria</th>
              <th className="table-header">Estoque</th>
              <th className="table-header">Mínimo</th>
              <th className="table-header">Custo médio</th>
              <th className="table-header">Validade</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {items.map((item) => {
              const low = item.minimum_stock > 0 && item.current_quantity <= item.minimum_stock;
              return (
                <tr key={item.id} className={low ? 'bg-red-50' : 'hover:bg-gray-50'}>
                  <td className="table-cell font-mono text-xs text-primary-700">{item.code || 'Código pendente'}</td>
                  <td className="table-cell font-medium text-gray-800"><span className="inline-flex items-center gap-2"><Package size={14} />{item.name}</span></td>
                  <td className="table-cell">{item.category || '-'}</td>
                  <td className="table-cell">{item.current_quantity.toFixed(3)} {item.unit_measure}</td>
                  <td className="table-cell">{item.minimum_stock.toFixed(3)} {item.unit_measure}</td>
                  <td className="table-cell">R$ {(item.average_cost || item.unit_cost || 0).toFixed(2)}</td>
                  <td className="table-cell">{item.expiry_date ? new Date(`${item.expiry_date}T00:00:00`).toLocaleDateString('pt-BR') : '-'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!loading && items.length === 0 && <div className="bg-white p-8 text-center text-gray-500">Nenhum ingrediente cadastrado.</div>}
      </div>
    </div>
  );
}
