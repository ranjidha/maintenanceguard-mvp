from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.utils.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    make = Column(String, nullable=False)
    model = Column(String, nullable=False)
    trim = Column(String, nullable=True)
    nickname = Column(String, nullable=True)
    current_mileage = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoices = relationship("Invoice", back_populates="vehicle", cascade="all, delete-orphan")
    service_records = relationship("ServiceRecord", back_populates="vehicle", cascade="all, delete-orphan")

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    
    # File information
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    
    # Extracted data
    service_date = Column(DateTime, nullable=True)
    mileage_at_service = Column(Integer, nullable=True)
    shop_name = Column(String, nullable=True)
    shop_address = Column(Text, nullable=True)
    total_amount = Column(Float, nullable=True)
    
    # OCR and extraction
    ocr_text = Column(Text, nullable=True)
    extraction_data = Column(JSON, nullable=True)  # Raw LLM extraction
    
    # Status
    is_confirmed = Column(Boolean, default=False)
    is_duplicate = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    # Line item details
    service_type = Column(String, nullable=False)  # Normalized (e.g., "Oil Change")
    service_description = Column(Text, nullable=True)  # Raw from invoice
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, nullable=True)
    line_total = Column(Float, nullable=True)
    is_labor = Column(Boolean, default=False)
    is_parts = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")

class ServiceRecord(Base):
    __tablename__ = "service_records"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    
    # Service details
    service_date = Column(DateTime, nullable=False)
    mileage_at_service = Column(Integer, nullable=False)
    service_type = Column(String, nullable=False)
    service_description = Column(Text, nullable=True)
    shop_name = Column(String, nullable=True)
    
    # For manual entries
    is_manual_entry = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="service_records")

class OEMSchedule(Base):
    """Store OEM maintenance schedule data"""
    __tablename__ = "oem_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    make = Column(String, nullable=False)
    model = Column(String, nullable=False)
    trim = Column(String, nullable=True)
    
    # Schedule details
    service_type = Column(String, nullable=False)
    interval_miles = Column(Integer, nullable=True)
    interval_months = Column(Integer, nullable=True)
    driving_condition = Column(String, default="normal")  # normal or severe
    
    # Documentation
    citation = Column(Text, nullable=True)  # e.g., "2020 Camry Owner's Manual, p. 42"
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
