from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Vehicle Schemas
class VehicleBase(BaseModel):
    year: int = Field(..., ge=1900, le=2030)
    make: str
    model: str
    trim: Optional[str] = None
    nickname: Optional[str] = None
    current_mileage: Optional[int] = Field(None, ge=0)

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    current_mileage: Optional[int] = Field(None, ge=0)
    nickname: Optional[str] = None

class VehicleResponse(VehicleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Invoice Schemas
class InvoiceLineItemBase(BaseModel):
    service_type: str
    service_description: Optional[str] = None
    quantity: float = 1.0
    unit_price: Optional[float] = None
    line_total: Optional[float] = None
    is_labor: bool = False
    is_parts: bool = False

class InvoiceLineItemResponse(InvoiceLineItemBase):
    id: int
    invoice_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    service_date: Optional[datetime] = None
    mileage_at_service: Optional[int] = None
    shop_name: Optional[str] = None
    shop_address: Optional[str] = None
    total_amount: Optional[float] = None

class InvoiceCreate(InvoiceBase):
    vehicle_id: int

class InvoiceConfirm(InvoiceBase):
    line_items: List[InvoiceLineItemBase]

class InvoiceResponse(InvoiceBase):
    id: int
    vehicle_id: int
    filename: str
    is_confirmed: bool
    is_duplicate: bool
    created_at: datetime
    line_items: List[InvoiceLineItemResponse] = []
    extraction_data: Optional[dict] = None
    
    class Config:
        from_attributes = True

# Service Record Schemas
class ServiceRecordBase(BaseModel):
    service_date: datetime
    mileage_at_service: int
    service_type: str
    service_description: Optional[str] = None
    shop_name: Optional[str] = None
    notes: Optional[str] = None

class ServiceRecordCreate(ServiceRecordBase):
    vehicle_id: int

class ServiceRecordResponse(ServiceRecordBase):
    id: int
    vehicle_id: int
    is_manual_entry: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Recommendation Schemas
class RecommendationItem(BaseModel):
    service_type: str
    category: str  # "recommended_now", "due_soon", "optional", "not_needed"
    reason: str
    interval_miles: Optional[int] = None
    interval_months: Optional[int] = None
    last_performed_date: Optional[datetime] = None
    last_performed_mileage: Optional[int] = None
    citation: Optional[str] = None
    confidence: str  # "high", "medium", "low"
    is_upsell_flag: bool = False
    upsell_reason: Optional[str] = None

class RecommendationRequest(BaseModel):
    vehicle_id: int
    current_mileage: int
    driving_condition: str = "normal"  # or "severe"

class RecommendationResponse(BaseModel):
    vehicle_id: int
    vehicle_info: str
    current_mileage: int
    recommendations: List[RecommendationItem]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

# Timeline Schemas
class TimelineEvent(BaseModel):
    date: datetime
    mileage: int
    service_type: str
    description: Optional[str] = None
    shop_name: Optional[str] = None
    amount: Optional[float] = None
    invoice_id: Optional[int] = None

class TimelineResponse(BaseModel):
    vehicle_id: int
    events: List[TimelineEvent]
