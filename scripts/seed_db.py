#!/usr/bin/env python3
"""Seed the database with sample data for testing."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from datetime import datetime, timedelta
from random import randint, choice, uniform

from app.database import SessionLocal, engine, Base
from app.models.user import User, Role
from app.models.client import Client
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.auth.auth import hash_password

fake = None
try:
    from faker import Faker
    fake = Faker("pt_BR")
except ImportError:
    class FakePhone:
        def phone_number(self):
            return f"+55 11 9{randint(10000000, 99999999)}"
    fake = FakePhone()


def seed():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Client).count() > 0:
            print("Database already has data. Skipping seed.")
            return

        print("Seeding roles...")
        roles = [
            Role(name="admin", description="Administrador"),
            Role(name="attendant", description="Atendente"),
            Role(name="financial", description="Financeiro"),
        ]
        for r in roles:
            db.add(r)
        db.flush()

        print("Seeding users...")
        users = [
            User(
                username="admin",
                password_hash=hash_password("admin123"),
                full_name="Administrador",
                role_id=roles[0].id,
                is_active=True,
            ),
            User(
                username="atendente",
                password_hash=hash_password("atendente123"),
                full_name="Maria Atendente",
                role_id=roles[1].id,
                is_active=True,
            ),
            User(
                username="financeiro",
                password_hash=hash_password("financeiro123"),
                full_name="João Financeiro",
                role_id=roles[2].id,
                is_active=True,
            ),
        ]
        for u in users:
            db.add(u)
        db.flush()

        print("Seeding clients...")
        client_names = [
            "Padaria Pão de Açúcar Ltda",
            "Escola Criança Feliz",
            "Auto Mecânica Veloz",
            "Escritório Rocha & Associados",
            "Loja do João",
            "Salão de Beleza Bela Vista",
            "Construtora Nova Era",
            "Clínica Saúde Total",
            "Farmácia Popular",
            "Mercado Bom Preço",
        ]
        clients = []
        for i, name in enumerate(client_names):
            phone = fake.phone_number()[:20] if hasattr(fake, 'phone_number') else f"119{randint(10000000, 99999999)}"
            client = Client(
                name=name,
                document=str(randint(10000000000, 99999999999)),
                phone=str(phone),
                company_sector=choice(["Alimentação", "Educação", "Automotivo", "Jurídico", "Varejo", "Beleza", "Construção", "Saúde"]),
                status="active",
                monthly_limit=round(uniform(500, 5000), 2) if i % 3 == 0 else None,
            )
            db.add(client)
            clients.append(client)
        db.flush()

        print("Seeding products...")
        categories = {
            "Bebidas": ["Coca-Cola", "Guaraná Antarctica", "Suco de Laranja", "Água Mineral", "Cerveja Brahma", "Café Expresso", "Chá Gelado", "Água com Gás"],
            "Lanches": ["X-Burguer", "X-Salada", "X-Calabresa", "Hot Dog", "Misto Quente", "Bauru", "Hambúrguer Artesanal", "Sanduíche Natural"],
            "Porções": ["Batata Frita", "Mandioca Frita", "Frango à Passarinho", "Calabresa Acebolada", "Isca de Peixe", "Filé de Frango"],
            "Sobremesas": ["Pudim", "Sorvete", "Mousse de Chocolate", "Torta de Limão", "Fruta da Estação"],
            "Refeições": ["Prato Executivo", "Prato do Dia", "Salada Completa", "Yakisoba", "Macarrão à Bolonhesa"],
        }
        products = []
        for category, names in categories.items():
            for name in names:
                product = Product(
                    name=name,
                    category=category,
                    price=round(uniform(5, 60), 2),
                    estimated_cost=round(uniform(2, 25), 2),
                    is_active=True,
                )
                db.add(product)
                products.append(product)
        db.flush()

        print("Seeding orders (3 months of data)...")
        for days_ago in range(1, 90):
            order_date = datetime.utcnow() - timedelta(days=days_ago)
            for _ in range(randint(3, 15)):
                client = choice(clients)
                num_items = randint(1, 5)
                total = 0
                order_items_data = []
                for _ in range(num_items):
                    product = choice(products)
                    qty = randint(1, 3)
                    unit_price = product.price * uniform(0.9, 1.1)
                    item_total = round(qty * unit_price, 2)
                    total += item_total
                    order_items_data.append({
                        "product_id": product.id,
                        "product_name": product.name,
                        "quantity": qty,
                        "unit_price": round(unit_price, 2),
                        "total": round(item_total, 2),
                    })

                order = Order(
                    client_id=client.id,
                    user_id=choice(users).id,
                    status=choice(["confirmed", "invoiced", "paid"]),
                    total=round(total, 2),
                    created_at=order_date + timedelta(hours=randint(7, 22), minutes=randint(0, 59)),
                )
                db.add(order)
                db.flush()

                for item in order_items_data:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=item["product_id"],
                        product_name=item["product_name"],
                        quantity=item["quantity"],
                        unit_price=item["unit_price"],
                        total=item["total"],
                    )
                    db.add(order_item)

            if days_ago % 30 == 0:
                print(f"  ... {days_ago} days of orders seeded")

        db.commit()
        print("\n✅ Database seeded successfully!")
        print(f"   - {len(roles)} roles")
        print(f"   - {len(users)} users")
        print(f"   - {len(clients)} clients")
        print(f"   - {len(products)} products")
        print(f"   - Orders from {90} days")
        print("\n   Login credentials:")
        print("   admin / admin123")
        print("   atendente / atendente123")
        print("   financeiro / financeiro123")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
