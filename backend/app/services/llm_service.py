import os
import json
from anthropic import Anthropic
from typing import Dict, Any, Optional

class LLMService:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
    
    async def extract_invoice_data(self, ocr_text: str) -> Dict[str, Any]:
        """
        Extract structured data from invoice OCR text using Claude
        """
        
        system_prompt = """You are an expert at extracting structured data from vehicle maintenance invoices.
        
Your task is to extract the following information from the invoice text:
- service_date: Date of service (ISO format YYYY-MM-DD)
- mileage: Vehicle mileage at time of service (integer)
- shop_name: Name of the service provider
- shop_address: Full address of the shop
- total_amount: Total invoice amount (float)
- line_items: Array of services performed, each with:
  - service_type: Normalized service name (e.g., "Oil Change", "Tire Rotation")
  - service_description: Original description from invoice
  - quantity: Quantity (default 1.0)
  - unit_price: Price per unit if available
  - line_total: Total for this line item
  - is_labor: true if this is labor, false if parts
  - is_parts: true if this is parts, false if labor

Return ONLY valid JSON. If a field cannot be determined, use null.

Service type normalization examples:
- "Oil Chng", "Lube Oil Filter" → "Oil Change"
- "Rotate Tires", "Tire Rot" → "Tire Rotation"
- "Replace Air Filter", "Air Fltr" → "Air Filter Replacement"
- "Brake Insp", "Brk Inspection" → "Brake Inspection"
"""
        
        user_message = f"""Extract data from this invoice:

{ocr_text}

Return only JSON with the structure specified."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            )
            
            # Extract text from response
            response_text = message.content[0].text
            
            # Parse JSON
            extracted_data = json.loads(response_text)
            
            return {
                "success": True,
                "data": extracted_data,
                "raw_response": response_text
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse JSON: {str(e)}",
                "raw_response": response_text if 'response_text' in locals() else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_recommendations(
        self, 
        vehicle_info: Dict[str, Any],
        current_mileage: int,
        service_history: list,
        oem_schedules: list,
        driving_condition: str = "normal"
    ) -> Dict[str, Any]:
        """
        Generate maintenance recommendations based on vehicle info, history, and OEM schedules
        """
        
        system_prompt = """You are a vehicle maintenance expert advisor. Your role is to provide evidence-based maintenance recommendations.

Analyze the provided information and generate recommendations in these categories:
1. "recommended_now" - Services that should be performed immediately based on OEM schedule
2. "due_soon" - Services approaching their interval (within 1,000 miles or 1 month)
3. "optional" - Services that may provide benefit but aren't required by OEM schedule
4. "not_needed" - Services that are NOT due based on OEM schedule (potential upsells)

For each recommendation, provide:
- service_type: Name of the service
- category: One of the four categories above
- reason: Clear explanation of why this service is recommended or not needed
- interval_miles: Recommended mileage interval from OEM schedule
- interval_months: Recommended time interval from OEM schedule
- last_performed_date: When this service was last performed (if in history)
- last_performed_mileage: Mileage when last performed (if in history)
- citation: Reference to OEM schedule (e.g., "2020 Toyota Camry Owner's Manual")
- confidence: "high", "medium", or "low"
- is_upsell_flag: true if this appears to be unnecessary upsell
- upsell_reason: Explanation if flagged as upsell

CRITICAL RULES:
- NEVER recommend a service without OEM schedule support
- Always cite the OEM manual
- Flag services performed too early as potential upsells
- If uncertain, state assumptions clearly

Return only valid JSON array of recommendations."""

        # Prepare context
        context = {
            "vehicle": vehicle_info,
            "current_mileage": current_mileage,
            "driving_condition": driving_condition,
            "service_history": service_history,
            "oem_schedules": oem_schedules
        }
        
        user_message = f"""Generate maintenance recommendations for this vehicle:

Vehicle: {vehicle_info['year']} {vehicle_info['make']} {vehicle_info['model']}
Current Mileage: {current_mileage:,} miles
Driving Condition: {driving_condition}

Service History:
{json.dumps(service_history, indent=2, default=str)}

OEM Maintenance Schedule:
{json.dumps(oem_schedules, indent=2)}

Provide recommendations in JSON format."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            )
            
            response_text = message.content[0].text
            
            # Try to parse JSON (might be wrapped in markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            recommendations = json.loads(response_text)
            
            return {
                "success": True,
                "recommendations": recommendations
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "raw_response": response_text if 'response_text' in locals() else None
            }

# Singleton instance
llm_service = LLMService()
