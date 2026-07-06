import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { products as productsApi } from '../services/api';
import { toast } from 'react-toastify';
import { Save, ArrowLeft } from 'lucide-react';

const CATEGORIES = ['Bebidas', 'Lanches', 'Porções', 'Sobremesas', 'Refeições', 'Saladas', 'Outros'];

export default function ProductForm() {
  const { id } = useParams();
  const isEdit = !!id;
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEdit);
  const [form, setForm] = useState({
    name: '',
    category: 'Lanches',
    price: '',
    estimated_cost: '',
    is_active: true,
    notes: '',
    seasonality: null,
  });

  useEffect(() => {
    if (isEdit) {
      productsApi.get(id).then((res) => {
        const p = res.data;
        setForm({
          name: p.name || '',
          category: p.category || 'Outros',
          price: String(p.price || ''),
          estimated_cost: p.estimated_cost ? String(p.estimated_cost) : '',
          is_active: p.is_active,
          notes: p.notes || '',
          seasonality: p.seasonality || null,
        });
      }).catch(() => {
        toast.error('Erro ao carregar produto');
        navigate('/products');
      }).finally(() => setFetching(false));
    }
  }, [id]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.price) {
      toast.warning('Nome e preço são obrigatórios');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...form,
        price: parseFloat(form.price),
        estimated_cost: form.estimated_cost ? parseFloat(form.estimated_cost) : null,
        seasonality: form.seasonality || null,
      };

      if (isEdit) {
        await productsApi.update(id, payload);
        toast.success('Produto atualizado!');
      } else {
        await productsApi.create(payload);
        toast.success('Produto criado!');
      }
      navigate('/products');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao salvar produto');
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto animate-fade-in">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/products')} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft size={20} className="text-gray-600" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">
            {isEdit ? 'Editar Produto' : 'Novo Produto'}
          </h1>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
            <input className="input-field" value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} required />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Categoria</label>
            <select className="input-field" value={form.category} onChange={(e) => setForm({...form, category: e.target.value})}>
              {CATEGORIES.map((cat) => <option key={cat} value={cat}>{cat}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Preço * (R$)</label>
            <input type="number" step="0.01" min="0" className="input-field" value={form.price} onChange={(e) => setForm({...form, price: e.target.value})} required />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Custo Estimado (R$)</label>
            <input type="number" step="0.01" min="0" className="input-field" value={form.estimated_cost} onChange={(e) => setForm({...form, estimated_cost: e.target.value})} />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select className="input-field" value={form.is_active ? 'active' : 'inactive'} onChange={(e) => setForm({...form, is_active: e.target.value === 'active'})}>
              <option value="active">Ativo</option>
              <option value="inactive">Inativo</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
            <textarea className="input-field" rows={2} value={form.notes} onChange={(e) => setForm({...form, notes: e.target.value})} />
          </div>
        </div>

        <div className="flex items-center gap-3 pt-4 border-t border-gray-100">
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : <Save size={18} />}
            {isEdit ? 'Salvar Alterações' : 'Criar Produto'}
          </button>
          <button type="button" onClick={() => navigate('/products')} className="btn-secondary">Cancelar</button>
        </div>
      </form>
    </div>
  );
}
