from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from datetime import datetime

from app.models.models import Invoice, InvoiceLineItem, Vehicle, ServiceRecord
from app.models.schemas import InvoiceResponse, InvoiceConfirm
from app.utils.database import get_db
from app.services.ocr_service import ocr_service
from app.services.llm_service import llm_service

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_invoice(
    vehicle_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload invoice file, perform OCR, and extract structured data using LLM
    """
    
    # Verify vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file_extension} not supported. Allowed: {allowed_extensions}"
        )
    
    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{vehicle_id}_{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Perform OCR
    print(f"Running OCR on {file_path}...")
    ocr_text = await ocr_service.extract_text_from_file(file_path)
    
    if not ocr_text:
        raise HTTPException(status_code=500, detail="OCR extraction failed")
    
    print(f"OCR completed. Extracted {len(ocr_text)} characters")
    
    # Extract structured data using LLM
    print("Extracting structured data with Claude...")
    extraction_result = await llm_service.extract_invoice_data(ocr_text)
    
    if not extraction_result.get("success"):
        # Still create invoice record but mark as needs manual review
        db_invoice = Invoice(
            vehicle_id=vehicle_id,
            filename=file.filename,
            file_path=file_path,
            ocr_text=ocr_text,
            extraction_data={"error": extraction_result.get("error")},
            is_confirmed=False
        )
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
        
        return {
            "invoice_id": db_invoice.id,
            "status": "ocr_completed",
            "message": "OCR completed but extraction failed. Manual review required.",
            "ocr_text": ocr_text[:500] + "..." if len(ocr_text) > 500 else ocr_text,
            "error": extraction_result.get("error")
        }
    
    # Create invoice record with extracted data
    extracted = extraction_result["data"]
    
    db_invoice = Invoice(
        vehicle_id=vehicle_id,
        filename=file.filename,
        file_path=file_path,
        ocr_text=ocr_text,
        extraction_data=extracted,
        service_date=datetime.fromisoformat(extracted["service_date"]) if extracted.get("service_date") else None,
        mileage_at_service=extracted.get("mileage"),
        shop_name=extracted.get("shop_name"),
        shop_address=extracted.get("shop_address"),
        total_amount=extracted.get("total_amount"),
        is_confirmed=False
    )
    
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    # Create line items if present
    if extracted.get("line_items"):
        for item in extracted["line_items"]:
            line_item = InvoiceLineItem(
                invoice_id=db_invoice.id,
                service_type=item.get("service_type", "Unknown"),
                service_description=item.get("service_description"),
                quantity=item.get("quantity", 1.0),
                unit_price=item.get("unit_price"),
                line_total=item.get("line_total"),
                is_labor=item.get("is_labor", False),
                is_parts=item.get("is_parts", False)
            )
            db.add(line_item)
        
        db.commit()
    
    return {
        "invoice_id": db_invoice.id,
        "status": "extraction_completed",
        "message": "Invoice uploaded and processed successfully. Please review and confirm.",
        "extracted_data": extracted,
        "needs_confirmation": True
    }

@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get invoice details"""
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoice

@router.get("/vehicle/{vehicle_id}", response_model=List[InvoiceResponse])
async def get_vehicle_invoices(vehicle_id: int, db: Session = Depends(get_db)):
    """Get all invoices for a vehicle"""
    
    invoices = db.query(Invoice).filter(Invoice.vehicle_id == vehicle_id).all()
    return invoices

@router.post("/{invoice_id}/confirm")
async def confirm_invoice(
    invoice_id: int,
    confirmation: InvoiceConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirm invoice data and create service records
    User can edit extracted data before confirming
    """
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.is_confirmed:
        raise HTTPException(status_code=400, detail="Invoice already confirmed")
    
    # Update invoice with confirmed data
    invoice.service_date = confirmation.service_date
    invoice.mileage_at_service = confirmation.mileage_at_service
    invoice.shop_name = confirmation.shop_name
    invoice.shop_address = confirmation.shop_address
    invoice.total_amount = confirmation.total_amount
    invoice.is_confirmed = True
    
    # Delete existing line items
    db.query(InvoiceLineItem).filter(InvoiceLineItem.invoice_id == invoice_id).delete()
    
    # Create new line items from confirmation
    for item in confirmation.line_items:
        line_item = InvoiceLineItem(
            invoice_id=invoice_id,
            service_type=item.service_type,
            service_description=item.service_description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=item.line_total,
            is_labor=item.is_labor,
            is_parts=item.is_parts
        )
        db.add(line_item)
        
        # Create service record for this service
        service_record = ServiceRecord(
            vehicle_id=invoice.vehicle_id,
            invoice_id=invoice_id,
            service_date=confirmation.service_date,
            mileage_at_service=confirmation.mileage_at_service,
            service_type=item.service_type,
            service_description=item.service_description,
            shop_name=confirmation.shop_name,
            is_manual_entry=False
        )
        db.add(service_record)
    
    db.commit()
    
    return {
        "message": "Invoice confirmed successfully",
        "invoice_id": invoice_id,
        "service_records_created": len(confirmation.line_items)
    }

@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Delete an invoice"""
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Delete file from filesystem
    if os.path.exists(invoice.file_path):
        os.remove(invoice.file_path)
    
    # Delete from database (cascades to line items)
    db.delete(invoice)
    db.commit()
    
    return {"message": "Invoice deleted successfully"}
