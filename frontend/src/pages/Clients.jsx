import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { clients as clientsApi } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'react-toastify';
import { Plus, Search, Edit, UserCheck, UserX, Phone, Building, DollarSign, X } from 'lucide-react';
import EmptyState from '../components/EmptyState';
import BiometricEnrollModal from '../components/BiometricEnrollModal';

export default function Clients() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [showBioModal, setShowBioModal] = useState(false);
  const [form, setForm] = useState({ name:'', document:'', phone:'', company_sector:'', monthly_limit:'', notes:'', is_account_client: false });
  const [createdClient, setCreatedClient] = useState(null);
  const { hasRole } = useAuth();

  const loadClients = async () => {
    try {
      const params = {};
      if (search) params.phoneOrName = search;
      const res = await clientsApi.list(params);
      setClients(res.data);
    } catch (err) {
      toast.error('Erro ao carregar clientes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadClients(); }, []);

  const createClient = async (e) => {
    e.preventDefault();
    if(!form.name || !form.phone){ toast.warning('Preencha nome e telefone'); return; }
    try {
      const res = await clientsApi.create({
        name: form.name,
        document: form.document || null,
        phone: form.phone,
        company_sector: form.company_sector || null,
        monthly_limit: form.monthly_limit ? parseFloat(form.monthly_limit) : 0,
        notes: form.notes || null,
        is_account_client: !!form.is_account_client,
      });
      if (res.data?.id) setCreatedClient(res.data);
      toast.success('Cliente cadastrado!');
      setShowModal(false);
      setForm({ name:'', document:'', phone:'', company_sector:'', monthly_limit:'', notes:'', is_account_client: false });
      loadClients();
      if (res.data?.is_account_client) setShowBioModal(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao cadastrar cliente');
    }
  };

  const toggleStatus = async (client) => {
    try {
      const newStatus = client.status === 'active' ? 'inactive' : 'active';
      await clientsApi.update(client.id, { status: newStatus });
      toast.success(`Cliente ${newStatus === 'active' ? 'ativado' : 'inativado'} com sucesso`);
      loadClients();
    } catch (err) {
      toast.error('Erro ao alterar status');
    }
  };

  const StatusBadge = ({ status }) => {
    if (status === 'active') return <span className="badge-green">Ativo</span>;
    return <span className="badge-red">Inativo</span>;
  };

  const enrolledToast = () => {
    if (!createdClient) return;
    toast.success('Digital cadastrada para este cliente.');
    setCreatedClient(null);
    setShowBioModal(false);
  };

  return (
    <div className="animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Clientes</h1>
          <p className="text-gray-500 text-sm mt-1">{clients.length} cliente(s) cadastrado(s)</p>
        </div>
        {hasRole('admin') && (
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <Plus size={18} />
            Novo Cliente
          </button>
        )}
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            className="input-field pl-10"
            placeholder="Buscar por nome ou telefone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadClients()}
          />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-500"></div>
        </div>
      ) : clients.length === 0 ? (
        <div className="card text-center py-12">
          <EmptyState title="Nenhum cliente encontrado" description="Cadastre clientes para começar a usar o sistema." />
          {hasRole('admin') && (
            <button onClick={() => setShowModal(true)} className="btn-primary inline-flex items-center gap-2 mt-4">
              <Plus size={16} />
              Cadastrar Cliente
            </button>
          )}
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 bg-white">
            <thead className="bg-gray-50">
              <tr>
                <th className="table-header">Nome</th>
                <th className="table-header hidden md:table-cell">Documento</th>
                <th className="table-header">Telefone</th>
                <th className="table-header hidden lg:table-cell">Setor</th>
                <th className="table-header">Limite</th>
                <th className="table-header">Status</th>
                <th className="table-header text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {clients.map((client) => (
                <tr key={client.id} className="hover:bg-gray-50 transition-colors">
                  <td className="table-cell font-medium text-gray-800">{client.name}</td>
                  <td className="table-cell hidden md:table-cell text-gray-500">{client.document || '-'}</td>
                  <td className="table-cell">
                    <span className="flex items-center gap-1">
                      <Phone size={14} className="text-gray-400" />
                      {client.phone}
                    </span>
                  </td>
                  <td className="table-cell hidden lg:table-cell">
                    {client.company_sector ? (
                      <span className="flex items-center gap-1">
                        <Building size={14} className="text-gray-400" />
                        {client.company_sector}
                      </span>
                    ) : '-'}
                  </td>
                  <td className="table-cell">
                    {client.monthly_limit ? (
                      <span className="flex items-center gap-1">
                        <DollarSign size={14} className="text-gray-400" />
                        R$ {client.monthly_limit.toFixed(2)}
                      </span>
                    ) : '-'}
                  </td>
                  <td className="table-cell">
                    <StatusBadge status={client.status} />
                  </td>
                  <td className="table-cell text-right">
                    <div className="flex items-center justify-end gap-2">
                      {hasRole('admin') && (
                        <>
                          <Link
                            to={`/clients/${client.id}/edit`}
                            className="p-1.5 hover:bg-blue-50 rounded-lg text-blue-600 transition-colors"
                            title="Editar"
                          >
                            <Edit size={16} />
                          </Link>
                          <button
                            onClick={() => toggleStatus(client)}
                            className={`p-1.5 rounded-lg transition-colors ${
                              client.status === 'active'
                                ? 'hover:bg-red-50 text-red-600'
                                : 'hover:bg-green-50 text-green-600'
                            }`}
                            title={client.status === 'active' ? 'Inativar' : 'Ativar'}
                          >
                            {client.status === 'active' ? <UserX size={16} /> : <UserCheck size={16} />}
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowModal(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-primary-50 rounded-xl"><Plus size={20} className="text-primary-600"/></div>
                <div>
                  <h3 className="font-semibold text-gray-800">Novo Cliente</h3>
                  <p className="text-xs text-gray-500">Cadastro rápido pelo fluxo do sistema.</p>
                </div>
              </div>
              <button onClick={() => setShowModal(false)} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500"><X size={18}/></button>
            </div>
            <form onSubmit={createClient} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome</label>
                <input className="input-field" value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Telefone</label>
                <input className="input-field" value={form.phone} onChange={(e) => setForm({...form, phone: e.target.value})} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Documento</label>
                <input className="input-field" value={form.document} onChange={(e) => setForm({...form, document: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Setor</label>
                <input className="input-field" value={form.company_sector} onChange={(e) => setForm({...form, company_sector: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Limite Mensal</label>
                <input type="number" className="input-field" value={form.monthly_limit} onChange={(e) => setForm({...form, monthly_limit: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Obs</label>
                <textarea className="input-field" rows={2} value={form.notes} onChange={(e) => setForm({...form, notes: e.target.value})} />
              </div>
              <div className="flex items-center gap-2">
                <input id="is_account_client" type="checkbox" checked={!!form.is_account_client} onChange={(e) => setForm({...form, is_account_client: e.target.checked})} />
                <label htmlFor="is_account_client" className="text-sm text-gray-700">Cliente de conta</label>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" className="btn-primary flex-1">Salvar</button>
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1">Cancelar</button>
              </div>
            </form>
          </div>
        </div>
      )}
      {showBioModal && createdClient ? (
        <BiometricEnrollModal
          clientId={createdClient.id}
          clientName={createdClient.name}
          onClose={() => { setShowBioModal(false); setCreatedClient(null); }}
          onEnrolled={enrolledToast}
        />
      ) : null}
    </div>
  );
}
