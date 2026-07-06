import React, { useEffect, useMemo, useState } from 'react';
import { toast } from 'react-toastify';
import { ClipboardList, Plus, Trash2 } from 'lucide-react';
import { products, recipes, stock } from '../services/api';

const emptyItem = { stock_item_id: '', quantity_required: '', unit_measure: 'kg' };

export default function RecipeSheets() {
  const [productList, setProductList] = useState([]);
  const [ingredientList, setIngredientList] = useState([]);
  const [recipeList, setRecipeList] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [items, setItems] = useState([emptyItem]);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(true);

  const selectedRecipe = useMemo(
    () => recipeList.find((recipe) => recipe.product_id === parseInt(selectedProductId, 10)),
    [recipeList, selectedProductId]
  );

  const loadData = async () => {
    try {
      const [productsRes, stockRes, recipesRes] = await Promise.all([
        products.list({ active_only: true, limit: 500 }),
        stock.items.list({ limit: 500 }),
        recipes.list(),
      ]);
      setProductList(productsRes.data);
      setIngredientList(stockRes.data);
      setRecipeList(recipesRes.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao carregar fichas técnicas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  useEffect(() => {
    if (selectedRecipe) {
      setNotes(selectedRecipe.notes || '');
      setItems(selectedRecipe.items.map((item) => ({
        stock_item_id: String(item.stock_item_id),
        quantity_required: String(item.quantity_required),
        unit_measure: item.unit_measure,
      })));
    } else {
      setNotes('');
      setItems([emptyItem]);
    }
  }, [selectedRecipe?.id, selectedProductId]);

  const updateItem = (index, field, value) => {
    const next = [...items];
    next[index] = { ...next[index], [field]: value };
    if (field === 'stock_item_id') {
      const ingredient = ingredientList.find((item) => item.id === parseInt(value, 10));
      if (ingredient) next[index].unit_measure = ingredient.unit_measure;
    }
    setItems(next);
  };

  const saveRecipe = async (e) => {
    e.preventDefault();
    if (!selectedProductId) {
      toast.warning('Selecione um prato/produto');
      return;
    }
    const validItems = items.filter((item) => item.stock_item_id && item.quantity_required);
    if (validItems.length === 0) {
      toast.warning('Adicione pelo menos um ingrediente');
      return;
    }

    const payload = {
      product_id: parseInt(selectedProductId, 10),
      notes: notes || null,
      items: validItems.map((item) => ({
        stock_item_id: parseInt(item.stock_item_id, 10),
        quantity_required: parseFloat(item.quantity_required),
        unit_measure: item.unit_measure,
        cost: 0,
      })),
    };

    try {
      if (selectedRecipe) {
        await recipes.update(selectedRecipe.id, payload);
        toast.success('Ficha técnica atualizada');
      } else {
        await recipes.create(payload);
        toast.success('Ficha técnica criada');
      }
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao salvar ficha técnica');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Fichas Técnicas</h1>
        <p className="text-gray-500 text-sm mt-1">Defina quais ingredientes cada prato consome para baixar o estoque automaticamente.</p>
      </div>

      <form onSubmit={saveRecipe} className="card space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Prato/produto</label>
          <select className="input-field" value={selectedProductId} onChange={(e) => setSelectedProductId(e.target.value)}>
            <option value="">Selecione...</option>
            {productList.map((product) => (
              <option key={product.id} value={product.id}>{product.name} - R$ {product.price.toFixed(2)}</option>
            ))}
          </select>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-700 flex items-center gap-2"><ClipboardList size={18} />Ingredientes da receita</h2>
            <button type="button" className="btn-secondary flex items-center gap-1 text-sm py-1.5 px-3" onClick={() => setItems([...items, emptyItem])}>
              <Plus size={14} />Adicionar
            </button>
          </div>

          {items.map((item, index) => (
            <div key={index} className="grid grid-cols-1 md:grid-cols-[1fr_140px_120px_36px] gap-3 bg-gray-50 p-3 rounded-lg">
              <select className="input-field" value={item.stock_item_id} onChange={(e) => updateItem(index, 'stock_item_id', e.target.value)}>
                <option value="">Ingrediente...</option>
                {ingredientList.map((ingredient) => (
                  <option key={ingredient.id} value={ingredient.id}>
                    {ingredient.name} ({ingredient.current_quantity.toFixed(3)} {ingredient.unit_measure})
                  </option>
                ))}
              </select>
              <input
                type="number"
                step="0.001"
                min="0"
                className="input-field"
                placeholder="Qtd usada"
                value={item.quantity_required}
                onChange={(e) => updateItem(index, 'quantity_required', e.target.value)}
              />
              <select className="input-field" value={item.unit_measure} onChange={(e) => updateItem(index, 'unit_measure', e.target.value)}>
                {['kg', 'g', 'litro', 'ml', 'unidade', 'pacote', 'caixa'].map((unit) => <option key={unit} value={unit}>{unit}</option>)}
              </select>
              <button type="button" className="p-2 text-red-500 hover:bg-red-50 rounded-lg" onClick={() => setItems(items.filter((_, i) => i !== index))}>
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>

        <textarea className="input-field" rows={2} placeholder="Observações da ficha técnica" value={notes} onChange={(e) => setNotes(e.target.value)} />

        <button type="submit" className="btn-primary">{selectedRecipe ? 'Atualizar Ficha Técnica' : 'Criar Ficha Técnica'}</button>
      </form>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {recipeList.map((recipe) => (
          <div key={recipe.id} className="card">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold text-gray-800">{recipe.product_name}</h3>
                <p className="text-sm text-gray-500">Custo: R$ {recipe.total_cost.toFixed(2)} · Margem: {(recipe.estimated_margin || 0).toFixed(1)}%</p>
              </div>
              <button type="button" className="btn-secondary text-sm py-1.5 px-3" onClick={() => setSelectedProductId(String(recipe.product_id))}>Editar</button>
            </div>
            <div className="mt-3 space-y-1">
              {recipe.items.map((item) => (
                <div key={item.id} className="flex justify-between text-sm bg-gray-50 rounded px-3 py-2">
                  <span>{item.stock_item_name}</span>
                  <span>{item.quantity_required} {item.unit_measure}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
        {!loading && recipeList.length === 0 && <div className="card text-center text-gray-500 py-8">Nenhuma ficha técnica cadastrada.</div>}
      </div>
    </div>
  );
}
