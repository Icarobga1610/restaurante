import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { orders as ordersApi, clients as clientsApi } from '../services/api';
import { toast } from 'react-toastify';
import { Plus, Search, Filter, Eye, XCircle } from 'lucide-react';

const STATUS_MAP = {
  open: { label: 'Aberto', class: 'badge-yellow' },
  confirmed: { label: 'Confirmado', class: 'badge-blue' },
  cancelled: { label: 'Cancelado', class: 'badge-red' },
  invoiced: { label: 'Faturado', class: 'badge-purple' },
  paid: { label: 'Pago', class: 'badge-green' },
  in_preparation: { label: 'Em preparo', class: 'badge-yellow' },
  ready: { label: 'Pronto', class: 'badge-green' },
};

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterClient, setFilterClient] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [expanded, setExpanded] = useState(null);

  const loadData = async () => {
    try {
      const params = {};
      if (filterClient) params.client_id = filterClient;
      if (filterStatus) params.status = filterStatus;
      const [ordersRes, clientsRes] = await Promise.all([
        ordersApi.list(params),
        clientsApi.list({ limit: 200 }),
      ]);
      setOrders(ordersRes.data);
      setClients(clientsRes.data);
    } catch {
      toast.error('Erro ao carregar pedidos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const cancelOrder = async (order) => {
    if (!confirm(`Cancelar pedido #${order.id}?`)) return;
    try {
      await ordersApi.update(order.id, { status: 'cancelled' });
      toast.success('Pedido cancelado');
      loadData();
    } catch {
      toast.error('Erro ao cancelar pedido');
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Pedidos</h1>
          <p className="text-gray-500 text-sm mt-1">{orders.length} pedido(s)</p>
        </div>
        <Link to="/orders/new" className="btn-primary flex items-center gap-2">
          <Plus size={18} />
          Novo Pedido
        </Link>
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

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-500"></div>
        </div>
      ) : orders.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">Nenhum pedido encontrado</p>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map((order) => (
            <div key={order.id} className="card animate-slide-in">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 flex-wrap">
                  <span className="text-sm font-mono font-bold text-primary-700">{order.code || `PED-${String(order.id).padStart(6, '0')}`}</span>
                  <span className="font-medium text-gray-800">{order.client_name}</span>
                  <span className={STATUS_MAP[order.status]?.class || 'badge-gray'}>
                    {STATUS_MAP[order.status]?.label || order.status}
                  </span>
                  <span className="text-sm text-gray-500">
                    {new Date(order.created_at).toLocaleString('pt-BR')}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-bold text-gray-800">R$ {order.total.toFixed(2)}</span>
                  <button
                    onClick={() => setExpanded(expanded === order.id ? null : order.id)}
                    className="p-1.5 hover:bg-gray-100 rounded-lg"
                  >
                    <Eye size={16} className="text-gray-400" />
                  </button>
                  {order.status === 'confirmed' && (
                    <button onClick={() => cancelOrder(order)} className="p-1.5 hover:bg-red-50 rounded-lg text-red-500">
                      <XCircle size={16} />
                    </button>
                  )}
                </div>
              </div>

              {expanded === order.id && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-gray-500">
                        <th className="text-left pb-2 font-medium">Código / produto</th>
                        <th className="text-center pb-2 font-medium">Qtd</th>
                        <th className="text-right pb-2 font-medium">Unit.</th>
                        <th className="text-right pb-2 font-medium">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {order.items?.map((item) => (
                        <tr key={item.id} className="border-t border-gray-50">
                          <td className="py-2 text-gray-700"><span className="font-mono text-xs text-primary-700">{item.product_code || `PRD-${String(item.product_id).padStart(6, '0')}`}</span><span className="ml-2">{item.product_name}</span></td>
                          <td className="py-2 text-center">{item.quantity}</td>
                          <td className="py-2 text-right">R$ {item.unit_price.toFixed(2)}</td>
                          <td className="py-2 text-right font-medium">R$ {item.total.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="border-t border-gray-200 font-bold">
                        <td colSpan={3} className="py-2 text-right">Total:</td>
                        <td className="py-2 text-right">R$ {order.total.toFixed(2)}</td>
                      </tr>
                    </tfoot>
                  </table>
                  {order.user_name && (
                    <p className="text-xs text-gray-400 mt-2">Atendente: {order.user_name}</p>
                  )}
                  {order.notes && <p className="text-xs text-gray-500 mt-1">Obs: {order.notes}</p>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
