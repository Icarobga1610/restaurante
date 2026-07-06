import React, { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { CreditCard, Plus, Star } from 'lucide-react';
import { paymentMethods } from '../services/api';

export default function PaymentMethods() {
  const [methods, setMethods] = useState([]);
  const [form, setForm] = useState({ code: '', name: '', is_default: false });
  const [loading, setLoading] = useState(true);

  const loadMethods = async () => {
    try {
      const { data } = await paymentMethods.list({ active_only: false });
      setMethods(data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao carregar formas de pagamento');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadMethods(); }, []);

  const createMethod = async (e) => {
    e.preventDefault();
    if (!form.code || !form.name) {
      toast.warning('Informe código e nome');
      return;
    }
    try {
      await paymentMethods.create(form);
      toast.success('Forma de pagamento cadastrada');
      setForm({ code: '', name: '', is_default: false });
      loadMethods();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao cadastrar forma de pagamento');
    }
  };

  const setDefault = async (method) => {
    try {
      await paymentMethods.setDefault(method.id);
      toast.success(`${method.name} definida como principal`);
      loadMethods();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao definir principal');
    }
  };

  const toggleActive = async (method) => {
    try {
      await paymentMethods.update(method.id, { is_active: !method.is_active });
      loadMethods();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao atualizar forma de pagamento');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Formas de Pagamento</h1>
        <p className="text-gray-500 text-sm mt-1">Cadastre as formas aceitas e marque a principal para registros rápidos.</p>
      </div>

      <form onSubmit={createMethod} className="card space-y-3 max-w-2xl">
        <h2 className="font-semibold text-gray-700 flex items-center gap-2"><Plus size={18} />Nova forma</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <input className="input-field" placeholder="Código. Ex: pix, dinheiro" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          <input className="input-field" placeholder="Nome. Ex: Pix" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={form.is_default} onChange={(e) => setForm({ ...form, is_default: e.target.checked })} />
          Definir como forma principal
        </label>
        <button type="submit" className="btn-primary">Cadastrar</button>
      </form>

      <div className="overflow-x-auto rounded-xl border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 bg-white">
          <thead className="bg-gray-50">
            <tr>
              <th className="table-header">Forma</th>
              <th className="table-header">Código</th>
              <th className="table-header">Status</th>
              <th className="table-header">Principal</th>
              <th className="table-header text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {methods.map((method) => (
              <tr key={method.id} className="hover:bg-gray-50">
                <td className="table-cell font-medium text-gray-800">
                  <span className="inline-flex items-center gap-2"><CreditCard size={14} />{method.name}</span>
                </td>
                <td className="table-cell">{method.code}</td>
                <td className="table-cell">{method.is_active ? <span className="badge-green">Ativa</span> : <span className="badge-red">Inativa</span>}</td>
                <td className="table-cell">{method.is_default ? <span className="badge-blue">Principal</span> : '-'}</td>
                <td className="table-cell text-right">
                  <div className="flex items-center justify-end gap-2">
                    {!method.is_default && method.is_active && (
                      <button className="btn-secondary text-sm py-1.5 px-3 inline-flex items-center gap-1" onClick={() => setDefault(method)}>
                        <Star size={14} />
                        Principal
                      </button>
                    )}
                    <button className="btn-secondary text-sm py-1.5 px-3" onClick={() => toggleActive(method)}>
                      {method.is_active ? 'Inativar' : 'Ativar'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && methods.length === 0 && <div className="bg-white p-8 text-center text-gray-500">Nenhuma forma cadastrada.</div>}
      </div>
    </div>
  );
}
