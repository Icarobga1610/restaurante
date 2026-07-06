import os
import csv
import io
import shutil
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.product import Product
from app.models.stock_item import StockItem
from app.models.order import Order, OrderItem
from app.models.monthly_account import MonthlyAccount
from app.services.audit_service import AuditService

# Ensure directories exist
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
IMPORT_DIR = os.path.join(BASE_DIR, "imports")
LOG_DIR = os.path.join(BASE_DIR, "logs")

for d in [BACKUP_DIR, EXPORT_DIR, IMPORT_DIR, LOG_DIR]:
    os.makedirs(d, exist_ok=True)


class BackupService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    # ── Backup ──────────────────────────────────────────────────

    def create_backup(self, user_id: Optional[int] = None, username: Optional[str] = None) -> dict:
        db_path = os.getenv("DATABASE_URL", "sqlite:///./restaurante.db")
        if db_path.startswith("sqlite:///"):
            db_path = db_path.replace("sqlite:///", "")
            if not os.path.isabs(db_path):
                db_path = os.path.join(BASE_DIR, db_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"restaurante_backup_{timestamp}.sqlite"
        backup_path = os.path.join(BACKUP_DIR, backup_name)

        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            size = os.path.getsize(backup_path)
        else:
            raise FileNotFoundError(f"Banco de dados não encontrado: {db_path}")

        self.audit.log(
            action="create", entity_type="backup",
            user_id=user_id, username=username,
            details=f"Backup criado: {backup_name} ({size} bytes)",
        )
        return {"filename": backup_name, "path": backup_path, "size": size, "created_at": timestamp}

    def list_backups(self) -> List[dict]:
        backups = []
        if os.path.exists(BACKUP_DIR):
            for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
                if f.endswith(".sqlite"):
                    fpath = os.path.join(BACKUP_DIR, f)
                    backups.append({
                        "filename": f,
                        "size": os.path.getsize(fpath),
                        "modified_at": datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
                    })
        return backups

    # ── CSV Export ──────────────────────────────────────────────

    def _export_csv(self, filename_prefix: str, headers: list, rows: list) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"
        filepath = os.path.join(EXPORT_DIR, filename)
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return filename

    def export_clients(self) -> str:
        clients = self.db.query(Client).all()
        rows = [[c.id, c.name, c.document or "", c.phone, c.company_sector or "",
                  c.status, c.monthly_limit or 0, c.notes or ""] for c in clients]
        return self._export_csv("clientes",
            ["id", "nome", "documento", "telefone", "setor", "status", "limite_mensal", "observacoes"], rows)

    def export_products(self) -> str:
        products = self.db.query(Product).all()
        rows = [[p.id, p.name, p.category, p.price, p.estimated_cost or 0,
                  p.is_active, p.availability, p.notes or ""] for p in products]
        return self._export_csv("produtos",
            ["id", "nome", "categoria", "preco", "custo_estimado", "ativo", "disponibilidade", "observacoes"], rows)

    def export_stock(self) -> str:
        items = self.db.query(StockItem).all()
        rows = [[i.id, i.name, i.category or "", i.unit_measure, i.current_quantity,
                  i.minimum_stock, i.unit_cost, i.average_cost, i.status, i.notes or ""] for i in items]
        return self._export_csv("estoque",
            ["id", "nome", "categoria", "unidade", "quantidade_atual", "estoque_minimo",
             "custo_unitario", "custo_medio", "status", "observacoes"], rows)

    def export_sales(self) -> str:
        orders = self.db.query(Order).order_by(Order.created_at.desc()).limit(1000).all()
        rows = []
        for o in orders:
            for item in o.items:
                rows.append([o.id, o.client_id, o.status, item.product_name,
                              item.quantity, item.unit_price, item.total,
                              o.created_at.isoformat()])
        return self._export_csv("vendas",
            ["pedido_id", "cliente_id", "status", "produto", "quantidade", "preco_unitario", "total", "data"], rows)

    def export_monthly_accounts(self) -> str:
        accounts = self.db.query(MonthlyAccount).order_by(MonthlyAccount.year.desc(), MonthlyAccount.month.desc()).all()
        rows = [[a.id, a.client_id, a.month, a.year, a.total, a.status,
                  a.closed_at.isoformat() if a.closed_at else "",
                  a.paid_at.isoformat() if a.paid_at else ""] for a in accounts]
        return self._export_csv("contas_mensais",
            ["id", "cliente_id", "mes", "ano", "total", "status", "fechado_em", "pago_em"], rows)

    def log_export(self, export_type: str, filename: str, user_id: Optional[int] = None, username: Optional[str] = None):
        self.audit.log(
            action="export", entity_type=export_type,
            user_id=user_id, username=username,
            details=f"Exportação {export_type}: {filename}",
        )

    # ── CSV Import ──────────────────────────────────────────────

    def import_clients(self, file_content: str, user_id: Optional[int] = None, username: Optional[str] = None) -> dict:
        reader = csv.DictReader(io.StringIO(file_content))
        required = ["nome", "telefone"]
        errors = []
        created = 0
        skipped = 0

        for i, row in enumerate(reader, start=2):
            missing = [r for r in required if not row.get(r)]
            if missing:
                errors.append(f"Linha {i}: campos obrigatórios ausentes: {', '.join(missing)}")
                skipped += 1
                continue
            try:
                client = Client(
                    name=row["nome"],
                    document=row.get("documento", "") or None,
                    phone=row["telefone"],
                    company_sector=row.get("setor", "") or None,
                    monthly_limit=float(row.get("limite_mensal", 0)) if row.get("limite_mensal") else None,
                    notes=row.get("observacoes", "") or None,
                )
                self.db.add(client)
                self.db.flush()
                created += 1
            except Exception as e:
                errors.append(f"Linha {i}: erro ao criar cliente: {str(e)}")
                skipped += 1

        self.db.commit()

        self.audit.log(
            action="import", entity_type="client",
            user_id=user_id, username=username,
            details=f"Importação de clientes: {created} criados, {skipped} ignorados, {len(errors)} erros",
        )
        return {"created": created, "skipped": skipped, "errors": errors}

    def import_products(self, file_content: str, user_id: Optional[int] = None, username: Optional[str] = None) -> dict:
        reader = csv.DictReader(io.StringIO(file_content))
        required = ["nome", "categoria", "preco"]
        errors = []
        created = 0
        skipped = 0

        for i, row in enumerate(reader, start=2):
            missing = [r for r in required if not row.get(r)]
            if missing:
                errors.append(f"Linha {i}: campos obrigatórios ausentes: {', '.join(missing)}")
                skipped += 1
                continue
            try:
                product = Product(
                    name=row["nome"],
                    category=row["categoria"],
                    price=float(row["preco"]),
                    estimated_cost=float(row.get("custo_estimado", 0)) if row.get("custo_estimado") else None,
                    is_active=row.get("ativo", "true").lower() in ("true", "1", "sim"),
                    notes=row.get("observacoes", "") or None,
                )
                self.db.add(product)
                self.db.flush()
                created += 1
            except Exception as e:
                errors.append(f"Linha {i}: erro ao criar produto: {str(e)}")
                skipped += 1

        self.db.commit()

        self.audit.log(
            action="import", entity_type="product",
            user_id=user_id, username=username,
            details=f"Importação de produtos: {created} criados, {skipped} ignorados, {len(errors)} erros",
        )
        return {"created": created, "skipped": skipped, "errors": errors}
