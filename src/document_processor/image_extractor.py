"""
Image-based Document Extraction using OpenAI Vision (GPT-4o)
Integrated from medi.mate project for prescription and discharge document processing
"""

from openai import OpenAI
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json
import time
import os
from PIL import Image
import base64
from io import BytesIO
import logging

from ..config import HealthcareConfig

logger = logging.getLogger(__name__)


class ImageDocumentExtractor:
    """
    Extracts structured data from medical documents (prescriptions, discharge summaries)
    using OpenAI Vision API (GPT-4o) with OCR capabilities.
    
    Features:
    - Supports PDF and image files (JPG, PNG)
    - Handles handwritten and printed text
    - Extracts structured medical information
    - Returns JSON-formatted data
    """
    
    def __init__(self, config: Optional[HealthcareConfig] = None):
        """
        Initialize the extractor with OpenAI API.
        
        Args:
            config: HealthcareConfig instance (optional, uses env vars if not provided)
        """
        self.config = config or HealthcareConfig(skip_rag=True)
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_1")
        
        if not api_key:
            logger.warning("OpenAI API Key not found. Image extraction will not work.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            # Use GPT-4o-mini for vision (cheaper and faster than GPT-4o)
            self.model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
            logger.info(f"Initialized OpenAI Vision model: {self.model}")
    
    def extract_prescription_data(self, file_input: Union[str, Path, Image.Image, bytes]) -> Optional[Dict[str, Any]]:
        """
        Extract prescription information from image or PDF.
        
        Args:
            file_input: File path, PIL Image, or bytes
            
        Returns:
            Dict with extracted prescription data:
            {
                "date": "Date of prescription",
                "doctor": "Doctor name",
                "patient": "Patient name",
                "medicines": [
                    {
                        "name": "Medicine name",
                        "dosage": "Dosage amount",
                        "frequency": "How often (e.g., 1-0-1, twice daily)",
                        "timing": {
                            "morning": true/false,
                            "afternoon": true/false,
                            "night": true/false,
                            "instruction": "Before/After meal"
                        },
                        "duration": "Duration (e.g., 7 days)"
                    }
                ],
                "notes": "Special instructions"
            }
        """
        prompt = """
        You are an expert medical assistant specialized in reading prescriptions.
        Analyze this prescription image and extract ALL information in JSON format.
        
        **CRITICAL: Extract EVERY medicine visible, including:**
        - Brand names and generic names
        - Dosage (mg, ml, tablets)
        - Frequency (1-0-1, twice daily, etc.)
        - Timing (morning/afternoon/night, before/after meals)
        - Duration (number of days/weeks)
        
        Return this exact JSON structure:
        {
            "date": "Prescription date (YYYY-MM-DD format if possible)",
            "patient_info": {
                "name": "Patient name",
                "age": "Patient age",
                "gender": "Patient gender"
            },
            "doctor_info": {
                "name": "Doctor name",
                "specialty": "Doctor specialty"
            },
            "diagnosis": "Reason for prescription",
            "medications": [
                {
                    "name": "Full medicine name",
                    "dosage": "Amount per dose (e.g., 500mg, 1 tablet)",
                    "frequency": "How often (e.g., 1-0-1, twice daily, every 8 hours)",
                    "timing": {
                        "morning": true/false,
                        "afternoon": true/false,
                        "night": true/false,
                        "instruction": "Before meal / After meal / With food / Empty stomach"
                    },
                    "duration": "How long (e.g., 7 days, 2 weeks)"
                }
            ],
            "additional_instructions": "Any special instructions or warnings"
        }
        
        If a field is not clearly visible, use "-" or null.
        Return ONLY valid JSON, no markdown formatting.
        """
        
        return self._extract_with_openai(file_input, prompt)
    
    def extract_discharge_summary(self, file_input: Union[str, Path, Image.Image, bytes]) -> Optional[Dict[str, Any]]:
        """
        Extract discharge summary information from document.
        
        Returns:
            Dict with discharge summary data including diagnosis, procedures,
            medications, follow-up instructions, etc.
        """
        prompt = """
        You are an expert medical assistant. Analyze this discharge summary and extract information in JSON format.
        
        {
            "patient_info": {
                "name": "Patient name",
                "age": "Age",
                "gender": "Gender",
                "admission_date": "Date admitted",
                "discharge_date": "Date discharged"
            },
            "diagnosis": {
                "primary": "Primary diagnosis",
                "secondary": ["List of secondary diagnoses"]
            },
            "procedures": ["List of procedures/surgeries performed"],
            "medications": [
                {
                    "name": "Medicine name",
                    "dosage": "Dosage",
                    "frequency": "Frequency",
                    "purpose": "Why prescribed"
                }
            ],
            "follow_up": {
                "appointments": ["Follow-up appointments with specialists"],
                "instructions": ["Post-discharge care instructions"],
                "warning_signs": ["Danger signs to watch for"]
            },
            "restrictions": {
                "activity": "Activity restrictions",
                "diet": "Dietary restrictions"
            },
            "notes": "Additional important notes"
        }
        
        Extract ALL visible information. If a field is missing, use "-" or empty array.
        Return ONLY valid JSON.
        """
        
        return self._extract_with_openai(file_input, prompt)
    
    def extract_lab_report(self, file_input: Union[str, Path, Image.Image, bytes]) -> Optional[Dict[str, Any]]:
        """
        Extract lab test results from report images.
        """
        prompt = """
        Extract all test results from this lab report in JSON format.
        
        {
            "report_date": "Date of report",
            "patient_name": "Patient name",
            "tests": [
                {
                    "test_name": "Name of test",
                    "result": "Result value",
                    "unit": "Unit of measurement",
                    "reference_range": "Normal range",
                    "status": "Normal/High/Low"
                }
            ],
            "notes": "Any remarks or additional notes"
        }
        
        Return ONLY valid JSON.
        """
        
        return self._extract_with_openai(file_input, prompt)
    
    def extract_medical_certificate(self, file_input: Union[str, Path, Image.Image, bytes]) -> Optional[Dict[str, Any]]:
        """
        Extract information from medical certificates or fitness certificates.
        """
        prompt = """
        Extract information from this medical certificate in JSON format.
        
        {
            "certificate_type": "Type of certificate",
            "issue_date": "Date issued",
            "valid_until": "Valid until date",
            "patient_name": "Patient name",
            "doctor_name": "Doctor name",
            "diagnosis": "Medical condition/diagnosis",
            "recommendation": "Medical recommendation",
            "restrictions": "Any restrictions mentioned",
            "notes": "Additional notes"
        }
        
        Return ONLY valid JSON.
        """
        
        return self._extract_with_openai(file_input, prompt)
    
    def _extract_with_openai(self, file_input: Union[str, Path, Image.Image, bytes], prompt: str) -> Optional[Dict[str, Any]]:
        """
        Internal method to extract data using OpenAI Vision API.
        
        Args:
            file_input: File path, PIL Image, or bytes
            prompt: Extraction prompt
            
        Returns:
            Extracted data as dictionary or None if failed
        """
        if not self.client:
            logger.error("OpenAI client not initialized. Check API key.")
            return None
        
        try:
            # Convert input to base64 image
            image_data = None
            
            if isinstance(file_input, (str, Path)):
                path_obj = Path(file_input)
                
                if path_obj.suffix.lower() == '.pdf':
                    # Try text extraction from PDF as fallback
                    try:
                        import PyPDF2
                        logger.info("Extracting text from PDF...")
                        with open(path_obj, 'rb') as pdf_file:
                            pdf_reader = PyPDF2.PdfReader(pdf_file)
                            text = ""
                            for page in pdf_reader.pages[:3]:  # First 3 pages
                                text += page.extract_text()
                            
                            if text.strip():
                                logger.info(f"Extracted {len(text)} characters from PDF")
                                # Return text for text-based extraction
                                return {"_pdf_text": text.strip()}
                            else:
                                logger.error("No text could be extracted from PDF")
                                return None
                    except ImportError:
                        logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
                        return None
                    except Exception as e:
                        logger.error(f"PDF text extraction failed: {e}")
                        return None
                else:
                    # Read image file
                    with open(path_obj, 'rb') as f:
                        image_bytes = f.read()
                    image_data = base64.b64encode(image_bytes).decode('utf-8')
                
            elif isinstance(file_input, Image.Image):
                # Convert PIL Image to bytes
                buffer = BytesIO()
                file_input.save(buffer, format='JPEG')
                image_bytes = buffer.getvalue()
                image_data = base64.b64encode(image_bytes).decode('utf-8')
                
            elif isinstance(file_input, bytes):
                image_data = base64.b64encode(file_input).decode('utf-8')
                
            else:
                logger.error(f"Unsupported file input type: {type(file_input)}")
                return None
            
            # Call OpenAI Vision API
            logger.info("Sending request to OpenAI Vision API...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            # Parse JSON from response
            text = response.choices[0].message.content
            logger.debug(f"Raw response: {text[:500]}...")
            
            # Clean up markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            # Parse JSON
            result = json.loads(text.strip())
            logger.info("Successfully extracted data from image")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {text}")
            return None
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            return None
    
    def extract_generic(self, file_input: Union[str, Path, Image.Image, bytes], custom_prompt: str) -> Optional[str]:
        """
        Extract information using a custom prompt.
        
        Args:
            file_input: File path, PIL Image, or bytes
            custom_prompt: Custom extraction prompt
            
        Returns:
            Extracted text or None if failed
        """
        if not self.client:
            logger.error("OpenAI client not initialized. Check API key.")
            return None
        
        try:
            # Convert to base64 and call OpenAI
            image_data = None
            if isinstance(file_input, (str, Path)):
                with open(file_input, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
            elif isinstance(file_input, Image.Image):
                buffer = BytesIO()
                file_input.save(buffer, format='JPEG')
                image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            elif isinstance(file_input, bytes):
                image_data = base64.b64encode(file_input).decode('utf-8')
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": custom_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]
                }],
                max_tokens=1000
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Generic extraction failed: {e}")
            return None


# Utility function for easy import
def extract_prescription(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Quick function to extract prescription data.
    
    Args:
        file_path: Path to prescription image or PDF
        
    Returns:
        Extracted prescription data
    """
    extractor = ImageDocumentExtractor()
    return extractor.extract_prescription_data(file_path)


def extract_discharge(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Quick function to extract discharge summary data.
    
    Args:
        file_path: Path to discharge summary image or PDF
        
    Returns:
        Extracted discharge data
    """
    extractor = ImageDocumentExtractor()
    return extractor.extract_discharge_summary(file_path)
