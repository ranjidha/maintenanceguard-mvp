from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.models import Vehicle, ServiceRecord
from app.models.schemas import TimelineResponse, TimelineEvent
from app.utils.database import get_db

router = APIRouter()

@router.get("/{vehicle_id}", response_model=TimelineResponse)
async def get_timeline(vehicle_id: int, db: Session = Depends(get_db)):
    """
    Get maintenance timeline for a vehicle
    Shows all service records in chronological order
    """
    
    # Verify vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Get all service records
    service_records = db.query(ServiceRecord)\
        .filter(ServiceRecord.vehicle_id == vehicle_id)\
        .order_by(ServiceRecord.service_date.desc())\
        .all()
    
    # Build timeline events
    events = []
    for record in service_records:
        # Try to get invoice total if available
        amount = None
        if record.invoice_id:
            from app.models.models import Invoice
            invoice = db.query(Invoice).filter(Invoice.id == record.invoice_id).first()
            if invoice:
                amount = invoice.total_amount
        
        events.append(TimelineEvent(
            date=record.service_date,
            mileage=record.mileage_at_service,
            service_type=record.service_type,
            description=record.service_description,
            shop_name=record.shop_name,
            amount=amount,
            invoice_id=record.invoice_id
        ))
    
    return TimelineResponse(
        vehicle_id=vehicle_id,
        events=events
    )
