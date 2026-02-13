from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.models import Vehicle
from app.models.schemas import VehicleCreate, VehicleUpdate, VehicleResponse
from app.utils.database import get_db

router = APIRouter()

@router.post("/", response_model=VehicleResponse, status_code=201)
async def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    """Create a new vehicle profile"""
    
    db_vehicle = Vehicle(
        year=vehicle.year,
        make=vehicle.make,
        model=vehicle.model,
        trim=vehicle.trim,
        nickname=vehicle.nickname,
        current_mileage=vehicle.current_mileage
    )
    
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    
    return db_vehicle

@router.get("/", response_model=List[VehicleResponse])
async def get_vehicles(db: Session = Depends(get_db)):
    """Get all vehicles"""
    
    vehicles = db.query(Vehicle).all()
    return vehicles

@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Get a specific vehicle by ID"""
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    return vehicle

@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: int, 
    vehicle_update: VehicleUpdate, 
    db: Session = Depends(get_db)
):
    """Update vehicle information"""
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Update fields
    if vehicle_update.current_mileage is not None:
        vehicle.current_mileage = vehicle_update.current_mileage
    if vehicle_update.nickname is not None:
        vehicle.nickname = vehicle_update.nickname
    
    db.commit()
    db.refresh(vehicle)
    
    return vehicle

@router.delete("/{vehicle_id}", status_code=204)
async def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Delete a vehicle"""
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    db.delete(vehicle)
    db.commit()
    
    return None
