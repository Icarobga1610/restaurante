import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { clients as clientsApi } from '../services/api';
import { toast } from 'react-toastify';
import { Save, ArrowLeft, User } from 'lucide-react';

export default function ClientForm() {
  const { id } = useParams();
  const isEdit = !!id;
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEdit);
  const [form, setForm] = useState({
    name: '',
    document: '',
    phone: '',
    company_sector: '',
    monthly_limit: '',
    notes: '',
    status: 'active',
  });

  useEffect(() => {
    if (isEdit) {
      clientsApi.get(id).then((res) => {
        const c = res.data;
        setForm({
          name: c.name || '',
          document: c.document || '',
          phone: c.phone || '',
          company_sector: c.company_sector || '',
          monthly_limit: c.monthly_limit ? String(c.monthly_limit) : '',
          notes: c.notes || '',
          status: c.status || 'active',
        });
      }).catch(() => {
        toast.error('Erro ao carregar cliente');
        navigate('/clients');
      }).finally(() => setFetching(false));
    }
  }, [id]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.phone) {
      toast.warning('Nome e telefone são obrigatórios');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...form,
        monthly_limit: form.monthly_limit ? parseFloat(form.monthly_limit) : null,
      };

      if (isEdit) {
        await clientsApi.update(id, payload);
        toast.success('Cliente atualizado com sucesso!');
      } else {
        await clientsApi.create(payload);
        toast.success('Cliente criado com sucesso!');
      }
      navigate('/clients');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao salvar cliente');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field) => (e) => {
    setForm({ ...form, [field]: e.target.value });
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
        <button onClick={() => navigate('/clients')} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft size={20} className="text-gray-600" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">
            {isEdit ? 'Editar Cliente' : 'Novo Cliente'}
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            {isEdit ? 'Altere os dados do cliente' : 'Preencha os dados para cadastrar'}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
            <input className="input-field" value={form.name} onChange={handleChange('name')} placeholder="Nome completo" required />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">CPF/Documento</label>
            <input className="input-field" value={form.document} onChange={handleChange('document')} placeholder="Apenas números" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Telefone *</label>
            <input className="input-field" value={form.phone} onChange={handleChange('phone')} placeholder="(11) 99999-9999" required />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Empresa/Setor</label>
            <input className="input-field" value={form.company_sector} onChange={handleChange('company_sector')} placeholder="Ex: Alimentação" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Limite Mensal (R$)</label>
            <input type="number" step="0.01" min="0" className="input-field" value={form.monthly_limit} onChange={handleChange('monthly_limit')} placeholder="Opcional" />
          </div>

          {isEdit && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select className="input-field" value={form.status} onChange={handleChange('status')}>
                <option value="active">Ativo</option>
                <option value="inactive">Inativo</option>
              </select>
            </div>
          )}

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
            <textarea className="input-field" rows={3} value={form.notes} onChange={handleChange('notes')} placeholder="Observações sobre o cliente..." />
          </div>
        </div>

        <div className="flex items-center gap-3 pt-4 border-t border-gray-100">
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <Save size={18} />
            )}
            {isEdit ? 'Salvar Alterações' : 'Cadastrar Cliente'}
          </button>
          <button type="button" onClick={() => navigate('/clients')} className="btn-secondary">
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}
