from datetime import datetime
from app.utils import utcnow
from typing import Optional
from sqlalchemy.orm import Session
from app.models.promotion import Promotion, Coupon, ComboItem, DiscountLog
from app.models.order import Order
from app.services.audit_service import AuditService


class PromotionService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    # ── Promotions ──────────────────────────────────────────────

    def create_promotion(self, data: dict, user_id: int, username: str) -> Promotion:
        promo = Promotion(**data)
        self.db.add(promo)
        self.db.commit()
        self.db.refresh(promo)
        self.audit.log(
            action="create", entity_type="promotion", entity_id=promo.id,
            user_id=user_id, username=username,
            details=f"Promoção '{promo.name}' criada",
        )
        return promo

    def toggle_promotion(self, promo_id: int, active: bool, user_id: int, username: str) -> Promotion:
        promo = self.db.query(Promotion).filter(Promotion.id == promo_id).first()
        if not promo:
            raise ValueError("Promoção não encontrada")
        promo.active = active
        self.db.commit()
        self.db.refresh(promo)
        self.audit.log(
            action="update", entity_type="promotion", entity_id=promo.id,
            user_id=user_id, username=username,
            details=f"Promoção '{promo.name}' {'ativada' if active else 'inativada'}",
        )
        return promo

    # ── Coupons ─────────────────────────────────────────────────

    def create_coupon(self, data: dict, user_id: int, username: str) -> Coupon:
        coupon = Coupon(**data)
        self.db.add(coupon)
        self.db.commit()
        self.db.refresh(coupon)
        self.audit.log(
            action="create", entity_type="coupon", entity_id=coupon.id,
            user_id=user_id, username=username,
            details=f"Cupom '{coupon.code}' criado",
        )
        return coupon

    def validate_coupon(self, code: str) -> dict:
        """Validate coupon and return discount info or error."""
        coupon = self.db.query(Coupon).filter(Coupon.code == code).first()
        if not coupon:
            return {"valid": False, "error": "Cupom não encontrado"}
        if not coupon.active:
            return {"valid": False, "error": "Cupom inativo"}
        now = utcnow()
        if coupon.starts_at and now < coupon.starts_at:
            return {"valid": False, "error": "Cupom ainda não está válido"}
        if coupon.ends_at and now > coupon.ends_at:
            return {"valid": False, "error": "Cupom expirado"}
        if coupon.max_uses > 0 and coupon.current_uses >= coupon.max_uses:
            return {"valid": False, "error": "Cupom esgotado"}
        return {
            "valid": True,
            "coupon_id": coupon.id,
            "discount_type": coupon.discount_type,
            "discount_value": coupon.discount_value,
        }

    def apply_coupon(self, coupon_id: int, order_id: int, user_id: int, username: str) -> dict:
        coupon = self.db.query(Coupon).filter(Coupon.id == coupon_id).first()
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not coupon or not order:
            raise ValueError("Cupom ou pedido não encontrado")

        discount_value = coupon.discount_value
        if coupon.discount_type == "percentual":
            discount_value = round(order.total * coupon.discount_value / 100, 2)

        coupon.current_uses += 1
        order.discount = (order.discount or 0) + discount_value
        order.total = max(0, order.total - discount_value)
        self.db.commit()

        log = DiscountLog(
            order_id=order_id, user_id=user_id,
            discount_type="cupom", discount_value=discount_value,
            reason=f"Cupom {coupon.code}", coupon_id=coupon.id,
        )
        self.db.add(log)
        self.db.commit()

        self.audit.log(
            action="update", entity_type="order", entity_id=order_id,
            user_id=user_id, username=username,
            details=f"Desconto de R$ {discount_value:.2f} aplicado via cupom {coupon.code}",
        )
        return {"discount": discount_value, "new_total": order.total}

    # ── Manual Discount ─────────────────────────────────────────

    def apply_manual_discount(
        self, order_id: int, discount_value: float, reason: str,
        user_id: int, username: str,
    ) -> dict:
        if not reason or len(reason.strip()) < 3:
            raise ValueError("Desconto manual exige um motivo com pelo menos 3 caracteres")

        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Pedido não encontrado")

        order.discount = (order.discount or 0) + discount_value
        order.total = max(0, order.total - discount_value)
        self.db.commit()

        log = DiscountLog(
            order_id=order_id, user_id=user_id,
            discount_type="manual", discount_value=discount_value,
            reason=reason,
        )
        self.db.add(log)
        self.db.commit()

        self.audit.log(
            action="update", entity_type="order", entity_id=order_id,
            user_id=user_id, username=username,
            details=f"Desconto manual de R$ {discount_value:.2f}: {reason}",
        )
        return {"discount": discount_value, "new_total": order.total}

    # ── Combos ──────────────────────────────────────────────────

    def create_combo(self, combo_product_id: int, items: list[dict]) -> list[ComboItem]:
        created = []
        for item in items:
            combo_item = ComboItem(
                combo_product_id=combo_product_id,
                product_id=item["product_id"],
                quantity=item.get("quantity", 1.0),
            )
            self.db.add(combo_item)
            created.append(combo_item)
        self.db.commit()
        for ci in created:
            self.db.refresh(ci)
        return created
