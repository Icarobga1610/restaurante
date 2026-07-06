import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { products as productsApi } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'react-toastify';
import { Plus, Search, Edit, Tag, Package, DollarSign, TrendingUp } from 'lucide-react';

export default function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [categories, setCategories] = useState([]);
  const { hasRole } = useAuth();

  const loadProducts = async () => {
    try {
      const params = { active_only: false };
      if (search) params.search = search;
      if (categoryFilter) params.category = categoryFilter;
      const res = await productsApi.list(params);
      setProducts(res.data);
      const cats = [...new Set(res.data.map((p) => p.category))];
      setCategories(cats);
    } catch (err) {
      toast.error('Erro ao carregar produtos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const filtered = products.filter((p) => {
    if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false;
    if (categoryFilter && p.category !== categoryFilter) return false;
    return true;
  });

  const toggleActive = async (product) => {
    try {
      await productsApi.update(product.id, { is_active: !product.is_active });
      toast.success(`Produto ${product.is_active ? 'desativado' : 'ativado'}`);
      loadProducts();
    } catch {
      toast.error('Erro ao alterar produto');
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Produtos</h1>
          <p className="text-gray-500 text-sm mt-1">{products.length} produto(s) cadastrado(s)</p>
        </div>
        {hasRole('admin') && (
          <Link to="/products/new" className="btn-primary flex items-center gap-2">
            <Plus size={18} />
            Novo Produto
          </Link>
        )}
      </div>

      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            className="input-field pl-10"
            placeholder="Buscar produto..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select className="input-field max-w-xs" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
          <option value="">Todas categorias</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-500"></div>
        </div>
      ) : filtered.length === 0 ? (
        <div className="card text-center py-12">
          <Package className="mx-auto text-gray-300" size={48} />
          <p className="text-gray-500 mt-4">Nenhum produto encontrado</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map((product) => (
            <div key={product.id} className={`card card-hover ${!product.is_active ? 'opacity-60' : ''}`}>
              <div className="flex items-start justify-between mb-2">
                <span className="badge-blue">{product.category}</span>
                <span className={`badge ${product.is_active ? 'badge-green' : 'badge-gray'}`}>
                  {product.is_active ? 'Ativo' : 'Inativo'}
                </span>
              </div>
              <h3 className="font-semibold text-gray-800 mb-2">{product.name}</h3>
              <div className="space-y-1 text-sm">
                <p className="flex items-center gap-1 text-gray-600">
                  <DollarSign size={14} />
                  Preço: <strong className="text-gray-800">R$ {product.price.toFixed(2)}</strong>
                </p>
                {product.estimated_cost && (
                  <p className="flex items-center gap-1 text-gray-500">
                    <TrendingUp size={14} />
                    Custo est.: R$ {product.estimated_cost.toFixed(2)}
                  </p>
                )}
                {product.seasonality && (
                  <p className="flex items-center gap-1 text-primary-600 text-xs mt-2">
                    <Tag size={12} />
                    Sazonal: {product.seasonality.type || 'personalizado'}
                  </p>
                )}
              </div>
              {hasRole('admin') && (
                <div className="mt-4 pt-3 border-t border-gray-100 flex justify-end gap-2">
                  <Link
                    to={`/products/${product.id}/edit`}
                    className="p-1.5 hover:bg-blue-50 rounded-lg text-blue-600 transition-colors"
                    title="Editar"
                  >
                    <Edit size={16} />
                  </Link>
                  <button
                    onClick={() => toggleActive(product)}
                    className={`p-1.5 rounded-lg transition-colors ${
                      product.is_active ? 'hover:bg-red-50 text-red-600' : 'hover:bg-green-50 text-green-600'
                    }`}
                  >
                    {product.is_active ? (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
                    ) : (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 13l4 4L19 7"/></svg>
                    )}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
