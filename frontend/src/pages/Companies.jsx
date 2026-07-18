import React, { useEffect, useMemo, useState } from 'react';
import { Building2, Link2, Plus, Receipt, RefreshCw, Trash2, Users, X } from 'lucide-react';
import { toast } from 'react-toastify';
import { clients, companies, companyAccounts } from '../services/api';

const initialForm = {
  legal_name: '',
  trade_name: '',
  document: '',
  phone: '',
  email: '',
  address: '',
  monthly_limit: '',
  payment_day: '',
  notes: '',
};

const money = (value) => Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
const periodLabel = (month, year) => `${String(month).padStart(2, '0')}/${year}`;

export default function Companies() {
  const now = new Date();
  const [form, setForm] = useState(initialForm);
  const [companyList, setCompanyList] = useState([]);
  const [allClients, setAllClients] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [members, setMembers] = useState([]);
  const [memberToLink, setMemberToLink] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [companiesResponse, clientsResponse, accountsResponse] = await Promise.all([
        companies.list({ status: 'active' }),
        clients.list({ status: 'active' }),
        companyAccounts.list({ month: now.getMonth() + 1, year: now.getFullYear() }),
      ]);
      setCompanyList(companiesResponse.data);
      setAllClients(clientsResponse.data);
      setAccounts(accountsResponse.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const availableClients = useMemo(
    () => allClients.filter((client) => !client.company_id),
    [allClients],
  );

  const updateField = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }));

  const createCompany = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      await companies.create({
        ...form,
        monthly_limit: form.monthly_limit ? Number(form.monthly_limit) : null,
        payment_day: form.payment_day ? Number(form.payment_day) : null,
      });
      toast.success('Empresa cadastrada.');
      setForm(initialForm);
      await load();
    } finally {
      setSaving(false);
    }
  };

  const toggleMembers = async (companyId) => {
    if (expandedId === companyId) {
      setExpandedId(null);
      return;
    }
    const response = await companies.members(companyId);
    setMembers(response.data);
    setExpandedId(companyId);
    setMemberToLink('');
  };

  const linkMember = async (companyId) => {
    if (!memberToLink) return;
    await companies.linkMember(companyId, memberToLink);
    toast.success('Pessoa vinculada à empresa.');
    const response = await companies.members(companyId);
    setMembers(response.data);
    setMemberToLink('');
    await load();
  };

  const unlinkMember = async (companyId, clientId) => {
    await companies.unlinkMember(companyId, clientId);
    toast.success('Pessoa desvinculada.');
    const response = await companies.members(companyId);
    setMembers(response.data);
    await load();
  };

  const createAccount = async (companyId) => {
    await companyAccounts.create({ company_id: companyId, month: now.getMonth() + 1, year: now.getFullYear() });
    toast.success('Conta corporativa criada para o mês atual.');
    await load();
  };

  const closeAccount = async (id) => {
    await companyAccounts.close(id);
    toast.success('Conta corporativa fechada e consolidada.');
    await load();
  };

  const payAccount = async (id) => {
    await companyAccounts.pay(id, { payment_method: 'pix' });
    toast.success('Pagamento corporativo registrado.');
    await load();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-medium text-primary-600">Gestão corporativa</p>
          <h2 className="text-2xl font-bold text-gray-900">Empresas e pessoas vinculadas</h2>
          <p className="mt-1 text-sm text-gray-500">Permita que uma empresa centralize o pagamento das contas mensais da sua equipe.</p>
        </div>
        <button onClick={load} className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
          <RefreshCw size={16} /> Atualizar
        </button>
      </div>

      <div className="grid gap-6 xl:grid-cols-[380px,1fr]">
        <form onSubmit={createCompany} className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="mb-5 flex items-center gap-3">
            <div className="rounded-xl bg-primary-50 p-3 text-primary-600"><Building2 size={22} /></div>
            <div><h3 className="font-semibold text-gray-900">Cadastrar empresa</h3><p className="text-xs text-gray-500">O CNPJ identifica o pagador corporativo.</p></div>
          </div>
          <div className="space-y-3">
            <input required name="legal_name" value={form.legal_name} onChange={updateField} placeholder="Razão social *" className="input" />
            <input name="trade_name" value={form.trade_name} onChange={updateField} placeholder="Nome fantasia" className="input" />
            <input required name="document" value={form.document} onChange={updateField} placeholder="CNPJ *" className="input" />
            <div className="grid grid-cols-2 gap-3"><input name="phone" value={form.phone} onChange={updateField} placeholder="Telefone" className="input" /><input name="email" type="email" value={form.email} onChange={updateField} placeholder="E-mail" className="input" /></div>
            <input name="address" value={form.address} onChange={updateField} placeholder="Endereço" className="input" />
            <div className="grid grid-cols-2 gap-3"><input name="monthly_limit" type="number" min="0" step="0.01" value={form.monthly_limit} onChange={updateField} placeholder="Limite mensal" className="input" /><input name="payment_day" type="number" min="1" max="31" value={form.payment_day} onChange={updateField} placeholder="Dia de pagamento" className="input" /></div>
            <textarea name="notes" value={form.notes} onChange={updateField} placeholder="Observações" rows="3" className="input resize-none" />
          </div>
          <button disabled={saving} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-700 disabled:opacity-50"><Plus size={17} /> {saving ? 'Salvando...' : 'Cadastrar empresa'}</button>
        </form>

        <div className="space-y-4">
          {loading && <div className="rounded-2xl border border-gray-200 bg-white p-10 text-center text-sm text-gray-500">Carregando empresas...</div>}
          {!loading && companyList.length === 0 && <div className="rounded-2xl border border-dashed border-gray-300 bg-white p-10 text-center"><Building2 className="mx-auto mb-3 text-gray-400" /><p className="font-medium text-gray-700">Nenhuma empresa cadastrada</p><p className="mt-1 text-sm text-gray-500">Cadastre a primeira empresa para habilitar o faturamento agrupado.</p></div>}
          {companyList.map((company) => {
            const account = accounts.find((item) => item.company_id === company.id);
            return <div key={company.id} className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="flex gap-3"><div className="rounded-xl bg-emerald-50 p-3 text-emerald-600"><Building2 size={22} /></div><div><h3 className="font-semibold text-gray-900">{company.trade_name || company.legal_name}</h3><p className="text-sm text-gray-500">{company.legal_name} · CNPJ {company.document}</p><p className="mt-1 text-xs text-gray-500">{company.member_count} pessoa(s) vinculada(s) · Limite {company.monthly_limit ? money(company.monthly_limit) : 'não definido'}</p></div></div>
                <button onClick={() => toggleMembers(company.id)} className="inline-flex items-center justify-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"><Users size={16} /> {expandedId === company.id ? 'Ocultar pessoas' : 'Gerenciar pessoas'}</button>
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-gray-100 pt-4">
                {account ? <><span className={`rounded-full px-3 py-1 text-xs font-semibold ${account.status === 'paid' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>{periodLabel(account.month, account.year)} · {account.status} · {money(account.total)}</span>{account.status === 'open' && <button onClick={() => closeAccount(account.id)} className="rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-semibold text-white">Fechar e consolidar</button>}{['closed', 'confirmed_by_biometrics'].includes(account.status) && <button onClick={() => payAccount(account.id)} className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white">Registrar pagamento</button>}</> : <button onClick={() => createAccount(company.id)} className="inline-flex items-center gap-2 rounded-lg border border-primary-200 bg-primary-50 px-3 py-1.5 text-xs font-semibold text-primary-700"><Receipt size={15} /> Criar conta de {periodLabel(now.getMonth() + 1, now.getFullYear())}</button>}
              </div>
              {expandedId === company.id && <div className="mt-4 rounded-xl bg-gray-50 p-4"><div className="mb-3 flex items-center justify-between"><h4 className="text-sm font-semibold text-gray-800">Pessoas da empresa</h4><button onClick={() => setExpandedId(null)} className="text-gray-400 hover:text-gray-700"><X size={16} /></button></div>{members.length === 0 ? <p className="text-sm text-gray-500">Nenhuma pessoa vinculada.</p> : <div className="space-y-2">{members.map((member) => <div key={member.id} className="flex items-center justify-between rounded-lg bg-white px-3 py-2 text-sm"><span><b>{member.name}</b><span className="ml-2 text-gray-500">{member.phone}</span></span><button onClick={() => unlinkMember(company.id, member.id)} className="text-red-500 hover:text-red-700" title="Desvincular"><Trash2 size={16} /></button></div>)}</div>}<div className="mt-3 flex gap-2"><select value={memberToLink} onChange={(event) => setMemberToLink(event.target.value)} className="input flex-1"><option value="">Selecionar pessoa já cadastrada...</option>{availableClients.map((client) => <option key={client.id} value={client.id}>{client.name} — {client.phone}</option>)}</select><button onClick={() => linkMember(company.id)} disabled={!memberToLink} className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"><Link2 size={16} /> Vincular</button></div></div>}
            </div>;
          })}
        </div>
      </div>
    </div>
  );
}
