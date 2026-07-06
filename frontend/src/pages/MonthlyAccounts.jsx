import React, { useState, useEffect } from 'react';
import { monthlyAccounts as maApi, clients as clientsApi } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';
import {
  FileText, Plus, Search, Filter, CheckCircle, DollarSign,
  Fingerprint, AlertTriangle, Eye, XCircle, Calendar, User, X
} from 'lucide-react';

const STATUS_MAP = {
  open: { label: 'Em Aberto', class: 'badge-yellow' },
  closed: { label: 'Fechada', class: 'badge-blue' },
  confirmed_by_biometrics: { label: 'Confirmada por Biometria', class: 'badge-purple' },
  paid: { label: 'Paga', class: 'badge-green' },
  overdue: { label: 'Vencida', class: 'badge-red' },
};

export default function MonthlyAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [filterClient, setFilterClient] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [showCreateAccount, setShowCreateAccount] = useState(false);
  const [createAccount, setCreateAccount] = useState({ client_id:'', month: new Date().getMonth()+1, year: new Date().getFullYear() });
  const [showCreateClient, setShowCreateClient] = useState(false);
  const [createClient, setCreateClient] = useState({ name:'', document:'', phone:'', company_sector:'', monthly_limit:'', notes:'' });
  const { hasRole } = useAuth();
  const navigate = useNavigate();

  const loadData = async () => {
    try {
      const params = {};
      if (filterClient) params.client_id = filterClient;
      if (filterStatus) params.status = filterStatus;
      const [accountsRes, clientsRes] = await Promise.all([
        maApi.list(params),
        clientsApi.list({ limit: 200 }),
      ]);
      setAccounts(accountsRes.data);
      setClients(clientsRes.data);
    } catch {
      toast.error('Erro ao carregar contas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleCreateAccount = async (e) => {
    e.preventDefault();
    if (!createAccount.client_id) { toast.warning('Selecione um cliente'); return; }
    try {
      await maApi.create(createAccount);
      toast.success('Conta mensal criada!');
      setShowCreateAccount(false);
      setCreateAccount({ client_id:'', month: new Date().getMonth()+1, year: new Date().getFullYear() });
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao criar conta');
    }
  };

  const handleCreateClient = async (e) => {
    e.preventDefault();
    if (!createClient.name || !createClient.phone) { toast.warning('Preencha nome e telefone'); return; }
    try {
      const res = await clientsApi.create({
        name: createClient.name,
        document: createClient.document || null,
        phone: createClient.phone,
        company_sector: createClient.company_sector || null,
        monthly_limit: createClient.monthly_limit ? parseFloat(createClient.monthly_limit) : 0,
        notes: createClient.notes || null,
      });
      toast.success('Cliente cadastrado!');
      setShowCreateClient(false);
      setCreateClient({ name:'', document:'', phone:'', company_sector:'', monthly_limit:'', notes:'' });
      if (res.data?.id) {
        setCreateAccount({ ...createAccount, client_id: String(res.data.id) });
      }
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao cadastrar cliente');
    }
  };

  const closeAccount = async (account) => {
    if (!confirm(`Fechar conta mensal de ${account.client_name} para ${account.month}/${account.year}?`)) return;
    try {
      await maApi.close(account.id, {});
      toast.success('Conta fechada com sucesso!');
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao fechar conta');
    }
  };

  const confirmBiometric = (account) => {
    navigate('/biometric', { state: { account } });
  };

  const payAccount = async (account) => {
    if (account.client_is_account_client) {
      navigate('/biometric', { state: { account, autoPay: true } });
      return;
    }
    if (!confirm(`Registrar pagamento da conta de ${account.client_name} no valor de R$ ${account.total.toFixed(2)}?`)) return;
    try {
      const method = 'pix';
      await maApi.pay(account.id, { payment_method: method });
      toast.success('Pagamento registrado!');
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao registrar pagamento');
    }
  };

  const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

  return (
    <div className="animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Contas Mensais</h1>
          <p className="text-gray-500 text-sm mt-1">{accounts.length} conta(s)</p>
        </div>
        {hasRole('admin', 'financial') && (
          <button onClick={() => setShowCreateAccount(true)} className="btn-primary flex items-center gap-2">
            <Plus size={18} />
            Nova Conta
          </button>
        )}
      </div>

      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <select className="input-field max-w-xs" value={filterClient} onChange={(e) => setFilterClient(e.target.value)}>
          <option value="">Todos clientes</option>
          {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select className="input-field max-w-xs" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">Todos status</option>
          {Object.entries(STATUS_MAP).map(([key, val]) => (
            <option key={key} value={key}>{val.label}</option>
          ))}
        </select>
        <button onClick={loadData} className="btn-secondary flex items-center gap-2">
          <Filter size={16} />
          Filtrar
        </button>
      </div>

      <div className="space-y-3">
        {accounts.map((acc) => (
          <div key={acc.id} className="card animate-slide-in">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex items-center gap-4 flex-wrap">
                <span className="text-sm font-bold text-gray-400">#{acc.id}</span>
                <span className="font-medium text-gray-800">{acc.client_name}</span>
                <span className="flex items-center gap-1 text-sm text-gray-500">
                  <Calendar size={14} />
                  {months[acc.month - 1]} {acc.year}
                </span>
                <span className={STATUS_MAP[acc.status]?.class || 'badge-gray'}>
                  {STATUS_MAP[acc.status]?.label || acc.status}
                </span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xl font-bold text-gray-800">R$ {acc.total.toFixed(2)}</span>
                <button onClick={() => setSelected(selected === acc.id ? null : acc.id)} className="p-1.5 hover:bg-gray-100 rounded-lg">
                  <Eye size={16} className="text-gray-400" />
                </button>
              </div>
            </div>

            {selected === acc.id && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                {(acc.items || []).length > 0 ? (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-600 mb-2">Pedidos incluídos:</p>
                    <div className="space-y-1">
                      {acc.items.map((item) => (
                        <div key={item.id} className="flex justify-between text-sm bg-gray-50 px-3 py-2 rounded-lg">
                          <span className="text-gray-600">Pedido #{item.order_id}</span>
                          <span className="font-medium">R$ {item.order_total.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 mb-3">Nenhum pedido incluído ainda</p>
                )}

                <div className="flex flex-wrap gap-2">
                  {hasRole('admin', 'financial') && acc.status === 'open' && (
                    <button onClick={() => closeAccount(acc)} className="btn-primary flex items-center gap-1 text-sm py-1.5 px-3">
                      <CheckCircle size={14} />
                      Fechar Conta
                    </button>
                  )}
                  {hasRole('admin', 'financial') && (acc.status === 'closed' || acc.status === 'confirmed_by_biometrics') && (
                    <button onClick={() => confirmBiometric(acc)} className="btn-secondary flex items-center gap-1 text-sm py-1.5 px-3">
                      <Fingerprint size={14} />
                      Confirmar Biometria
                    </button>
                  )}
                  {hasRole('admin', 'financial') && acc.status === 'confirmed_by_biometrics' && (
                    <button onClick={() => payAccount(acc)} className="btn-success flex items-center gap-1 text-sm py-1.5 px-3">
                      <DollarSign size={14} />
                      Registrar Pagamento
                    </button>
                  )}
                </div>

                <div className="mt-3 text-xs text-gray-400 space-y-1">
                  {acc.closed_at && <p>Fechado em: {new Date(acc.closed_at).toLocaleString('pt-BR')} por {acc.closed_by_name}</p>}
                  {acc.paid_at && <p>Pago em: {new Date(acc.paid_at).toLocaleString('pt-BR')} por {acc.paid_by_name}</p>}
                  {acc.notes && <p>Obs: {acc.notes}</p>}
                </div>
              </div>
            )}
          </div>
        ))}

        {!loading && accounts.length === 0 && (
          <div className="card text-center py-12">
            <FileText className="mx-auto text-gray-300" size={48} />
            <p className="text-gray-500 mt-4">Nenhuma conta mensal encontrada</p>
          </div>
        )}
      </div>

      <button
        onClick={() => setShowCreateClient(true)}
        className="fixed bottom-6 right-6 btn-primary flex items-center gap-2 shadow-lg"
      >
        <Plus size={18} />
        Cliente
      </button>

      {showCreateAccount && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowCreateAccount(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-primary-50 rounded-xl"><FileText size={20} className="text-primary-600"/></div>
                <div>
                  <h3 className="font-semibold text-gray-800">Nova Conta Mensal</h3>
                  <p className="text-xs text-gray-500">Selecione cliente e período.</p>
                </div>
              </div>
              <button onClick={() => setShowCreateAccount(false)} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500"><X size={18}/></button>
            </div>
            <form onSubmit={handleCreateAccount} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cliente</label>
                <select className="input-field" value={createAccount.client_id} onChange={(e) => setCreateAccount({...createAccount, client_id: e.target.value})}>
                  <option value="">Selecione...</option>
                  {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Mês</label>
                  <select className="input-field" value={createAccount.month} onChange={(e) => setCreateAccount({...createAccount, month: parseInt(e.target.value)})}>
                    {months.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ano</label>
                  <input type="number" className="input-field" value={createAccount.year} onChange={(e) => setCreateAccount({...createAccount, year: parseInt(e.target.value)})} />
                </div>
              </div>
              <div className="flex gap-3 mt-6">
                <button type="submit" className="btn-primary flex-1">Criar</button>
                <button type="button" onClick={() => setShowCreateAccount(false)} className="btn-secondary flex-1">Cancelar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showCreateClient && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowCreateClient(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-primary-50 rounded-xl"><User size={20} className="text-primary-600"/></div>
                <div>
                  <h3 className="font-semibold text-gray-800">Novo Cliente</h3>
                  <p className="text-xs text-gray-500">Cadastro rápido pelo fluxo do sistema.</p>
                </div>
              </div>
              <button onClick={() => setShowCreateClient(false)} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500"><X size={18}/></button>
            </div>
            <form onSubmit={handleCreateClient} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome</label>
                <input className="input-field" value={createClient.name} onChange={(e) => setCreateClient({...createClient, name: e.target.value})} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Telefone</label>
                <input className="input-field" value={createClient.phone} onChange={(e) => setCreateClient({...createClient, phone: e.target.value})} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Documento</label>
                <input className="input-field" value={createClient.document} onChange={(e) => setCreateClient({...createClient, document: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Setor</label>
                <input className="input-field" value={createClient.company_sector} onChange={(e) => setCreateClient({...createClient, company_sector: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Limite Mensal</label>
                <input type="number" className="input-field" value={createClient.monthly_limit} onChange={(e) => setCreateClient({...createClient, monthly_limit: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Obs</label>
                <textarea className="input-field" rows={2} value={createClient.notes} onChange={(e) => setCreateClient({...createClient, notes: e.target.value})} />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" className="btn-primary flex-1">Salvar</button>
                <button type="button" onClick={() => setShowCreateClient(false)} className="btn-secondary flex-1">Cancelar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
