import React, { useEffect, useState } from 'react';
import api, { delivery } from '../services/api';
import { toast } from 'react-toastify';

export default function Delivery() {
  const [tab, setTab] = useState('orders');
  const [platforms, setPlatforms] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deliveryView, setDeliveryView] = useState('kanban');
  const [platformForm, setPlatformForm] = useState({ name: '', slug: '', active: true, api_base_url: '', webhook_secret: '', settings: {} });
  const [orderForm, setOrderForm] = useState({ platform_slug: '', external_order_id: '', client_name: '', client_phone: '', address: '', payment_method: 'money', subtotal: '', delivery_fee: '0', discount: '0', items: [{ product_name: '', quantity: '1', unit_price: '', total: '' }] });

  const loadPlatforms = async () => {
    setLoading(true);
    try { const { data } = await delivery.platforms.list(); setPlatforms(data || []); }
    catch (e) { toast.error('Erro ao listar plataformas'); }
    finally { setLoading(false); }
  };

  const loadOrders = async () => {
    setLoading(true);
    try { const { data } = await delivery.orders.list(); setOrders(data || []); }
    catch (e) { toast.error('Erro ao listar pedidos'); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadPlatforms(); loadOrders(); }, []);

  const createPlatform = async () => {
    if (!platformForm.name) return toast.error('Informe o nome da plataforma');
    try {
      await delivery.platforms.create(platformForm);
      toast.success('Plataforma criada');
      setPlatformForm({ name: '', slug: '', active: true, api_base_url: '', webhook_secret: '', settings: {} });
      loadPlatforms();
    } catch (e) { toast.error(String(e?.response?.data?.detail || 'Erro ao criar plataforma')); }
  };

  const ensurePlatformForOrder = async () => {
    const name = orderForm.platform_slug;
    if (!name) return;
    const slug = name.trim().toLowerCase().replace(/ /g, '_').replace(/-/g, '_');
    setOrderForm(f => ({ ...f, platform_slug: name }));
    try { await delivery.platforms.create({ name: name.trim(), slug, active: true }); toast.success('Plataforma registrada'); await loadPlatforms(); }
    catch (e) { /* ignore if exists */ }
  };

  const updateItem = (idx, key, value) => {
    const items = [...orderForm.items];
    items[idx] = { ...items[idx], [key]: value };
    if (key === 'quantity' || key === 'unit_price') {
      const qty = parseFloat(items[idx].quantity || 0);
      const price = parseFloat(items[idx].unit_price || 0);
      items[idx].total = String((isNaN(qty) ? 0 : qty) * (isNaN(price) ? 0 : price));
    }
    setOrderForm(f => ({ ...f, items }));
  };

  const sendOrder = async () => {
    const subtotal = orderForm.items.reduce((s, it) => s + (parseFloat(it.total || 0) || 0), 0);
    const delivery_fee = parseFloat(orderForm.delivery_fee || 0) || 0;
    const discount = parseFloat(orderForm.discount || 0) || 0;
    const total = subtotal + delivery_fee - discount;
    await ensurePlatformForOrder();
    const payload = {
      platform_slug: orderForm.platform_slug || 'iFood',
      external_order_id: orderForm.external_order_id || undefined,
      client_name: orderForm.client_name || 'Cliente Delivery',
      client_phone: orderForm.client_phone,
      address: orderForm.address || 'Endereço',
      payment_method: orderForm.payment_method || 'money',
      subtotal,
      delivery_fee,
      discount,
      total,
      items: orderForm.items.map(it => ({ product_name: it.product_name, quantity: parseFloat(it.quantity || 1) || 1, unit_price: parseFloat(it.unit_price || 0) || 0, total: parseFloat(it.total || 0) || 0 }))
    };
    try { await delivery.orders.create(payload); toast.success('Pedido recebido'); loadOrders(); setOrderForm({ platform_slug: '', external_order_id: '', client_name: '', client_phone: '', address: '', payment_method: 'money', subtotal: '', delivery_fee: '0', discount: '0', items: [{ product_name: '', quantity: '1', unit_price: '', total: '' }] }); }
    catch (e) { toast.error(String(e?.response?.data?.detail || 'Erro ao criar pedido')); }
  };

  const ack = async id => {
    try { await delivery.orders.ack(id); toast.success('Pedido confirmado'); await loadOrders(); }
    catch (e) { toast.error(String(e?.response?.data?.detail || 'Não foi possível confirmar o pedido')); }
  };
  const cancel = async id => {
    if (!window.confirm('Cancelar pedido?')) return;
    try { await delivery.orders.cancel(id); toast.success('Pedido cancelado'); await loadOrders(); }
    catch (e) { toast.error(String(e?.response?.data?.detail || 'Não foi possível cancelar o pedido')); }
  };
  const convert = async id => {
    try { await delivery.orders.convert(id); toast.success('Pedido convertido'); await loadOrders(); }
    catch (e) { toast.error(String(e?.response?.data?.detail || 'Não foi possível converter o pedido')); }
  };

  const deliveryColumns = [
    { key: 'pending', label: 'Aguardando confirmação', color: 'border-amber-200 bg-amber-50' },
    { key: 'acknowledged', label: 'Confirmados / em preparo', color: 'border-blue-200 bg-blue-50' },
    { key: 'converted', label: 'Convertidos', color: 'border-emerald-200 bg-emerald-50' },
    { key: 'cancelled', label: 'Cancelados', color: 'border-red-200 bg-red-50' },
  ];
  const statusLabel = { pending: 'Pendente', acknowledged: 'Confirmado', converted: 'Convertido', cancelled: 'Cancelado' };

  const apiBase = (api.defaults.baseURL || '/api').replace(/\/$/, '');

  const copy = text => { navigator.clipboard.writeText(text).catch(() => {}); toast.success('URL copiada'); };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-semibold text-gray-800">Entregas</h1>
        <div className="flex gap-2">
          <button onClick={() => setTab('orders')} className={`px-3 py-1.5 text-sm border rounded-md ${tab === 'orders' ? 'bg-gray-900 text-white border-gray-900' : ''}`}>Entrada de Pedidos</button>
          <button onClick={() => setTab('platforms')} className={`px-3 py-1.5 text-sm border rounded-md ${tab === 'platforms' ? 'bg-gray-900 text-white border-gray-900' : ''}`}>Plataformas</button>
          <button onClick={() => setTab('webhook')} className={`px-3 py-1.5 text-sm border rounded-md ${tab === 'webhook' ? 'bg-gray-900 text-white border-gray-900' : ''}`}>Receber Webhook</button>
        </div>
      </div>

      {tab === 'orders' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100 font-medium text-gray-700">Entrada manual</div>
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-600">Plataforma</label>
                  <input value={orderForm.platform_slug} onChange={e => setOrderForm(f => ({ ...f, platform_slug: e.target.value }))} className="mt-1 w-full border rounded-md px-3 py-2 text-sm" placeholder="Ex: iFood, Rappi, Uber Eats" />
                </div>
                <div>
                  <label className="block text-xs text-gray-600">ID externo</label>
                  <input value={orderForm.external_order_id} onChange={e => setOrderForm(f => ({ ...f, external_order_id: e.target.value }))} className="mt-1 w-full border rounded-md px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-600">Cliente</label>
                  <input value={orderForm.client_name} onChange={e => setOrderForm(f => ({ ...f, client_name: e.target.value }))} className="mt-1 w-full border rounded-md px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-600">Telefone</label>
                  <input value={orderForm.client_phone} onChange={e => setOrderForm(f => ({ ...f, client_phone: e.target.value }))} className="mt-1 w-full border rounded-md px-3 py-2 text-sm" />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-600">Endereço</label>
                  <input value={orderForm.address} onChange={e => setOrderForm(f => ({ ...f, address: e.target.value }))} className="mt-1 w-full border rounded-md px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-600">Pagamento</label>
                  <select value={orderForm.payment_method} onChange={e => setOrderForm(f => ({ ...f, payment_method: e.target.value }))} className="mt-1 w-full border rounded-md px-3 py-2 text-sm">
                    <option value="money">Dinheiro</option>
                    <option value="pix">Pix</option>
                    <option value="card">Cartão</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-600">Taxa entrega</label>
                  <input type="number" value={orderForm.delivery_fee} onChange={e => setOrderForm(f => ({ ...f, delivery_fee: e.target.value }))} className="mt-1 w-full border rounded-md px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-600">Desconto</label>
                  <input type="number" value={orderForm.discount} onChange={e => setOrderForm(f => ({ ...f, discount: e.target.value }))} className="mt-1 w-full border rounded-md px-3 py-2 text-sm" />
                </div>
              </div>

              <div>
                <div className="text-xs text-gray-600 mb-1">Itens</div>
                <div className="space-y-2">
                  {orderForm.items.map((it, idx) => (
                    <div key={idx} className="grid grid-cols-5 gap-2">
                      <input className="col-span-2 border rounded-md px-2 py-1.5 text-xs" placeholder="Produto" value={it.product_name} onChange={e => updateItem(idx, 'product_name', e.target.value)} />
                      <input type="number" className="border rounded-md px-2 py-1.5 text-xs" placeholder="Qtd" value={it.quantity} onChange={e => updateItem(idx, 'quantity', e.target.value)} />
                      <input type="number" className="border rounded-md px-2 py-1.5 text-xs" placeholder="Preço" value={it.unit_price} onChange={e => updateItem(idx, 'unit_price', e.target.value)} />
                      <input disabled className="border rounded-md px-2 py-1.5 text-xs bg-gray-50" value={it.total} readOnly />
                    </div>
                  ))}
                </div>
                <button type="button" onClick={() => setOrderForm(f => ({ ...f, items: [...f.items, { product_name: '', quantity: '1', unit_price: '', total: '' }] }))} className="mt-2 text-xs border px-2 py-1 rounded-md">Adicionar item</button>
              </div>
              <button onClick={sendOrder} className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm">Receber pedido</button>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between gap-3">
              <div>
                <div className="font-medium text-gray-700">Central de delivery</div>
                <div className="text-xs text-gray-500">Acompanhe a entrada, confirmação e conversão dos pedidos.</div>
              </div>
              <div className="flex rounded-md border border-gray-200 p-0.5 text-xs">
                <button onClick={() => setDeliveryView('kanban')} className={`px-3 py-1.5 rounded ${deliveryView === 'kanban' ? 'bg-gray-900 text-white' : 'text-gray-600'}`}>Kanban</button>
                <button onClick={() => setDeliveryView('table')} className={`px-3 py-1.5 rounded ${deliveryView === 'table' ? 'bg-gray-900 text-white' : 'text-gray-600'}`}>Tabela</button>
              </div>
            </div>

            {deliveryView === 'kanban' ? (
              <div className="p-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 overflow-x-auto">
                {deliveryColumns.map(column => {
                  const columnOrders = orders.filter(order => order.status === column.key);
                  return (
                    <div key={column.key} className={`rounded-lg border ${column.color} min-h-[230px]`}>
                      <div className="px-3 py-2 border-b border-inherit flex items-center justify-between">
                        <span className="text-sm font-semibold text-gray-800">{column.label}</span>
                        <span className="rounded-full bg-white/80 px-2 py-0.5 text-xs font-semibold text-gray-600">{columnOrders.length}</span>
                      </div>
                      <div className="p-2 space-y-2">
                        {columnOrders.length === 0 && <div className="p-4 text-center text-xs text-gray-500">Nenhum pedido</div>}
                        {columnOrders.map(order => (
                          <div key={order.id} className="rounded-lg border border-gray-200 bg-white p-3 shadow-sm space-y-2">
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <div className="font-semibold text-sm text-gray-800">Pedido #{order.id}</div>
                                <div className="text-xs text-gray-500 capitalize">{order.platform?.slug || order.platform_slug || 'delivery'} · {statusLabel[order.status] || order.status}</div>
                              </div>
                              <div className="font-semibold text-sm text-gray-800">R$ {Number(order.total || 0).toFixed(2)}</div>
                            </div>
                            <div className="text-xs text-gray-600 truncate">{order.client_name || 'Cliente não informado'}</div>
                            <div className="text-xs text-gray-500 truncate">{order.address || 'Endereço não informado'}</div>
                            <div className="flex flex-wrap gap-1 pt-1">
                              {order.status === 'pending' && <button onClick={() => ack(order.id)} className="text-xs px-2 py-1 rounded border border-blue-200 text-blue-700 hover:bg-blue-50">Confirmar</button>}
                              {order.status !== 'cancelled' && order.status !== 'converted' && <button onClick={() => convert(order.id)} className="text-xs px-2 py-1 rounded border border-emerald-200 text-emerald-700 hover:bg-emerald-50">Converter</button>}
                              {order.status !== 'cancelled' && order.status !== 'converted' && <button onClick={() => cancel(order.id)} className="text-xs px-2 py-1 rounded border border-red-200 text-red-700 hover:bg-red-50">Cancelar</button>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead><tr className="text-left text-gray-500 border-b border-gray-100"><th className="px-4 py-2">ID</th><th className="px-4 py-2">Plataforma</th><th className="px-4 py-2">Status</th><th className="px-4 py-2">Cliente</th><th className="px-4 py-2">Total</th><th className="px-4 py-2">Ações</th></tr></thead>
                  <tbody className="divide-y divide-gray-100">
                    {orders.length === 0 && <tr><td colSpan={6} className="p-4 text-center text-gray-500">Sem pedidos recebidos</td></tr>}
                    {orders.map(order => (
                      <tr key={order.id} className="text-gray-700"><td className="px-4 py-2">#{order.id}</td><td className="px-4 py-2 capitalize">{order.platform?.slug || order.platform_slug || '-'}</td><td className="px-4 py-2">{statusLabel[order.status] || order.status}</td><td className="px-4 py-2">{order.client_name || '-'}</td><td className="px-4 py-2">R$ {Number(order.total || 0).toFixed(2)}</td><td className="px-4 py-2 space-x-2"><button onClick={() => ack(order.id)} className="text-xs px-2 py-1 border rounded-md">Confirmar</button><button onClick={() => convert(order.id)} className="text-xs px-2 py-1 border rounded-md">Converter</button><button onClick={() => cancel(order.id)} className="text-xs px-2 py-1 border rounded-md text-red-700">Cancelar</button></td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'platforms' && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="px-4 py-3 border-b border-gray-100 font-medium text-gray-700">Plataformas</div>
          <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="space-y-2 md:border-r md:pr-4">
              <div className="text-xs text-gray-600">Nova plataforma</div>
              <input value={platformForm.name} onChange={e => setPlatformForm(f => ({ ...f, name: e.target.value, slug: e.target.value.trim().toLowerCase().replace(/ /g,'_').replace(/-/g,'_') }))} className="w-full border rounded-md px-3 py-2 text-sm" placeholder="Nome" />
              <input value={platformForm.slug} onChange={e => setPlatformForm(f => ({ ...f, slug: e.target.value }))} className="w-full border rounded-md px-3 py-2 text-sm" placeholder="slug" />
              <input value={platformForm.api_base_url} onChange={e => setPlatformForm(f => ({ ...f, api_base_url: e.target.value }))} className="w-full border rounded-md px-3 py-2 text-sm" placeholder="API base URL" />
              <input value={platformForm.webhook_secret} onChange={e => setPlatformForm(f => ({ ...f, webhook_secret: e.target.value }))} className="w-full border rounded-md px-3 py-2 text-sm" placeholder="Webhook secret" />
              <button onClick={createPlatform} className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm">Salvar</button>
            </div>
            <div className="divide-y divide-gray-100">
              {platforms.length === 0 && !loading && <div className="text-sm text-gray-500">Nenhuma plataforma cadastrada</div>}
              {platforms.map(p => (
                <div key={p.id} className="py-2 flex items-center justify-between text-sm">
                  <div>
                    <div className="font-medium text-gray-800">{p.name}</div>
                    <div className="text-gray-500 text-xs">{p.slug} {p.webhook_secret ? '• secret definido' : ''}</div>
                  </div>
                  <div className="text-xs text-gray-500">{p.active ? 'Ativa' : 'Inativa'}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === 'webhook' && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-3 text-sm text-gray-700">
          <div className="font-medium text-gray-800">Receber pedidos via webhook</div>
          <p>Configure no app de entrega o endpoint abaixo como webhook. O sistema normaliza e importa automaticamente.</p>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="font-medium">Endpoint:</span>
              <code className="flex-1 bg-gray-100 border rounded-md px-3 py-2 text-xs break-all">{apiBase}/delivery/webhook/{'{platform_slug}'}</code>
              <button onClick={() => copy(`${apiBase}/delivery/webhook/{platform_slug}`)} className="text-xs border px-2 py-1 rounded-md">Copiar</button>
            </div>
            <div className="text-xs text-gray-600">Use headers: <code>X-Webhook-Secret</code> ou <code>Authorization</code></div>
            <div className="text-xs text-gray-600">Cadastre antes a plataforma na aba <strong>Plataformas</strong> para garantir o slug e o secret.</div>
          </div>
        </div>
      )}
    </div>
  );
}
