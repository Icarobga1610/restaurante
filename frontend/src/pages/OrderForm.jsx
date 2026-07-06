import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { orders as ordersApi, clients as clientsApi, products as productsApi, monthlyAccounts as maApi, biometrics as bioApi } from '../services/api';
import { toast } from 'react-toastify';
import { Save, ArrowLeft, Plus, Trash2, Search, User, Fingerprint, CheckCircle, X } from 'lucide-react';

export default function OrderForm() {
  const navigate = useNavigate();
  const [clients, setClients] = useState([]);
  const [products, setProducts] = useState([]);
  const [clientSearch, setClientSearch] = useState('');
  const [selectedClient, setSelectedClient] = useState(null);
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      clientsApi.list({ status: 'active', limit: 200 }),
      productsApi.list({ active_only: true }),
    ]).then(([clientsRes, productsRes]) => {
      setClients(clientsRes.data);
      setProducts(productsRes.data);
    }).catch(() => toast.error('Erro ao carregar dados'));
  }, []);

  const addItem = () => {
    setItems([...items, { product_id: '', product_name: '', quantity: 1, unit_price: 0, total: 0 }]);
  };

  const removeItem = (idx) => setItems(items.filter((_, i) => i !== idx));

  const updateItem = (idx, field, value) => {
    const newItems = [...items];
    newItems[idx] = { ...newItems[idx], [field]: value };
    if (field === 'product_id') {
      const product = products.find((p) => p.id === parseInt(value));
      if (product) {
        newItems[idx].product_name = product.name;
        newItems[idx].unit_price = product.price;
        newItems[idx].total = product.price * parseFloat(newItems[idx].quantity || 0);
      }
    }
    if (field === 'quantity') newItems[idx].total = newItems[idx].unit_price * parseFloat(value || 0);
    setItems(newItems);
  };

  const total = items.reduce((sum, item) => sum + item.total, 0);

  const filteredClients = clients.filter((c) => c.name.toLowerCase().includes(clientSearch.toLowerCase()));

  const submitOrder = async () => {
    if (!selectedClient) { toast.warning('Selecione um cliente'); return; }
    if (items.length === 0) { toast.warning('Adicione pelo menos um item'); return; }

    const payload = {
      client_id: selectedClient.id,
      notes,
      items: items.map((item) => ({
        product_id: parseInt(item.product_id),
        product_name: item.product_name,
        quantity: parseFloat(item.quantity),
        unit_price: parseFloat(item.unit_price),
        total: parseFloat(item.total),
      })),
    };

    setLoading(true);
    try {
      await ordersApi.create(payload);
      toast.success('Pedido criado com sucesso!');
      navigate('/orders');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao criar pedido');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      <div className="flex items-center gap-4 mb-6">
        <button type="button" onClick={() => navigate('/orders')} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft size={20} className="text-gray-600" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Novo Pedido</h1>
          <p className="text-gray-500 text-sm mt-1">
            {selectedClient?.is_account_client ? 'Cliente de conta: pedido vinculado à conta mensal. Assinatura/biometria no fechamento/pagamento.' : 'Cliente avulso: fluxo normal de caixa.'}
          </p>
        </div>
      </div>

      <div className="space-y-6">
        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-3 flex items-center gap-2"><User size={18}/>Cliente</h2>
          {!selectedClient ? (
            <div>
              <input type="text" className="input-field mb-2" placeholder="Buscar cliente..." value={clientSearch} onChange={(e) => setClientSearch(e.target.value)} autoFocus />
              <div className="max-h-48 overflow-y-auto space-y-1">
                {filteredClients.map((c) => (
                  <button key={c.id} type="button" onClick={() => { setSelectedClient(c); setClientSearch(''); }} className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 text-sm text-gray-700 transition-colors">
                    <span className="font-medium">{c.name}</span>
                    <span className="ml-2 text-xs text-gray-400">{c.is_account_client ? '- Conta' : '- Avulso'}</span>
                  </button>
                ))}
                {filteredClients.length === 0 && <p className="text-sm text-gray-400 py-2">Nenhum cliente encontrado</p>}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between p-3 bg-primary-50 rounded-lg border border-primary-100">
              <div>
                <p className="font-medium text-gray-800">{selectedClient.name}</p>
                <p className="text-sm text-gray-500">{selectedClient.phone} {selectedClient.is_account_client ? '- Cliente de conta' : '- Avulso'}</p>
              </div>
              <button type="button" onClick={() => setSelectedClient(null)} className="text-sm text-red-600 hover:text-red-700">Trocar</button>
            </div>
          )}
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-700">Itens do Pedido</h2>
            <button type="button" onClick={addItem} className="btn-secondary flex items-center gap-1 text-sm py-1.5 px-3"><Plus size={14}/>Adicionar</button>
          </div>
          {items.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <p>Nenhum item adicionado</p>
              <button type="button" onClick={addItem} className="text-primary-600 hover:text-primary-700 text-sm mt-2">Clique para adicionar</button>
            </div>
          ) : (
            <div className="space-y-3">
              {items.map((item, idx) => (
                <div key={idx} className="flex flex-col sm:flex-row items-start sm:items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1 w-full sm:w-auto">
                    <select className="input-field text-sm" value={item.product_id} onChange={(e) => updateItem(idx, 'product_id', e.target.value)}>
                      <option value="">Selecione...</option>
                      {products.map((p) => <option key={p.id} value={p.id}>{p.name} - R$ {p.price.toFixed(2)}</option>)}
                    </select>
                  </div>
                  <div className="w-20"><input type="number" min="0.5" step="0.5" className="input-field text-sm text-center" value={item.quantity} onChange={(e) => updateItem(idx, 'quantity', e.target.value)} /></div>
                  <div className="text-sm font-medium text-gray-700 w-24 text-right">R$ {item.total.toFixed(2)}</div>
                  <button type="button" onClick={() => removeItem(idx)} className="p-1.5 hover:bg-red-50 rounded-lg text-red-500"><Trash2 size={16}/></button>
                </div>
              ))}
            </div>
          )}
          {items.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100 flex justify-between items-center">
              <span className="text-gray-600">Total de itens: {items.length}</span>
              <span className="text-xl font-bold text-gray-800">R$ {total.toFixed(2)}</span>
            </div>
          )}
        </div>

        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
          <textarea className="input-field" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Observações do pedido..." />
        </div>

        <div className="flex items-center gap-3">
          <button type="button" disabled={loading || items.length === 0} onClick={submitOrder} className="btn-primary flex items-center gap-2">
            {loading ? 'Processando...' : <><Save size={18}/>Confirmar Pedido - R$ {total.toFixed(2)}</>}
          </button>
          <button type="button" onClick={() => navigate('/orders')} className="btn-secondary">Cancelar</button>
        </div>
      </div>
    </div>
  );
}
