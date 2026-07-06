from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.permission import Permission, RolePermission
from app.services.audit_service import AuditService


class PermissionService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def get_user_permissions(self, user: User) -> List[str]:
        """Get all permission keys for a user based on their role."""
        role_perms = self.db.query(RolePermission).filter(
            RolePermission.role_id == user.role_id
        ).all()
        perm_ids = [rp.permission_id for rp in role_perms]
        perms = self.db.query(Permission).filter(
            Permission.id.in_(perm_ids)
        ).all()
        return [p.key for p in perms]

    def check_permission(self, user: User, permission_key: str) -> bool:
        """Check if user has a specific permission."""
        # Admin roles have all permissions
        role_name = user.role.name if user.role else ""
        if role_name in ("admin", "dono_gerente", "administrador"):
            return True
        user_perms = self.get_user_permissions(user)
        return permission_key in user_perms

    def seed_default_permissions(self):
        """Seed default permissions and assign them to admin roles."""
        existing = self.db.query(Permission).count()
        if existing > 0:
            return

        permissions_data = [
            # Clientes
            ("clients.read", "Visualizar clientes", "clientes"),
            ("clients.create", "Criar clientes", "clientes"),
            ("clients.update", "Editar clientes", "clientes"),
            ("clients.disable", "Desativar clientes", "clientes"),
            # Produtos
            ("products.read", "Visualizar produtos", "produtos"),
            ("products.create", "Criar produtos", "produtos"),
            ("products.update", "Editar produtos", "produtos"),
            ("products.disable", "Desativar produtos", "produtos"),
            # Estoque
            ("stock.read", "Visualizar estoque", "estoque"),
            ("stock.create", "Criar itens de estoque", "estoque"),
            ("stock.update", "Editar itens de estoque", "estoque"),
            ("stock.adjust", "Ajustar estoque manualmente", "estoque"),
            ("stock.loss", "Registrar perda de estoque", "estoque"),
            # Pedidos
            ("orders.read", "Visualizar pedidos", "pedidos"),
            ("orders.create", "Criar pedidos", "pedidos"),
            ("orders.cancel", "Cancelar pedidos", "pedidos"),
            ("orders.discount", "Aplicar descontos", "pedidos"),
            # Caixa
            ("cash.read", "Visualizar caixa", "caixa"),
            ("cash.open", "Abrir caixa", "caixa"),
            ("cash.close", "Fechar caixa", "caixa"),
            ("cash.movement", "Registrar movimentos de caixa", "caixa"),
            # Financeiro
            ("finance.read", "Visualizar financeiro", "financeiro"),
            ("finance.payments", "Registrar pagamentos", "financeiro"),
            ("finance.monthly_accounts", "Gerenciar contas mensais", "financeiro"),
            ("finance.refund", "Realizar estornos", "financeiro"),
            # Biometria
            ("biometrics.read", "Visualizar dados biométricos", "biometria"),
            ("biometrics.enroll", "Cadastrar biometria", "biometria"),
            ("biometrics.verify", "Verificar biometria", "biometria"),
            ("biometrics.revoke", "Revogar biometria", "biometria"),
            # Configurações
            ("settings.read", "Visualizar configurações", "configuracoes"),
            ("settings.update", "Editar configurações", "configuracoes"),
            # Relatórios
            ("reports.read", "Visualizar relatórios", "relatorios"),
            ("reports.export", "Exportar relatórios", "relatorios"),
            # Backup
            ("backup.create", "Criar backup", "backup"),
            ("backup.restore", "Restaurar backup", "backup"),
            ("backup.export", "Exportar dados", "backup"),
            ("backup.import", "Importar dados", "backup"),
        ]

        perms = []
        for key, desc, mod in permissions_data:
            perm = Permission(key=key, description=desc, module=mod)
            self.db.add(perm)
            perms.append(perm)
        self.db.flush()

        # Get admin roles and assign all permissions
        from app.models.user import Role
        admin_role_names = ["admin", "dono_gerente", "administrador"]
        admin_roles = self.db.query(Role).filter(
            Role.name.in_(admin_role_names)
        ).all()

        for role in admin_roles:
            for perm in perms:
                rp = RolePermission(role_id=role.id, permission_id=perm.id)
                self.db.add(rp)

        self.db.commit()
