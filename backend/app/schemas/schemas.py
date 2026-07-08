from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, field_validator
import re


# === Auth ===
class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    full_name: str
    role_id: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: Optional[str] = None
    full_name: str
    is_active: bool
    role_id: int
    role_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserOut] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None


# === Client ===
class ClientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    document: Optional[str] = None
    phone: str
    company_sector: Optional[str] = None
    monthly_limit: Optional[float] = None
    is_account_client: bool = False
    payment_day: Optional[int] = None
    notes: Optional[str] = None
    
    @field_validator('document')
    @classmethod
    def validate_document(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = re.sub(r'[^0-9]', '', v)
        if clean and len(clean) not in (11, 14):
            raise ValueError('Document must be CPF (11 digits) or CNPJ (14 digits)')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        clean = re.sub(r'[^0-9]', '', v)
        if len(clean) not in (10, 11):
            raise ValueError('Phone must have 10 or 11 digits')
        return v


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    document: Optional[str] = None
    phone: Optional[str] = None
    company_sector: Optional[str] = None
    status: Optional[str] = None
    monthly_limit: Optional[float] = None
    is_account_client: Optional[bool] = None
    payment_day: Optional[int] = None
    notes: Optional[str] = None


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    document: Optional[str] = None
    phone: str
    company_sector: Optional[str] = None
    status: str
    monthly_limit: Optional[float] = None
    is_account_client: bool = False
    payment_day: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# === Product / Cardápio ===
class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category: str
    price: float
    estimated_cost: Optional[float] = None
    estimated_margin: Optional[float] = None
    avg_prep_time_minutes: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True
    is_seasonal: bool = False
    availability: str = "always"
    seasonality: Optional[dict] = None
    notes: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    estimated_cost: Optional[float] = None
    estimated_margin: Optional[float] = None
    avg_prep_time_minutes: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_seasonal: Optional[bool] = None
    availability: Optional[str] = None
    seasonality: Optional[dict] = None
    notes: Optional[str] = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    category: str
    price: float
    estimated_cost: Optional[float] = None
    estimated_margin: Optional[float] = None
    avg_prep_time_minutes: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool
    is_seasonal: bool
    availability: str
    seasonality: Optional[dict] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# === Order ===
class OrderItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int
    product_name: str
    quantity: float = 1.0
    unit_price: float
    total: float


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: int
    tab_id: Optional[int] = None
    monthly_account_id: Optional[int] = None
    table_id: Optional[int] = None
    notes: Optional[str] = None
    items: List[OrderItemCreate]
    payment_mode: str = "monthly_account"
    confirm_with_biometric: bool = False
    biometric_verification_token: Optional[str] = None
    signature_data: Optional[str] = None


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    product_id: int
    product_name: str
    quantity: float
    unit_price: float
    total: float
    created_at: datetime


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    client_id: int
    client_name: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    tab_id: Optional[int] = None
    table_id: Optional[int] = None
    status: str
    preparation_time_seconds: Optional[int] = None
    notes: Optional[str] = None
    total: float
    items: List[OrderItemOut] = []
    created_at: datetime
    updated_at: datetime


# === Monthly Account ===
class MonthlyAccountCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: int
    month: int
    year: int


class MonthlyAccountClose(BaseModel):
    notes: Optional[str] = None


class MonthlyAccountPay(BaseModel):
    payment_method: str = "cash"
    notes: Optional[str] = None
    signature_data: Optional[str] = None


class MonthlyAccountItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    order_id: int
    order_total: float
    created_at: datetime


class MonthlyAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    client_id: int
    client_name: Optional[str] = None
    month: int
    year: int
    total: float
    status: str
    client_is_account_client: Optional[bool] = False
    due_date: Optional[date] = None
    closed_at: Optional[datetime] = None
    closed_by: Optional[int] = None
    closed_by_name: Optional[str] = None
    biometric_verification_id: Optional[int] = None
    biometric_verified_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    paid_by: Optional[int] = None
    paid_by_name: Optional[str] = None
    notes: Optional[str] = None
    over_limit: Optional[bool] = False
    items: List[MonthlyAccountItemOut] = []
    created_at: datetime
    updated_at: datetime


# === Payment ===
class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    monthly_account_id: int
    client_id: int
    user_id: int
    amount: float
    payment_method: str
    paid_at: datetime
    notes: Optional[str] = None
    created_at: datetime


# === Signature ===
class SignatureCreate(BaseModel):
    monthly_account_id: int
    client_id: int
    signature_data: str
    signed_value: Optional[float] = None
    ip_address: Optional[str] = None
    device_info: Optional[str] = None


class SignatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    monthly_account_id: int
    client_id: int
    user_id: int
    signature_data: str
    signed_value: float
    signed_at: datetime
    ip_address: Optional[str] = None
    device_info: Optional[str] = None
    verification_hash: str
    created_at: datetime


# === Biometrics ===
class BiometricEnrollRequest(BaseModel):
    client_id: int


class BiometricVerifyRequest(BaseModel):
    client_id: int
    monthly_account_id: int


class WebAuthnOptionsRequest(BaseModel):
    client_id: int


class WebAuthnEnrollComplete(BaseModel):
    client_id: int
    credential_id: str
    raw_id: str
    type: str
    response: dict


class WebAuthnVerifyComplete(BaseModel):
    client_id: int
    credential_id: str
    type: str
    response: dict


class BiometricProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    client_id: int
    client_name: Optional[str] = None
    algorithm: str
    fingers_enrolled: int
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime


class BiometricConsentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    profile_id: int
    purpose: str
    consent_version: Optional[str] = None
    is_active: bool
    granted_at: datetime
    revoked_at: Optional[datetime] = None


class BiometricEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    profile_id: int
    event_type: str
    success: bool
    match_score: Optional[int] = None
    detail: Optional[str] = None
    performed_by: Optional[int] = None
    ip_address: Optional[str] = None
    created_at: datetime


class BiometricVerifyResult(BaseModel):
    success: bool
    message: str
    account_id: int
    status: str
    match_score: Optional[int] = None


# === Dashboard ===
class DashboardData(BaseModel):
    """Dashboard data response model."""
    month_revenue_open: float = 0.0
    month_revenue_paid: float = 0.0
    month_revenue_pending: float = 0.0
    active_clients: int = 0
    total_products: int = 0
    total_orders_month: int = 0
    top_clients: List[Dict[str, Any]] = []
    top_products: List[Dict[str, Any]] = []
    average_ticket: float = 0.0
    consumption_by_day: List[Dict[str, Any]] = []
    consumption_by_category: List[Dict[str, Any]] = []
    overdue_accounts: int = 0
    unsigned_accounts: int = 0


# === Insights ===
class SeasonalityMetricOut(BaseModel):
    """Seasonality metric output."""
    metric: str
    value: float
    period: str
    category: Optional[str] = None
    timestamp: datetime


class InsightLogOut(BaseModel):
    """Insight log output."""
    id: int
    insight_type: str
    title: str
    description: Optional[str] = None
    severity: str = "info"
    data: Optional[dict] = None
    is_active: int = 1
    created_at: datetime


# === Cash Register ===
class CashRegisterCreate(BaseModel):
    opening_balance: float = 0.0
    notes: Optional[str] = None


class CashRegisterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    opening_balance: float
    closing_balance: Optional[float] = None
    opened_by: int
    opened_by_name: Optional[str] = None
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    closed_by: Optional[int] = None
    closed_by_name: Optional[str] = None
    status: str
    notes: Optional[str] = None


class CashMovementCreate(BaseModel):
    movement_type: str
    amount: float
    description: Optional[str] = None
    reference_id: Optional[int] = None


class CashMovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    cash_register_id: int
    movement_type: str
    amount: float
    balance_after: float
    description: Optional[str] = None
    reference_id: Optional[int] = None
    performed_by: int
    performed_by_name: Optional[str] = None
    performed_at: datetime


# === Internal Consumption ===
class InternalConsumptionCreate(BaseModel):
    product_id: int
    quantity: float
    reason: Optional[str] = None


class InternalConsumptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    reason: Optional[str] = None
    performed_by: int
    performed_by_name: Optional[str] = None
    performed_at: datetime


# === Backup ===
class BackupInfo(BaseModel):
    backup_path: str
    size_mb: float
    created_at: datetime
    status: str


class ImportResult(BaseModel):
    imported_records: int
    failed_records: int
    errors: List[str] = []


# === Kitchen ===
class KitchenOrderUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class KitchenOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    order_id: int
    status: str
    items: List[Dict[str, Any]] = []
    assigned_to: Optional[int] = None
    assigned_to_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# === Recipe ===
class RecipeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    items: List[Dict[str, Any]] = []


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    items: Optional[List[Dict[str, Any]]] = None


class RecipeItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    recipe_id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    unit: str


class RecipeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    items: List[RecipeItemOut] = []
    created_at: datetime
    updated_at: datetime


# === Purchase ===
class PurchaseCreate(BaseModel):
    supplier_id: int
    items: List[Dict[str, Any]]
    notes: Optional[str] = None


class PurchaseUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class PurchaseItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    purchase_id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    unit_price: float
    total: float


class PurchaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    status: str
    total: float
    items: List[PurchaseItemOut] = []
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# === Stock ===
class StockItemCreate(BaseModel):
    product_id: int
    quantity: float
    location: Optional[str] = None


class StockItemUpdate(BaseModel):
    quantity: Optional[float] = None
    location: Optional[str] = None


class StockItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    location: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class StockMovementCreate(BaseModel):
    product_id: int
    movement_type: str
    quantity: float
    reason: Optional[str] = None


class StockMovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    product_id: int
    product_name: Optional[str] = None
    movement_type: str
    quantity: float
    balance_after: float
    reason: Optional[str] = None
    performed_by: int
    performed_by_name: Optional[str] = None
    performed_at: datetime


# === Delivery ===
class DeliveryPlatformCreate(BaseModel):
    name: str
    active: bool = True
    api_base_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class DeliveryPlatformOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    slug: str
    active: bool
    api_base_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DeliveryPlatformItemCreate(BaseModel):
    external_item_id: Optional[str] = None
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    unit_price: float
    total: float
    notes: Optional[str] = None


class DeliveryPlatformItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    delivery_order_id: int
    external_item_id: Optional[str] = None
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    unit_price: float
    total: float
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DeliveryOrderCreate(BaseModel):
    platform_slug: Optional[str] = None
    external_order_id: Optional[str] = None
    client_name: str
    client_phone: Optional[str] = None
    address: str
    payment_method: str = "cash"
    subtotal: float
    delivery_fee: float = 0.0
    discount: float = 0.0
    total: float
    notes: Optional[str] = None


class DeliveryOrderIncoming(BaseModel):
    external_order_id: Optional[str] = None
    client_name: str
    client_phone: Optional[str] = None
    address: str
    payment_method: str = "cash"
    subtotal: float
    delivery_fee: float = 0.0
    discount: float = 0.0
    total: float
    raw_payload: Optional[str] = None
    items: List[Dict[str, Any]] = []


class DeliveryOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    platform_id: int
    external_order_id: Optional[str] = None
    client_name: str
    client_phone: Optional[str] = None
    address: str
    payment_method: str
    subtotal: float
    delivery_fee: float
    discount: float
    total: float
    status: str
    raw_payload: Optional[str] = None
    received_at: datetime
    acknowledged_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    items: List[DeliveryPlatformItemOut] = []
    created_at: datetime
    updated_at: datetime


# === Payment Method ===
class PaymentMethodCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool = True


class PaymentMethodUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PaymentMethodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime


# === Permission ===
class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    resource: str
    action: str


class RolePermissionUpdate(BaseModel):
    role_id: int
    permission_ids: List[int]


# === Settings ===
class RestaurantSettingsUpdate(BaseModel):
    restaurant_name: Optional[str] = None
    currency: Optional[str] = None
    tax_rate: Optional[float] = None
    default_payment_method: Optional[str] = None


class RestaurantSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    restaurant_name: str
    currency: str
    tax_rate: float
    default_payment_method: str
    updated_at: datetime


# === Tab ===
class TabCreate(BaseModel):
    client_id: int
    table_id: Optional[int] = None
    notes: Optional[str] = None


class TabItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tab_id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    unit_price: float
    total: float
    added_at: datetime


class TabOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    client_id: int
    client_name: Optional[str] = None
    table_id: Optional[int] = None
    total: float
    status: str
    items: List[TabItemOut] = []
    created_at: datetime
    updated_at: datetime


# === Table ===
class TableCreate(BaseModel):
    name: str
    capacity: int
    location: Optional[str] = None


class TableUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    location: Optional[str] = None
    is_available: Optional[bool] = None


class TableOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    capacity: int
    location: Optional[str] = None
    is_available: bool
    created_at: datetime


# === Supplier ===
class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: bool
    created_at: datetime


# === Loss Record ===
class LossRecordCreate(BaseModel):
    product_id: int
    quantity: float
    reason: str
    notes: Optional[str] = None


class LossRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: float
    reason: str
    notes: Optional[str] = None
    recorded_by: int
    recorded_by_name: Optional[str] = None
    recorded_at: datetime


# === Expense ===
class ExpenseCreate(BaseModel):
    category: str
    amount: float
    description: Optional[str] = None
    expense_date: Optional[date] = None


class ExpenseUpdate(BaseModel):
    category: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    expense_date: Optional[date] = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    category: str
    amount: float
    description: Optional[str] = None
    expense_date: date
    recorded_by: int
    recorded_by_name: Optional[str] = None
    recorded_at: datetime


# === Audit ===
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime


# === Promotion ===
class PromotionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True
    product_ids: Optional[List[int]] = None
    category_ids: Optional[List[int]] = None


class PromotionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class PromotionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool
    product_ids: Optional[List[int]] = None
    category_ids: Optional[List[int]] = None
    created_at: datetime
    updated_at: datetime