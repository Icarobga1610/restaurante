import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { clients as clientsApi, companies as companiesApi } from '../services/api';
import { toast } from 'react-toastify';
import { Save, ArrowLeft, Fingerprint } from 'lucide-react';
import BiometricEnrollModal from '../components/BiometricEnrollModal';

export default function ClientForm() {
  const { id } = useParams();
  const isEdit = !!id;
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEdit);
  const [savedClient, setSavedClient] = useState(null);
  const [showBiometricModal, setShowBiometricModal] = useState(false);
  const [enrollAfterSave, setEnrollAfterSave] = useState(false);
  const [companies, setCompanies] = useState([]);
  const [form, setForm] = useState({
    name: '',
    document: '',
    phone: '',
    company_sector: '',
    monthly_limit: '',
    is_account_client: false,
    payment_day: '',
    notes: '',
    status: 'active',
    company_id: '',
  });

  useEffect(() => {
    companiesApi.list({ status: 'active' }).then((res) => setCompanies(res.data)).catch(() => {});
    if (isEdit) {
      clientsApi.get(id).then((res) => {
        const c = res.data;
        setForm({
          name: c.name || '',
          document: c.document || '',
          phone: c.phone || '',
          company_sector: c.company_sector || '',
          monthly_limit: c.monthly_limit ? String(c.monthly_limit) : '',
          is_account_client: !!c.is_account_client,
          payment_day: c.payment_day ? String(c.payment_day) : '',
          notes: c.notes || '',
          status: c.status || 'active',
          company_id: c.company_id ? String(c.company_id) : '',
        });
        setSavedClient(c);
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
      // `status` is only accepted by ClientUpdate (edit), not ClientCreate.
      // Sending it on create triggers extra="forbid" (422) and the client
      // is never created. Strip it from the create payload.
      const { status, ...rest } = form;
      const payload = {
        ...rest,
        company_id: form.company_id ? parseInt(form.company_id, 10) : null,
        monthly_limit: form.monthly_limit ? parseFloat(form.monthly_limit) : null,
        payment_day: form.payment_day ? parseInt(form.payment_day, 10) : null,
      };

      if (isEdit) {
        const res = await clientsApi.update(id, payload);
        setSavedClient(res.data);
        toast.success('Cliente atualizado com sucesso!');
      } else {
        const res = await clientsApi.create(payload);
        setSavedClient(res.data);
        toast.success('Cliente criado com sucesso!');
        if (enrollAfterSave) {
          setShowBiometricModal(true);
          return;
        }
      }
      navigate('/clients');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao salvar cliente');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm({ ...form, [field]: value });
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Empresa pagadora</label>
            <select className="input-field" value={form.company_id} onChange={handleChange('company_id')}>
              <option value="">Pagamento individual</option>
              {companies.map((company) => <option key={company.id} value={company.id}>{company.trade_name || company.legal_name}</option>)}
            </select>
            <p className="mt-1 text-xs text-gray-400">A conta desta pessoa poderá ser consolidada no faturamento da empresa.</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Limite Mensal (R$)</label>
            <input type="number" step="0.01" min="0" className="input-field" value={form.monthly_limit} onChange={handleChange('monthly_limit')} placeholder="Opcional" />
          </div>

          <div className="md:col-span-2 flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2">
            <input
              id="is_account_client"
              type="checkbox"
              checked={!!form.is_account_client}
              onChange={(e) => {
                setForm({ ...form, is_account_client: e.target.checked });
                if (e.target.checked) setEnrollAfterSave(true);
              }}
            />
            <label htmlFor="is_account_client" className="text-sm text-gray-700">
              Cliente de conta mensal
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Dia de pagamento</label>
            <input
              type="number"
              min="1"
              max="31"
              className="input-field"
              value={form.payment_day}
              onChange={handleChange('payment_day')}
              placeholder="Ex: 5"
            />
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

        {isEdit ? (
          <div className="rounded-lg border border-primary-100 bg-primary-50 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-white rounded-lg">
                <Fingerprint size={20} className="text-primary-600" />
              </div>
              <div>
                <p className="font-medium text-gray-800">Digital do cliente</p>
                <p className="text-sm text-gray-500">
                  Cadastre ou atualize a digital usada na confirmação de contas mensais.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setShowBiometricModal(true)}
              className="btn-secondary flex items-center justify-center gap-2"
            >
              <Fingerprint size={16} />
              Cadastrar Digital
            </button>
          </div>
        ) : (
          <div className="rounded-lg border border-primary-100 bg-primary-50 p-4">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                className="mt-1"
                checked={enrollAfterSave}
                onChange={(e) => setEnrollAfterSave(e.target.checked)}
              />
              <span>
                <span className="block font-medium text-gray-800">Cadastrar digital depois de salvar</span>
                <span className="block text-sm text-gray-500">
                  Após criar o cliente, o sistema abrirá a captura da digital.
                </span>
              </span>
            </label>
          </div>
        )}

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

      {showBiometricModal && savedClient ? (
        <BiometricEnrollModal
          clientId={savedClient.id}
          clientName={savedClient.name}
          onClose={() => {
            setShowBiometricModal(false);
            if (!isEdit) navigate('/clients');
          }}
          onEnrolled={() => {
            toast.success('Digital cadastrada para este cliente.');
            setShowBiometricModal(false);
            if (!isEdit) navigate('/clients');
          }}
        />
      ) : null}
    </div>
  );
}
