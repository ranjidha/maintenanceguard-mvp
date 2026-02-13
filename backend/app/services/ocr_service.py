import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
from typing import Optional

class OCRService:
    """Service for extracting text from invoice images and PDFs"""
    
    @staticmethod
    async def extract_text_from_file(file_path: str) -> Optional[str]:
        """
        Extract text from PDF or image file using Tesseract OCR
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text or None if extraction failed
        """
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                return await OCRService._extract_from_pdf(file_path)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                return await OCRService._extract_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            print(f"OCR extraction failed: {str(e)}")
            return None
    
    @staticmethod
    async def _extract_from_pdf(pdf_path: str) -> str:
        """Extract text from PDF by converting to images first"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            # Extract text from each page
            full_text = []
            for i, image in enumerate(images):
                print(f"Processing PDF page {i+1}/{len(images)}...")
                text = pytesseract.image_to_string(image)
                full_text.append(text)
            
            return "\n\n--- PAGE BREAK ---\n\n".join(full_text)
            
        except Exception as e:
            print(f"PDF OCR failed: {str(e)}")
            raise
    
    @staticmethod
    async def _extract_from_image(image_path: str) -> str:
        """Extract text from image file"""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text
            
        except Exception as e:
            print(f"Image OCR failed: {str(e)}")
            raise
    
    @staticmethod
    def preprocess_image(image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy
        - Convert to grayscale
        - Increase contrast
        """
        # Convert to grayscale
        image = image.convert('L')
        
        # You can add more preprocessing here like:
        # - Thresholding
        # - Noise removal
        # - Deskewing
        
        return image

# Singleton instance
ocr_service = OCRService()
