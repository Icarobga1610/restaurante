import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { orders as ordersApi, clients as clientsApi, products as productsApi, biometrics } from '../services/api';
import { toast } from 'react-toastify';
import { Save, ArrowLeft, Plus, Trash2, User, Fingerprint, Search } from 'lucide-react';
import { browserSupportsWebAuthn, getWebAuthnCredential } from '../app/webauthn';

export default function OrderForm() {
  const navigate = useNavigate();
  const [clients, setClients] = useState([]);
  const [products, setProducts] = useState([]);
  const [clientSearch, setClientSearch] = useState('');
  const [productSearch, setProductSearch] = useState('');
  const [selectedClient, setSelectedClient] = useState(null);
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState([]);
  const [confirmWithBiometric, setConfirmWithBiometric] = useState(true);
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

  const addProductToOrder = (product) => {
    const existingIndex = items.findIndex((item) => item.product_id === product.id);
    if (existingIndex >= 0) {
      updateItem(existingIndex, 'quantity', Number(items[existingIndex].quantity || 0) + 1);
      return;
    }
    setItems([...items, { product_id: product.id, product_name: product.name, quantity: 1, unit_price: product.price, total: product.price }]);
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

  const verifyDigitalForAccountLaunch = async () => {
    if (!browserSupportsWebAuthn()) {
      throw new Error('Este navegador/dispositivo não suporta leitura de digital.');
    }

    toast.info('Confirme a digital para lançar o pedido na conta.');
    const options = await biometrics.webauthn.verifyOptions({ client_id: selectedClient.id });
    const credential = await getWebAuthnCredential(options.data.publicKey);
    const verification = await biometrics.webauthn.verifyComplete({
      client_id: selectedClient.id,
      ...credential,
    });
    return verification.data.verification_token;
  };

  const submitOrder = async () => {
    if (!selectedClient) { toast.warning('Selecione um cliente'); return; }
    if (items.length === 0) { toast.warning('Adicione pelo menos um item'); return; }

    setLoading(true);
    try {
      const biometricToken = confirmWithBiometric ? await verifyDigitalForAccountLaunch() : null;
      const payload = {
        client_id: selectedClient.id,
        notes,
        payment_mode: 'monthly_account',
        confirm_with_biometric: confirmWithBiometric,
        biometric_verification_token: biometricToken,
        items: items.map((item) => ({
          product_id: parseInt(item.product_id),
          product_name: item.product_name,
          quantity: parseFloat(item.quantity),
          unit_price: parseFloat(item.unit_price),
          total: parseFloat(item.total),
        })),
      };
      await ordersApi.create(payload);
      toast.success(confirmWithBiometric ? 'Pedido lançado na conta com digital!' : 'Pedido lançado na conta mensal!');
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
            {selectedClient?.is_account_client ? 'Cliente de conta: use a digital para lançar consumo na conta mensal.' : 'Cliente avulso: fluxo normal de caixa.'}
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
                <p className="text-sm text-gray-500">
                  {selectedClient.phone} {selectedClient.is_account_client ? '- Cliente de conta' : '- Avulso'}
                  {selectedClient.payment_day ? ` - paga dia ${selectedClient.payment_day}` : ''}
                </p>
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
          <div className="mb-4 rounded-xl border border-primary-100 bg-primary-50/50 p-3">
            <div className="relative mb-3"><Search size={16} className="absolute left-3 top-2.5 text-gray-400" /><input value={productSearch} onChange={(e) => setProductSearch(e.target.value)} placeholder="Buscar no cardápio e adicionar rapidamente..." className="input-field pl-9" /></div>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
              {products.filter((product) => product.name.toLowerCase().includes(productSearch.toLowerCase())).slice(0, 8).map((product) => <button type="button" key={product.id} onClick={() => addProductToOrder(product)} className="rounded-lg border border-white bg-white p-2 text-left shadow-sm transition hover:border-primary-300 hover:shadow"><p className="truncate text-xs font-semibold text-gray-700">{product.name}</p><p className="mt-1 text-xs text-primary-700">R$ {Number(product.price).toFixed(2)}</p></button>)}
            </div>
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

        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Fingerprint size={18} />
            Lançamento na conta
          </h2>
          <label className={`block rounded-lg border p-4 cursor-pointer transition-colors ${
            confirmWithBiometric ? 'border-primary-300 bg-primary-50' : 'border-gray-200 hover:border-gray-300'
          }`}>
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                className="mt-1"
                checked={confirmWithBiometric}
                onChange={(e) => setConfirmWithBiometric(e.target.checked)}
              />
              <div>
                <div className="flex items-center gap-2 font-medium text-gray-800">
                  <Fingerprint size={18} className={confirmWithBiometric ? 'text-primary-600' : 'text-gray-300'} />
                  Confirmar lançamento com digital
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  O pedido será colocado na conta mensal após validar a digital do cliente
                  {selectedClient?.payment_day ? `, com vencimento no dia ${selectedClient.payment_day}.` : '.'}
                </p>
              </div>
            </div>
          </label>
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
