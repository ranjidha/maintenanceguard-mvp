from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.models.models import Vehicle, ServiceRecord, OEMSchedule
from app.models.schemas import RecommendationRequest, RecommendationResponse
from app.utils.database import get_db
from app.services.llm_service import llm_service

router = APIRouter()


class SelectedRecommendation(BaseModel):
    service_type: str
    category: str
    reason: str
    interval_miles: Optional[int] = None
    interval_months: Optional[int] = None
    citation: Optional[str] = None
    confidence: Optional[str] = "medium"


class AddRecommendationsRequest(BaseModel):
    vehicle_id: int
    current_mileage: int
    service_date: Optional[str] = None  # ISO date string, defaults to today
    shop_name: Optional[str] = None
    selected_recommendations: List[SelectedRecommendation]

@router.post("/", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate maintenance recommendations based on vehicle, mileage, and service history
    """
    
    # Get vehicle
    vehicle = db.query(Vehicle).filter(Vehicle.id == request.vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Get service history
    service_records = db.query(ServiceRecord)\
        .filter(ServiceRecord.vehicle_id == request.vehicle_id)\
        .order_by(ServiceRecord.service_date.desc())\
        .all()
    
    # Format service history for LLM
    service_history = []
    for record in service_records:
        service_history.append({
            "service_type": record.service_type,
            "date": record.service_date.isoformat(),
            "mileage": record.mileage_at_service,
            "shop": record.shop_name,
            "description": record.service_description
        })
    
    # Get OEM schedule for this vehicle
    oem_schedules = db.query(OEMSchedule)\
        .filter(
            OEMSchedule.year == vehicle.year,
            OEMSchedule.make == vehicle.make,
            OEMSchedule.model == vehicle.model,
            OEMSchedule.driving_condition == request.driving_condition
        )\
        .all()
    
    # Format OEM schedules
    oem_schedule_data = []
    for schedule in oem_schedules:
        oem_schedule_data.append({
            "service_type": schedule.service_type,
            "interval_miles": schedule.interval_miles,
            "interval_months": schedule.interval_months,
            "citation": schedule.citation,
            "notes": schedule.notes
        })
    
    # If no OEM schedule data, return generic message
    if not oem_schedule_data:
        return RecommendationResponse(
            vehicle_id=request.vehicle_id,
            vehicle_info=f"{vehicle.year} {vehicle.make} {vehicle.model}",
            current_mileage=request.current_mileage,
            recommendations=[
                {
                    "service_type": "OEM Schedule Not Available",
                    "category": "optional",
                    "reason": f"No OEM maintenance schedule data available for {vehicle.year} {vehicle.make} {vehicle.model}. Please consult your owner's manual or add OEM schedule data.",
                    "interval_miles": None,
                    "interval_months": None,
                    "last_performed_date": None,
                    "last_performed_mileage": None,
                    "citation": "Owner's Manual",
                    "confidence": "low",
                    "is_upsell_flag": False,
                    "upsell_reason": None
                }
            ],
            generated_at=datetime.utcnow()
        )
    
    # Generate recommendations using LLM
    vehicle_info = {
        "year": vehicle.year,
        "make": vehicle.make,
        "model": vehicle.model,
        "trim": vehicle.trim
    }
    
    result = await llm_service.generate_recommendations(
        vehicle_info=vehicle_info,
        current_mileage=request.current_mileage,
        service_history=service_history,
        oem_schedules=oem_schedule_data,
        driving_condition=request.driving_condition
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate recommendations: {result.get('error')}"
        )
    
    return RecommendationResponse(
        vehicle_id=request.vehicle_id,
        vehicle_info=f"{vehicle.year} {vehicle.make} {vehicle.model}",
        current_mileage=request.current_mileage,
        recommendations=result["recommendations"],
        generated_at=datetime.utcnow()
    )


@router.post("/add-to-history")
async def add_recommendations_to_history(
    request: AddRecommendationsRequest,
    db: Session = Depends(get_db)
):
    """
    Add user-selected recommendations as service records.
    Called when user checks recommendations and clicks 'Add to Service History'.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == request.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Parse service date (default to today)
    if request.service_date:
        try:
            service_date = datetime.fromisoformat(request.service_date)
        except ValueError:
            service_date = datetime.utcnow()
    else:
        service_date = datetime.utcnow()

    created_records = []
    for rec in request.selected_recommendations:
        service_record = ServiceRecord(
            vehicle_id=request.vehicle_id,
            invoice_id=None,
            service_date=service_date,
            mileage_at_service=request.current_mileage,
            service_type=rec.service_type,
            service_description=rec.reason,
            shop_name=request.shop_name or "Added from Recommendations",
            is_manual_entry=True,
            notes=f"Added from recommendations. Category: {rec.category}. Citation: {rec.citation or 'N/A'}. Confidence: {rec.confidence}."
        )
        db.add(service_record)
        created_records.append(rec.service_type)

    # Update vehicle current mileage if higher
    if vehicle.current_mileage is None or request.current_mileage > vehicle.current_mileage:
        vehicle.current_mileage = request.current_mileage

    db.commit()

    return {
        "message": f"Successfully added {len(created_records)} service record(s) to history",
        "added_services": created_records,
        "service_date": service_date.isoformat(),
        "mileage": request.current_mileage
    }
