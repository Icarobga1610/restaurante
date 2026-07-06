from datetime import datetime, date, time
from typing import Optional, List
from pydantic import BaseModel


# === Auth ===
class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str; email: Optional[str] = None; password: str; full_name: str; role_id: int

class UserOut(BaseModel):
    id: int; username: str; email: Optional[str] = None; full_name: str
    is_active: bool; role_id: int; role_name: Optional[str] = None
    class Config: from_attributes = True

class TokenResponse(BaseModel):
    access_token: str; token_type: str = "bearer"; user: Optional[UserOut] = None

class RoleOut(BaseModel):
    id: int; name: str; description: Optional[str] = None
    class Config: from_attributes = True

# === Client ===
class ClientCreate(BaseModel):
    name: str; document: Optional[str] = None; phone: str
    company_sector: Optional[str] = None; monthly_limit: Optional[float] = None
    is_account_client: bool = False; notes: Optional[str] = None

class ClientUpdate(BaseModel):
    name: Optional[str] = None; document: Optional[str] = None; phone: Optional[str] = None
    company_sector: Optional[str] = None; status: Optional[str] = None
    monthly_limit: Optional[float] = None; is_account_client: Optional[bool] = None
    notes: Optional[str] = None

class ClientOut(BaseModel):
    id: int; name: str; document: Optional[str] = None; phone: str
    company_sector: Optional[str] = None; status: str; monthly_limit: Optional[float] = None
    is_account_client: bool = False; notes: Optional[str] = None
    created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

# === Product / Cardápio ===
class ProductCreate(BaseModel):
    name: str; category: str; price: float; estimated_cost: Optional[float] = None
    estimated_margin: Optional[float] = None; avg_prep_time_minutes: Optional[int] = None
    description: Optional[str] = None; image_url: Optional[str] = None
    is_active: bool = True; is_seasonal: bool = False; availability: str = "always"
    seasonality: Optional[dict] = None; notes: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None; category: Optional[str] = None; price: Optional[float] = None
    estimated_cost: Optional[float] = None; estimated_margin: Optional[float] = None
    avg_prep_time_minutes: Optional[int] = None; description: Optional[str] = None
    image_url: Optional[str] = None; is_active: Optional[bool] = None
    is_seasonal: Optional[bool] = None; availability: Optional[str] = None
    seasonality: Optional[dict] = None; notes: Optional[str] = None

class ProductOut(BaseModel):
    id: int; name: str; category: str; price: float
    estimated_cost: Optional[float] = None; estimated_margin: Optional[float] = None
    avg_prep_time_minutes: Optional[int] = None; description: Optional[str] = None
    image_url: Optional[str] = None; is_active: bool; is_seasonal: bool
    availability: str; seasonality: Optional[dict] = None; notes: Optional[str] = None
    created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

# === Order ===
class OrderItemCreate(BaseModel):
    product_id: int; product_name: str; quantity: float = 1.0; unit_price: float; total: float

class OrderCreate(BaseModel):
    client_id: int; tab_id: Optional[int] = None; table_id: Optional[int] = None
    notes: Optional[str] = None; items: List[OrderItemCreate]
    signature_data: Optional[str] = None

class OrderUpdate(BaseModel):
    status: Optional[str] = None; notes: Optional[str] = None

class OrderItemOut(BaseModel):
    id: int; product_id: int; product_name: str; quantity: float
    unit_price: float; total: float; created_at: datetime
    class Config: from_attributes = True

class OrderOut(BaseModel):
    id: int; client_id: int; client_name: Optional[str] = None
    user_id: int; user_name: Optional[str] = None
    tab_id: Optional[int] = None; table_id: Optional[int] = None
    status: str; preparation_time_seconds: Optional[int] = None
    notes: Optional[str] = None; total: float
    items: List[OrderItemOut] = []; created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

# === Monthly Account ===
class MonthlyAccountCreate(BaseModel):
    client_id: int; month: int; year: int
class MonthlyAccountClose(BaseModel): notes: Optional[str] = None
class MonthlyAccountPay(BaseModel):
    payment_method: str = "cash"; notes: Optional[str] = None

class MonthlyAccountItemOut(BaseModel):
    id: int; order_id: int; order_total: float; created_at: datetime
    class Config: from_attributes = True

class MonthlyAccountOut(BaseModel):
    id: int; client_id: int; client_name: Optional[str] = None; month: int; year: int
    total: float; status: str; client_is_account_client: Optional[bool] = False
    closed_at: Optional[datetime] = None
    closed_by: Optional[int] = None; closed_by_name: Optional[str] = None
    biometric_verification_id: Optional[int] = None
    biometric_verified_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None; paid_by: Optional[int] = None
    paid_by_name: Optional[str] = None; notes: Optional[str] = None
    items: List[MonthlyAccountItemOut] = []; created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

# === Biometrics ===
class BiometricEnrollRequest(BaseModel): client_id: int
class BiometricVerifyRequest(BaseModel): client_id: int; monthly_account_id: int

class BiometricProfileOut(BaseModel):
    id: int; client_id: int; client_name: Optional[str] = None; algorithm: str
    fingers_enrolled: int; is_active: bool; last_used_at: Optional[datetime] = None
    created_at: datetime
    class Config: from_attributes = True

class BiometricConsentOut(BaseModel):
    id: int; profile_id: int; purpose: str; consent_version: Optional[str] = None
    is_active: bool; granted_at: datetime; revoked_at: Optional[datetime] = None
    class Config: from_attributes = True

class BiometricEventOut(BaseModel):
    id: int; profile_id: int; event_type: str; success: bool
    match_score: Optional[int] = None; detail: Optional[str] = None
    performed_by: Optional[int] = None; ip_address: Optional[str] = None; created_at: datetime
    class Config: from_attributes = True

class BiometricVerifyResult(BaseModel):
    success: bool; message: str; account_id: Optional[int] = None
    status: Optional[str] = None; match_score: Optional[int] = None

# === Signature (legacy) ===
class SignatureCreate(BaseModel):
    monthly_account_id: int; client_id: int; signature_data: str
    signed_value: float; ip_address: Optional[str] = None; device_info: Optional[str] = None

class SignatureOut(BaseModel):
    id: int; monthly_account_id: int; client_id: int; client_name: Optional[str] = None
    user_id: int; user_name: Optional[str] = None; signed_value: float; signed_at: datetime
    ip_address: Optional[str] = None; device_info: Optional[str] = None; verification_hash: str
    class Config: from_attributes = True

# === Payment ===
class PaymentOut(BaseModel):
    id: int; monthly_account_id: int; client_id: int; user_id: int; amount: float
    payment_method: str; paid_at: datetime; notes: Optional[str] = None
    class Config: from_attributes = True

# === Audit ===
class AuditLogOut(BaseModel):
    id: int; timestamp: datetime; user_id: Optional[int] = None; username: Optional[str] = None
    action: str; entity_type: str; entity_id: Optional[int] = None
    before_state: Optional[dict] = None; after_state: Optional[dict] = None
    ip_address: Optional[str] = None; details: Optional[str] = None
    class Config: from_attributes = True

# === Insights ===
class SeasonalityMetricOut(BaseModel):
    id: int; metric_type: str; period: str; period_value: Optional[str] = None
    data: dict; calculated_at: datetime
    class Config: from_attributes = True

class InsightLogOut(BaseModel):
    id: int; insight_type: str; title: str; description: Optional[str] = None
    severity: str; data: Optional[dict] = None; is_active: int; created_at: datetime
    class Config: from_attributes = True

# === Supplier ===
class SupplierCreate(BaseModel):
    name: str; cnpj: Optional[str] = None; phone: Optional[str] = None
    whatsapp: Optional[str] = None; email: Optional[str] = None; address: Optional[str] = None
    category: Optional[str] = None; notes: Optional[str] = None

class SupplierUpdate(BaseModel):
    name: Optional[str] = None; cnpj: Optional[str] = None; phone: Optional[str] = None
    whatsapp: Optional[str] = None; email: Optional[str] = None; address: Optional[str] = None
    category: Optional[str] = None; notes: Optional[str] = None; status: Optional[str] = None

class SupplierOut(BaseModel):
    id: int; name: str; cnpj: Optional[str] = None; phone: Optional[str] = None
    whatsapp: Optional[str] = None; email: Optional[str] = None; address: Optional[str] = None
    category: Optional[str] = None; notes: Optional[str] = None; status: str
    created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

# === Stock Item ===
class StockItemCreate(BaseModel):
    name: str; category: Optional[str] = None; unit_measure: str = "unidade"
    current_quantity: float = 0; minimum_stock: float = 0; unit_cost: float = 0
    supplier_id: Optional[int] = None; expiry_date: Optional[date] = None; notes: Optional[str] = None

class StockItemUpdate(BaseModel):
    name: Optional[str] = None; category: Optional[str] = None; unit_measure: Optional[str] = None
    current_quantity: Optional[float] = None; minimum_stock: Optional[float] = None
    unit_cost: Optional[float] = None; supplier_id: Optional[int] = None
    expiry_date: Optional[date] = None; notes: Optional[str] = None; status: Optional[str] = None

class StockItemOut(BaseModel):
    id: int; name: str; category: Optional[str] = None; unit_measure: str
    current_quantity: float; minimum_stock: float; unit_cost: float; average_cost: float
    supplier_id: Optional[int] = None; supplier_name: Optional[str] = None
    expiry_date: Optional[date] = None; status: str; notes: Optional[str] = None
    created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

# === Stock Movement ===
class StockMovementCreate(BaseModel):
    stock_item_id: int; movement_type: str; quantity: float
    unit_cost: Optional[float] = None; reference_id: Optional[int] = None
    reference_type: Optional[str] = None; notes: Optional[str] = None

class StockMovementOut(BaseModel):
    id: int; stock_item_id: int; stock_item_name: Optional[str] = None
    movement_type: str; quantity: float; unit_cost: Optional[float] = None
    total_cost: Optional[float] = None; reference_id: Optional[int] = None
    reference_type: Optional[str] = None; notes: Optional[str] = None
    performed_by: Optional[int] = None; performer_name: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True

# === Product Recipe ===
class RecipeItemCreate(BaseModel):
    stock_item_id: int; quantity_required: float; unit_measure: str; cost: float = 0

class RecipeCreate(BaseModel):
    product_id: int; items: List[RecipeItemCreate]; notes: Optional[str] = None

class RecipeItemOut(BaseModel):
    id: int; stock_item_id: int; stock_item_name: Optional[str] = None
    quantity_required: float; unit_measure: str; cost: float
    class Config: from_attributes = True

class RecipeOut(BaseModel):
    id: int; product_id: int; product_name: Optional[str] = None
    total_cost: float; estimated_margin: Optional[float] = None
    version: int; notes: Optional[str] = None; items: List[RecipeItemOut] = []
    created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

# === Purchase ===
class PurchaseItemCreate(BaseModel):
    stock_item_id: int; quantity: float; unit_cost: float; total_cost: float

class PurchaseCreate(BaseModel):
    supplier_id: Optional[int] = None; invoice_number: Optional[str] = None
    payment_method: str = "cash"; status: str = "planned"
    items: List[PurchaseItemCreate]; notes: Optional[str] = None

class PurchaseItemOut(BaseModel):
    id: int; stock_item_id: int; stock_item_name: Optional[str] = None
    quantity: float; unit_cost: float; total_cost: float
    class Config: from_attributes = True

class PurchaseOut(BaseModel):
    id: int; supplier_id: Optional[int] = None; supplier_name: Optional[str] = None
    purchase_date: datetime; invoice_number: Optional[str] = None
    total_cost: float; payment_method: str; status: str
    notes: Optional[str] = None; created_by: Optional[int] = None
    items: List[PurchaseItemOut] = []; created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

# === Table ===
class TableCreate(BaseModel):
    number: int; capacity: int = 4; notes: Optional[str] = None

class TableUpdate(BaseModel):
    number: Optional[int] = None; capacity: Optional[int] = None
    status: Optional[str] = None; client_id: Optional[int] = None; notes: Optional[str] = None

class TableOut(BaseModel):
    id: int; number: int; capacity: int; status: str
    client_id: Optional[int] = None; client_name: Optional[str] = None
    opened_at: Optional[datetime] = None; closed_at: Optional[datetime] = None
    notes: Optional[str] = None; created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

# === Tab (Comanda) ===
class TabItemCreate(BaseModel):
    product_id: int; product_name: str; quantity: float = 1.0
    unit_price: float; total: float; notes: Optional[str] = None

class TabCreate(BaseModel):
    table_id: Optional[int] = None; client_id: Optional[int] = None
    notes: Optional[str] = None; items: List[TabItemCreate]

class TabItemOut(BaseModel):
    id: int; product_id: int; product_name: str; quantity: float
    unit_price: float; total: float; notes: Optional[str] = None; created_at: datetime
    class Config: from_attributes = True

class TabOut(BaseModel):
    id: int; table_id: Optional[int] = None; table_number: Optional[int] = None
    client_id: Optional[int] = None; client_name: Optional[str] = None
    user_id: int; user_name: Optional[str] = None
    total: float; status: str; notes: Optional[str] = None
    opened_at: datetime; closed_at: Optional[datetime] = None
    items: List[TabItemOut] = []; created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

# === Cash Register ===
class CashRegisterCreate(BaseModel):
    opening_balance: float = 0; notes: Optional[str] = None

class CashMovementCreate(BaseModel):
    movement_type: str; description: Optional[str] = None; amount: float
    payment_method: Optional[str] = None; reference_id: Optional[int] = None
    reference_type: Optional[str] = None; notes: Optional[str] = None

class CashMovementOut(BaseModel):
    id: int; movement_type: str; description: Optional[str] = None; amount: float
    payment_method: Optional[str] = None; reference_id: Optional[int] = None
    reference_type: Optional[str] = None; performer_name: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True

class CashRegisterOut(BaseModel):
    id: int; date: date; opening_balance: float; expected_closing: float
    informed_closing: Optional[float] = None; difference: Optional[float] = None
    status: str; opened_by: int; opener_name: Optional[str] = None
    closed_by: Optional[int] = None; closer_name: Optional[str] = None
    opened_at: datetime; closed_at: Optional[datetime] = None
    notes: Optional[str] = None; movements: List[CashMovementOut] = []
    class Config: from_attributes = True

# === Expense ===
class ExpenseCreate(BaseModel):
    description: str; category: str; amount: float
    expense_date: date; payment_method: str = "cash"
    supplier_id: Optional[int] = None; notes: Optional[str] = None

class ExpenseOut(BaseModel):
    id: int; description: str; category: str; amount: float
    expense_date: date; payment_method: str
    supplier_id: Optional[int] = None; supplier_name: Optional[str] = None
    notes: Optional[str] = None; created_by: Optional[int] = None
    creator_name: Optional[str] = None; created_at: datetime
    class Config: from_attributes = True

# === Kitchen Order ===
class KitchenOrderUpdate(BaseModel):
    status: str; notes: Optional[str] = None

class KitchenOrderOut(BaseModel):
    id: int; order_id: int; product_id: int; product_name: str
    quantity: float; status: str; notes: Optional[str] = None
    preparation_time_seconds: Optional[int] = None
    started_at: Optional[datetime] = None; completed_at: Optional[datetime] = None
    assigned_to: Optional[int] = None; assignee_name: Optional[str] = None
    created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

# === Dashboard ===
class DashboardData(BaseModel):
    # Operação
    total_tables: int = 0; open_tables: int = 0
    orders_in_preparation: int = 0; open_tabs: int = 0
    # Financeiro
    day_revenue: float = 0; month_revenue_open: float = 0
    month_revenue_paid: float = 0; month_revenue_pending: float = 0
    month_expenses: float = 0; estimated_gross_profit: float = 0
    # Estoque
    low_stock_items: int = 0; expiring_items: int = 0
    unavailable_products: int = 0
    # Vendas
    active_clients: int = 0; total_products: int = 0
    total_orders_month: int = 0; top_clients: List[dict] = []
    top_products: List[dict] = []; average_ticket: float = 0
    consumption_by_day: List[dict] = []; consumption_by_category: List[dict] = []
    # Contas
    overdue_accounts: int = 0; unsigned_accounts: int = 0
    # Biometria
    biometric_clients: int = 0; biometric_confirmations: int = 0
    biometric_failures: int = 0
    # Módulos adicionais
    pending_deliveries: int = 0
    month_losses: float = 0
    month_courtesies: float = 0
    discounts_applied: int = 0
    low_stock_count: int = 0
    last_backup: Optional[str] = None
    has_settings: bool = False


# === Restaurant Settings ===
class RestaurantSettingsUpdate(BaseModel):
    restaurant_name: Optional[str] = None
    cnpj: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    opening_hours: Optional[str] = None
    service_fee_percent: Optional[float] = None
    delivery_fee_default: Optional[float] = None
    default_monthly_limit: Optional[float] = None
    default_due_days: Optional[int] = None
    logo_url: Optional[str] = None
    cancellation_policy: Optional[str] = None

class RestaurantSettingsOut(BaseModel):
    id: int
    restaurant_name: str
    cnpj: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    opening_hours: Optional[str] = None
    service_fee_percent: float = 0
    delivery_fee_default: float = 0
    default_monthly_limit: float = 500
    default_due_days: int = 30
    logo_url: Optional[str] = None
    cancellation_policy: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


# === Delivery ===
class DeliveryAddressCreate(BaseModel):
    client_id: int
    label: Optional[str] = None
    street: str
    number: Optional[str] = None
    neighborhood: Optional[str] = None
    city: str = "São Paulo"
    state: str = "SP"
    reference: Optional[str] = None
    is_default: bool = False

class DeliveryAddressOut(BaseModel):
    id: int
    client_id: int
    label: Optional[str] = None
    street: str
    number: Optional[str] = None
    neighborhood: Optional[str] = None
    city: str
    state: str
    reference: Optional[str] = None
    is_default: bool
    created_at: datetime
    class Config: from_attributes = True

class DeliveryEventOut(BaseModel):
    id: int
    order_id: int
    status: str
    notes: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True


# === Promotions ===
class PromotionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    promotion_type: str
    discount_type: str
    discount_value: float
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    day_of_week: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    active: bool = True

class PromotionOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    promotion_type: str
    discount_type: str
    discount_value: float
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    day_of_week: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    active: bool
    created_at: datetime
    class Config: from_attributes = True

class CouponCreate(BaseModel):
    code: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    max_uses: int = 0
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    active: bool = True

class CouponOut(BaseModel):
    id: int
    code: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    max_uses: int
    current_uses: int
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    active: bool
    created_at: datetime
    class Config: from_attributes = True

class CouponValidateRequest(BaseModel):
    code: str

class DiscountApplyRequest(BaseModel):
    coupon_code: Optional[str] = None
    discount_value: Optional[float] = None
    reason: Optional[str] = None
    order_id: int

class ComboItemCreate(BaseModel):
    product_id: int
    quantity: float = 1.0

class ComboCreate(BaseModel):
    combo_product_id: int
    items: List[ComboItemCreate]

class ComboItemOut(BaseModel):
    id: int
    combo_product_id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    created_at: datetime
    class Config: from_attributes = True

class DiscountLogOut(BaseModel):
    id: int
    order_id: Optional[int] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    discount_type: str
    discount_value: float
    reason: str
    coupon_id: Optional[int] = None
    promotion_id: Optional[int] = None
    created_at: datetime
    class Config: from_attributes = True


# === Loss Records ===
class LossRecordCreate(BaseModel):
    stock_item_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: float
    unit_measure: str = "unidade"
    estimated_cost: float = 0
    loss_type: str
    reason: str

class LossRecordOut(BaseModel):
    id: int
    stock_item_id: Optional[int] = None
    stock_item_name: Optional[str] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: float
    unit_measure: str
    estimated_cost: float
    loss_type: str
    reason: str
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True


# === Internal Consumption ===
class InternalConsumptionCreate(BaseModel):
    consumption_type: str
    client_id: Optional[int] = None
    employee_name: Optional[str] = None
    product_id: int
    quantity: float = 1.0
    estimated_cost: float = 0
    reason: str
    authorized_by_user_id: int

class InternalConsumptionOut(BaseModel):
    id: int
    consumption_type: str
    client_id: Optional[int] = None
    client_name: Optional[str] = None
    employee_name: Optional[str] = None
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    estimated_cost: float
    reason: str
    authorized_by_user_id: Optional[int] = None
    authorized_by_name: Optional[str] = None
    created_by_user_id: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True


# === Permissions ===
class PermissionOut(BaseModel):
    id: int
    key: str
    description: Optional[str] = None
    module: str
    created_at: datetime
    class Config: from_attributes = True

class RolePermissionUpdate(BaseModel):
    role_id: int
    permission_ids: List[int]


# === Backup ===
class BackupInfo(BaseModel):
    filename: str
    size: int
    modified_at: str

class ImportResult(BaseModel):
    created: int
    skipped: int
    errors: List[str] = []
