from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ProductRecipe(Base):
    """Ficha técnica de um produto — define os insumos necessários para produzi-lo."""
    __tablename__ = "product_recipes"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True, index=True)
    # Custo total calculado a partir dos itens da receita
    total_cost = Column(Float, default=0.0)
    # Margem de lucro estimada (%)
    estimated_margin = Column(Float, nullable=True)
    # Versão da receita
    version = Column(Integer, default=1)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    product = relationship("Product")
    items = relationship("ProductRecipeItem", back_populates="recipe", cascade="all, delete-orphan")


class ProductRecipeItem(Base):
    """Item da ficha técnica — vincula um insumo a um produto com quantidade."""
    __tablename__ = "product_recipe_items"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("product_recipes.id"), nullable=False)
    stock_item_id = Column(Integer, ForeignKey("stock_items.id"), nullable=False)
    quantity_required = Column(Float, nullable=False)  # quantidade necessária
    unit_measure = Column(String(20), nullable=False)  # kg, g, litro, ml, unidade, pacote
    # Custo proporcional (calculado = stock_item.unit_cost * quantity_required)
    cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())

    recipe = relationship("ProductRecipe", back_populates="items")
    stock_item = relationship("StockItem")
