import React, { useState, useEffect } from 'react';
import { audit as auditApi } from '../services/api';
import { toast } from 'react-toastify';
import { History, Search, Filter, Clock, User, Activity, FileText } from 'lucide-react';

const ACTION_LABELS = {
  create: 'Criação',
  update: 'Alteração',
  delete: 'Exclusão',
  cancel: 'Cancelamento',
  login: 'Login',
  login_failed: 'Falha Login',
  logout: 'Logout',
  close: 'Fechamento',
  sign: 'Assinatura',
  pay: 'Pagamento',
};

const ACTION_COLORS = {
  create: 'bg-green-100 text-green-700',
  update: 'bg-blue-100 text-blue-700',
  delete: 'bg-red-100 text-red-700',
  cancel: 'bg-red-100 text-red-700',
  login: 'bg-gray-100 text-gray-700',
  login_failed: 'bg-red-100 text-red-700',
  close: 'bg-purple-100 text-purple-700',
  sign: 'bg-indigo-100 text-indigo-700',
  pay: 'bg-green-100 text-green-700',
};

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterEntity, setFilterEntity] = useState('');
  const [filterAction, setFilterAction] = useState('');

  const loadLogs = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterEntity) params.entity_type = filterEntity;
      if (filterAction) params.action = filterAction;
      const res = await auditApi.list(params);
      setLogs(res.data);
    } catch {
      toast.error('Erro ao carregar logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadLogs(); }, []);

  return (
    <div className="animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Auditoria</h1>
          <p className="text-gray-500 text-sm mt-1">{logs.length} registro(s) de auditoria</p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <select className="input-field max-w-xs" value={filterEntity} onChange={(e) => setFilterEntity(e.target.value)}>
          <option value="">Todas entidades</option>
          <option value="client">Cliente</option>
          <option value="product">Produto</option>
          <option value="order">Pedido</option>
          <option value="monthly_account">Conta Mensal</option>
          <option value="signature">Assinatura</option>
          <option value="payment">Pagamento</option>
          <option value="user">Usuário</option>
        </select>
        <select className="input-field max-w-xs" value={filterAction} onChange={(e) => setFilterAction(e.target.value)}>
          <option value="">Todas ações</option>
          {Object.entries(ACTION_LABELS).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
        <button onClick={loadLogs} className="btn-secondary flex items-center gap-2">
          <Filter size={16} />
          Filtrar
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-500"></div>
        </div>
      ) : logs.length === 0 ? (
        <div className="card text-center py-12">
          <History className="mx-auto text-gray-300" size={48} />
          <p className="text-gray-500 mt-4">Nenhum registro de auditoria encontrado</p>
        </div>
      ) : (
        <div className="space-y-3">
          {logs.map((log) => (
            <div key={log.id} className="card animate-slide-in">
              <div className="flex items-start gap-4">
                <div className={`p-2 rounded-lg flex-shrink-0 ${ACTION_COLORS[log.action] || 'bg-gray-100'}`}>
                  <Activity size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ACTION_COLORS[log.action] || 'bg-gray-100 text-gray-700'}`}>
                      {ACTION_LABELS[log.action] || log.action}
                    </span>
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {log.entity_type}
                      {log.entity_id && <span className="text-gray-400"> #{log.entity_id}</span>}
                    </span>
                    <span className="text-xs text-gray-400 flex items-center gap-1">
                      <Clock size={12} />
                      {new Date(log.timestamp).toLocaleString('pt-BR')}
                    </span>
                  </div>

                  {log.details && (
                    <p className="text-sm text-gray-600 mt-1">{log.details}</p>
                  )}

                  <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-gray-400">
                    {log.username && (
                      <span className="flex items-center gap-1">
                        <User size={12} />
                        {log.username}
                      </span>
                    )}
                    {log.ip_address && <span>IP: {log.ip_address}</span>}
                  </div>

                  {(log.before_state || log.after_state) && (
                    <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                      {log.before_state && (
                        <div>
                          <span className="text-red-600 font-medium">Antes: </span>
                          {JSON.stringify(log.before_state)}
                        </div>
                      )}
                      {log.after_state && (
                        <div>
                          <span className="text-green-600 font-medium">Depois: </span>
                          {JSON.stringify(log.after_state)}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
