from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from fastapi.responses import HTMLResponse

from app.database import get_db
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.tab import Tab, TabItem
from app.models.monthly_account import MonthlyAccount, MonthlyAccountItem
from app.models.payment import Payment
from app.models.cash_register import CashRegister, CashMovement
from app.auth.auth import get_current_user

router = APIRouter(prefix="/api/print", tags=["Print"])

RECEIPT_CSS = """
<style>
  @page { margin: 0; size: 80mm auto; }
  body { font-family: 'Courier New', monospace; font-size: 12px;
         width: 80mm; margin: 0 auto; padding: 8px; color: #000; }
  h2 { text-align: center; font-size: 14px; margin: 4px 0; }
  h3 { text-align: center; font-size: 12px; margin: 4px 0; }
  .info { text-align: center; font-size: 10px; margin: 2px 0; }
  hr { border: none; border-top: 1px dashed #000; margin: 6px 0; }
  table { width: 100%; font-size: 11px; border-collapse: collapse; }
  th { text-align: left; border-bottom: 1px solid #000; padding: 2px 0; }
  td { padding: 2px 0; }
  .right { text-align: right; }
  .center { text-align: center; }
  .total-row { font-weight: bold; font-size: 13px; border-top: 1px solid #000; }
  .footer { text-align: center; font-size: 10px; margin-top: 8px; }
  .btn-print { display: block; margin: 16px auto; padding: 10px 24px;
               font-size: 14px; cursor: pointer; background: #2563eb;
               color: #fff; border: none; border-radius: 6px; }
  @media print { .btn-print { display: none; } }
</style>
"""


def _receipt_html(content: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Comprovante</title>{RECEIPT_CSS}</head>
<body>
  <button class="btn-print" onclick="window.print()">🖨️ Imprimir</button>
  {content}
  <p class="footer">Impresso em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
  <button class="btn-print" onclick="window.print()">🖨️ Imprimir</button>
</body></html>"""


@router.get("/kitchen-order/{order_id}", response_class=HTMLResponse)
def print_kitchen_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = db.query(Order).options(
        joinedload(Order.client), joinedload(Order.items)
    ).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    items_html = "".join(
        f"<tr><td>{i.product_name}</td><td class='center'>{i.quantity:.1f}</td><td class='right'>R$ {i.unit_price:.2f}</td></tr>"
        for i in order.items
    )

    content = f"""
    <h2>🛎️ PEDIDO COZINHA</h2>
    <hr>
    <div class='info'>Pedido #{order.id}</div>
    <div class='info'>Cliente: {order.client.name if order.client else '-'}</div>
    <div class='info'>{order.created_at.strftime('%d/%m/%Y %H:%M')}</div>
    <hr>
    <table><thead><tr><th>Item</th><th class='center'>Qtd</th><th class='right'>Valor</th></tr></thead>
    <tbody>{items_html}</tbody></table>
    <hr>
    <div class='info'>Total: R$ {order.total:.2f}</div>
    {f"<div class='info'>Obs: {order.notes}</div>" if order.notes else ""}
    """
    return HTMLResponse(_receipt_html(content))


@router.get("/tab/{tab_id}", response_class=HTMLResponse)
def print_tab(tab_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    tab = db.query(Tab).options(
        joinedload(Tab.client), joinedload(Tab.items)
    ).filter(Tab.id == tab_id).first()
    if not tab:
        raise HTTPException(status_code=404, detail="Comanda não encontrada")

    items_html = "".join(
        f"<tr><td>{i.product_name}</td><td class='center'>{i.quantity:.1f}</td><td class='right'>R$ {i.total:.2f}</td></tr>"
        for i in tab.items
    )

    content = f"""
    <h2>📋 COMANDA</h2>
    <hr>
    <div class='info'>Comanda #{tab.id}</div>
    <div class='info'>Cliente: {tab.client.name if tab.client else '-'}</div>
    <div class='info'>{tab.opened_at.strftime('%d/%m/%Y %H:%M')}</div>
    <hr>
    <table><thead><tr><th>Item</th><th class='center'>Qtd</th><th class='right'>Total</th></tr></thead>
    <tbody>{items_html}</tbody></table>
    <hr>
    <div class='total-row center'>TOTAL: R$ {tab.total:.2f}</div>
    """
    return HTMLResponse(_receipt_html(content))


@router.get("/monthly-account/{account_id}", response_class=HTMLResponse)
def print_monthly_account(account_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    account = db.query(MonthlyAccount).options(
        joinedload(MonthlyAccount.client), joinedload(MonthlyAccount.items)
    ).filter(MonthlyAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta mensal não encontrada")

    items_html = "".join(
        f"<tr><td>Pedido #{i.order_id}</td><td class='right'>R$ {i.order_total:.2f}</td></tr>"
        for i in account.items
    )

    content = f"""
    <h2>📄 CONTA MENSAL</h2>
    <hr>
    <div class='info'>Cliente: {account.client.name if account.client else '-'}</div>
    <div class='info'>{account.month:02d}/{account.year}</div>
    <div class='info'>Status: {account.status}</div>
    <hr>
    <table><thead><tr><th>Pedido</th><th class='right'>Valor</th></tr></thead>
    <tbody>{items_html}</tbody></table>
    <hr>
    <div class='total-row center'>TOTAL: R$ {account.total:.2f}</div>
    {f"<div class='info'>Fechado: {account.closed_at.strftime('%d/%m/%Y %H:%M')}</div>" if account.closed_at else ""}
    {f"<div class='info'>Pago: {account.paid_at.strftime('%d/%m/%Y %H:%M')}</div>" if account.paid_at else ""}
    """
    return HTMLResponse(_receipt_html(content))


@router.get("/payment/{payment_id}", response_class=HTMLResponse)
def print_payment(payment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    payment = db.query(Payment).options(
        joinedload(Payment.client), joinedload(Payment.user),
        joinedload(Payment.monthly_account)
    ).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    content = f"""
    <h2>💰 RECIBO DE PAGAMENTO</h2>
    <hr>
    <div class='info'>Recibo #{payment.id}</div>
    <div class='info'>Cliente: {payment.client.name if payment.client else '-'}</div>
    <div class='info'>Conta Mensal: #{payment.monthly_account_id}</div>
    <div class='info'>Período: {payment.monthly_account.month:02d}/{payment.monthly_account.year if payment.monthly_account else ''}</div>
    <hr>
    <div class='info'>Valor: <strong>R$ {payment.amount:.2f}</strong></div>
    <div class='info'>Forma: {payment.payment_method}</div>
    <div class='info'>Pago em: {payment.paid_at.strftime('%d/%m/%Y %H:%M')}</div>
    <div class='info'>Atendente: {payment.user.full_name if payment.user else '-'}</div>
    {f"<div class='info'>Obs: {payment.notes}</div>" if payment.notes else ""}
    """
    return HTMLResponse(_receipt_html(content))


@router.get("/cash-register/{cash_register_id}", response_class=HTMLResponse)
def print_cash_register(cash_register_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    cr = db.query(CashRegister).options(
        joinedload(CashRegister.opener), joinedload(CashRegister.closer),
        joinedload(CashRegister.movements)
    ).filter(CashRegister.id == cash_register_id).first()
    if not cr:
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    movements_html = "".join(
        f"<tr><td>{m.movement_type}</td><td class='right'>R$ {m.amount:.2f}</td></tr>"
        for m in cr.movements
    )

    content = f"""
    <h2>🧾 FECHAMENTO DE CAIXA</h2>
    <hr>
    <div class='info'>Caixa #{cr.id}</div>
    <div class='info'>Data: {cr.date.strftime('%d/%m/%Y')}</div>
    <hr>
    <div class='info'>Abertura: R$ {cr.opening_balance:.2f}</div>
    <div class='info'>Fechamento esperado: R$ {cr.expected_closing:.2f}</div>
    {f"<div class='info'>Fechamento informado: R$ {cr.informed_closing:.2f}</div>" if cr.informed_closing is not None else ""}
    {f"<div class='info'>Diferença: R$ {cr.difference:.2f}</div>" if cr.difference is not None else ""}
    <hr>
    <h3>Movimentações</h3>
    <table><thead><tr><th>Tipo</th><th class='right'>Valor</th></tr></thead>
    <tbody>{movements_html}</tbody></table>
    <hr>
    <div class='info'>Aberto por: {cr.opener.full_name if cr.opener else '-'}</div>
    {f"<div class='info'>Fechado por: {cr.closer.full_name if cr.closer else '-'}</div>" if cr.closed_by else ""}
    """
    return HTMLResponse(_receipt_html(content))
