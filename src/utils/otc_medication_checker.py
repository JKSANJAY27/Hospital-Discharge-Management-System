"""
OTC (Over-The-Counter) Medication Safety Checker
Integrated from medi.mate project
Uses vector search + LLM verification to check if medications are safe to buy without prescription
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from ..config import HealthcareConfig
from ..utils.logging_utils import setup_logging
from ..vector_store.vector_store_manager import VectorStoreManager

logger = setup_logging(__name__)


# Common OTC medications approved in India (sample list - expand as needed)
APPROVED_OTC_MEDICATIONS = [
    {"medicine_name": "Paracetamol", "type": "Analgesic", "common_brands": ["Crocin", "Dolo", "Calpol"]},
    {"medicine_name": "Ibuprofen", "type": "Analgesic/Anti-inflammatory", "common_brands": ["Brufen", "Advil"]},
    {"medicine_name": "Aspirin", "type": "Analgesic/Antiplatelet", "common_brands": ["Disprin", "Ecosprin"]},
    {"medicine_name": "Cetirizine", "type": "Antihistamine", "common_brands": ["Zyrtec", "Alerid"]},
    {"medicine_name": "Loperamide", "type": "Antidiarrheal", "common_brands": ["Imodium", "Eldoper"]},
    {"medicine_name": "Omeprazole", "type": "Antacid", "common_brands": ["Omez", "Prilosec"]},
    {"medicine_name": "Pantoprazole", "type": "Antacid", "common_brands": ["Pan", "Pantocid"]},
    {"medicine_name": "Ranitidine", "type": "Antacid", "common_brands": ["Aciloc", "Rantac"]},
    {"medicine_name": "Domperidone", "type": "Antiemetic", "common_brands": ["Domstal", "Vomistop"]},
    {"medicine_name": "Chlorpheniramine", "type": "Antihistamine", "common_brands": ["Avil", "Piriton"]},
    {"medicine_name": "Diphenhydramine", "type": "Antihistamine", "common_brands": ["Benadryl"]},
    {"medicine_name": "Loratadine", "type": "Antihistamine", "common_brands": ["Lorfast", "Claritin"]},
    {"medicine_name": "Fexofenadine", "type": "Antihistamine", "common_brands": ["Allegra", "Fexo"]},
    {"medicine_name": "Dextromethorphan", "type": "Cough Suppressant", "common_brands": ["Benadryl DR"]},
    {"medicine_name": "Guaifenesin", "type": "Expectorant", "common_brands": ["Mucinex"]},
    {"medicine_name": "Salbutamol", "type": "Bronchodilator", "common_brands": ["Asthalin", "Ventolin"]},
    {"medicine_name": "Menthol", "type": "Topical Analgesic", "common_brands": ["Vicks", "Moov"]},
    {"medicine_name": "Diclofenac", "type": "NSAID", "common_brands": ["Voveran", "Voltaren"]},
    {"medicine_name": "Multivitamins", "type": "Supplement", "common_brands": ["Becosules", "Supradyn"]},
    {"medicine_name": "Vitamin C", "type": "Supplement", "common_brands": ["Celin", "Limcee"]},
    {"medicine_name": "Vitamin D", "type": "Supplement", "common_brands": ["D-Rise", "Calcirol"]},
    {"medicine_name": "Calcium", "type": "Supplement", "common_brands": ["Shelcal", "Calcimax"]},
    {"medicine_name": "Iron", "type": "Supplement", "common_brands": ["Ferrous Sulfate", "Orofer"]},
    {"medicine_name": "Zinc", "type": "Supplement", "common_brands": ["Zincovit"]},
    {"medicine_name": "Oral Rehydration Salts", "type": "Electrolyte", "common_brands": ["Electral", "ORS"]},
    {"medicine_name": "Activated Charcoal", "type": "Antidote", "common_brands": ["Charcoal Tablets"]},
    {"medicine_name": "Antacid", "type": "Digestive", "common_brands": ["Digene", "Gelusil", "ENO"]},
    {"medicine_name": "Lactobacillus", "type": "Probiotic", "common_brands": ["Bifilac", "Econorm"]},
    {"medicine_name": "Lactulose", "type": "Laxative", "common_brands": ["Duphalac"]},
    {"medicine_name": "Bisacodyl", "type": "Laxative", "common_brands": ["Dulcolax"]},
    {"medicine_name": "Povidone-Iodine", "type": "Antiseptic", "common_brands": ["Betadine"]},
    {"medicine_name": "Hydrogen Peroxide", "type": "Antiseptic", "common_brands": ["H2O2"]},
    {"medicine_name": "Petroleum Jelly", "type": "Skin Protectant", "common_brands": ["Vaseline"]},
    {"medicine_name": "Hydrocortisone Cream", "type": "Anti-inflammatory", "common_brands": ["Dermacort"]},
    {"medicine_name": "Clotrimazole", "type": "Antifungal", "common_brands": ["Candid", "Clotrin"]},
    {"medicine_name": "Miconazole", "type": "Antifungal", "common_brands": ["Daktarin"]},
    {"medicine_name": "Glycerin", "type": "Laxative", "common_brands": ["Glycerin Suppositories"]},
    {"medicine_name": "Sodium Bicarbonate", "type": "Antacid", "common_brands": ["Baking Soda"]},
]


class OTCMedicationChecker:
    """
    Checks if medications require a prescription or are available over-the-counter.
    Uses vector similarity search + LLM verification for accurate results.
    """
    
    def __init__(self, config: Optional[HealthcareConfig] = None):
        """
        Initialize the OTC checker.
        
        Args:
            config: HealthcareConfig instance
        """
        self.config = config or HealthcareConfig()
        self.vector_store = None
        self.llm = None
        self.otc_namespace = "otc_medications"
        
        try:
            # Initialize vector store for semantic search
            self.vector_store = VectorStoreManager(self.config)
            logger.info("Vector store initialized for OTC checking")
            
            # Initialize LLM for verification
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model=self.config.model_name_secondary,
                temperature=0,
                api_key=self.config.openai_api_key
            )
            logger.info("LLM initialized for OTC verification")
            
            # Index OTC medications if needed
            self._initialize_otc_database()
            
        except Exception as e:
            logger.error(f"Failed to initialize OTC checker: {e}")
    
    def _initialize_otc_database(self):
        """
        Ingest OTC medication list into vector store for fast semantic search.
        """
        try:
            logger.info("Initializing OTC medication database...")
            
            # Prepare documents for ingestion
            documents = []
            metadatas = []
            
            for med in APPROVED_OTC_MEDICATIONS:
                # Create searchable text combining name, type, and brands
                brands_text = ", ".join(med.get("common_brands", []))
                text = f"{med['medicine_name']} ({med['type']}) - Common brands: {brands_text}"
                
                documents.append(text)
                metadatas.append({
                    "medicine_name": med["medicine_name"],
                    "type": med["type"],
                    "brands": brands_text,
                    "source": "approved_otc_list"
                })
            
            # Add to vector store with specific namespace
            if self.vector_store:
                # Check if already indexed (optional - for efficiency)
                # For now, we'll upsert every time (idempotent)
                self.vector_store.add_documents(
                    documents=documents,
                    metadatas=metadatas,
                    namespace=self.otc_namespace
                )
                logger.info(f"Indexed {len(documents)} OTC medications")
            
        except Exception as e:
            logger.error(f"Failed to initialize OTC database: {e}")
    
    def check_medication(self, medication_name: str, dosage: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if a single medication is OTC or requires prescription.
        
        Args:
            medication_name: Name of the medication
            dosage: Optional dosage information
            
        Returns:
            Dict with:
            {
                "medication": "Name",
                "status": "OTC" | "PRESCRIPTION_REQUIRED",
                "confidence": 0.0-1.0,
                "matched_otc": "Matched OTC name if found",
                "reason": "Explanation",
                "alternatives": ["Alternative OTC options if prescription required"]
            }
        """
        if not self.vector_store or not self.llm:
            return {
                "medication": medication_name,
                "status": "UNKNOWN",
                "confidence": 0.0,
                "reason": "OTC checker not properly initialized"
            }
        
        try:
            # Step 1: Vector search for similar medications
            query = f"{medication_name} {dosage or ''}".strip()
            matches = self.vector_store.search(
                query=query,
                namespace=self.otc_namespace,
                top_k=5
            )
            
            if not matches or len(matches) == 0:
                return self._check_with_llm_only(medication_name, dosage)
            
            # Step 2: Get top candidates
            candidates = []
            for match in matches:
                if match.get("score", 0) > 0.7:  # High similarity threshold
                    candidates.append({
                        "name": match["metadata"]["medicine_name"],
                        "type": match["metadata"]["type"],
                        "brands": match["metadata"]["brands"],
                        "score": match.get("score", 0)
                    })
            
            if not candidates:
                return self._check_with_llm_only(medication_name, dosage)
            
            # Step 3: LLM verification
            candidates_text = "\n".join([
                f"- {c['name']} ({c['type']}) - Brands: {c['brands']} [Similarity: {c['score']:.2f}]"
                for c in candidates
            ])
            
            prompt = f"""You are a medical expert verifying OTC medication classification.

Query Medication: "{medication_name}" {f"Dosage: {dosage}" if dosage else ""}

Approved OTC Candidates Found:
{candidates_text}

Task: Determine if the query medication is equivalent to any OTC candidate.

Rules:
1. Brand names (e.g., "Crocin") should match if they contain the same active ingredient (e.g., "Paracetamol")
2. Generic names should match exactly or be clear synonyms
3. Consider dosage - high doses may require prescription even if base medication is OTC
4. Be strict - if unsure, classify as PRESCRIPTION_REQUIRED

Respond in JSON:
{{
    "is_otc": true/false,
    "matched_name": "Matched OTC name or null",
    "confidence": 0.0-1.0,
    "reason": "Brief explanation"
}}"""
            
            response = self.llm.invoke(prompt)
            result_text = response.content
            
            # Parse JSON response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            llm_result = json.loads(result_text.strip())
            
            # Format final result
            status = "OTC" if llm_result.get("is_otc") else "PRESCRIPTION_REQUIRED"
            
            return {
                "medication": medication_name,
                "status": status,
                "confidence": llm_result.get("confidence", 0.0),
                "matched_otc": llm_result.get("matched_name"),
                "reason": llm_result.get("reason"),
                "alternatives": self._get_alternatives(medication_name) if status == "PRESCRIPTION_REQUIRED" else []
            }
            
        except Exception as e:
            logger.error(f"Error checking medication {medication_name}: {e}")
            return {
                "medication": medication_name,
                "status": "UNKNOWN",
                "confidence": 0.0,
                "reason": f"Error during check: {str(e)}"
            }
    
    def check_medications_batch(self, medications: List[str]) -> Dict[str, Any]:
        """
        Check multiple medications at once.
        
        Args:
            medications: List of medication names
            
        Returns:
            Dict with:
            {
                "otc_safe": [List of OTC medications],
                "prescription_required": [List of prescription medications],
                "unknown": [List of medications that couldn't be classified]
            }
        """
        results = {
            "otc_safe": [],
            "prescription_required": [],
            "unknown": []
        }
        
        for med in medications:
            check_result = self.check_medication(med)
            
            if check_result["status"] == "OTC":
                results["otc_safe"].append(check_result)
            elif check_result["status"] == "PRESCRIPTION_REQUIRED":
                results["prescription_required"].append(check_result)
            else:
                results["unknown"].append(check_result)
        
        return results
    
    def _check_with_llm_only(self, medication_name: str, dosage: Optional[str] = None) -> Dict[str, Any]:
        """
        Fallback: Check using LLM knowledge only when vector search finds no matches.
        """
        prompt = f"""You are a medical expert specializing in OTC medication classification.

Medication: "{medication_name}"
{f"Dosage: {dosage}" if dosage else ""}

Task: Determine if this medication is typically available over-the-counter (OTC) without prescription in India/US.

Respond in JSON:
{{
    "is_otc": true/false,
    "confidence": 0.0-1.0,
    "reason": "Explanation including typical use case",
    "alternatives": ["List 2-3 OTC alternatives if prescription required"]
}}"""
        
        try:
            response = self.llm.invoke(prompt)
            result_text = response.content
            
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            llm_result = json.loads(result_text.strip())
            
            return {
                "medication": medication_name,
                "status": "OTC" if llm_result.get("is_otc") else "PRESCRIPTION_REQUIRED",
                "confidence": llm_result.get("confidence", 0.5),
                "matched_otc": None,
                "reason": llm_result.get("reason"),
                "alternatives": llm_result.get("alternatives", [])
            }
            
        except Exception as e:
            logger.error(f"LLM fallback failed: {e}")
            return {
                "medication": medication_name,
                "status": "UNKNOWN",
                "confidence": 0.0,
                "reason": "Could not verify medication status"
            }
    
    def _get_alternatives(self, medication_name: str) -> List[str]:
        """
        Get OTC alternatives for prescription medications.
        """
        try:
            prompt = f"""List 2-3 OTC alternatives for "{medication_name}" that treat similar symptoms.
Return only the medication names, one per line."""
            
            response = self.llm.invoke(prompt)
            alternatives = [line.strip("- ").strip() for line in response.content.split("\n") if line.strip()]
            return alternatives[:3]
            
        except:
            return []
    
    def get_otc_list(self) -> List[Dict[str, Any]]:
        """
        Get the full list of approved OTC medications.
        
        Returns:
            List of OTC medication dictionaries
        """
        return APPROVED_OTC_MEDICATIONS


# Utility function for quick checks
def is_medication_otc(medication_name: str) -> bool:
    """
    Quick check if a medication is OTC.
    
    Args:
        medication_name: Name of the medication
        
    Returns:
        True if OTC, False if prescription required or unknown
    """
    checker = OTCMedicationChecker()
    result = checker.check_medication(medication_name)
    return result["status"] == "OTC"
