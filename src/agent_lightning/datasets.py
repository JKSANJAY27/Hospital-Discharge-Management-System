"""
Dataset Definitions and Loaders for Agent Lightning Training

Provides sample datasets for training and validating healthcare agents.

Note: This module does NOT import agentlightning, making it usable on Windows.
"""

from typing import List, Dict, Any, Tuple, Optional, TypedDict


# =============================================================================
# Task Type Definitions (local to avoid agentlightning import)
# =============================================================================

class DischargeTask(TypedDict):
    """Task definition for discharge simplification."""
    document_text: str
    expected_output: Optional[Dict[str, Any]]


class EducationTask(TypedDict):
    """Task definition for patient education."""
    context: str
    expected_queries: Optional[list]


class SafetyTask(TypedDict):
    """Task definition for safety check."""
    text: str
    expected_is_safe: Optional[bool]


# =============================================================================
# Sample Discharge Documents for Training
# =============================================================================

SAMPLE_DISCHARGE_NOTES = [
    {
        "document_text": """
DISCHARGE SUMMARY

Patient: John Doe (De-identified)
Date: January 1, 2024

ADMISSION DIAGNOSIS:
Acute exacerbation of congestive heart failure (CHF)

HOSPITAL COURSE:
58-year-old male with history of CHF (EF 35%), HTN, T2DM admitted with SOB and bilateral lower extremity edema. 
Patient presented to ED with 3-day history of progressive dyspnea on exertion and orthopnea.

Physical exam revealed JVD, bilateral crackles, and 3+ pitting edema to knees.
CXR showed pulmonary congestion. BNP elevated at 1200.

Treatment included IV furosemide 40mg BID with good diuresis (net negative 3L over 48 hours).
Daily weights monitored. Euvolemic status achieved by hospital day 3.

DISCHARGE MEDICATIONS:
1. Furosemide 40mg PO daily
2. Lisinopril 10mg PO daily  
3. Metoprolol succinate 25mg PO daily
4. Metformin 500mg PO BID
5. Aspirin 81mg PO daily

DISCHARGE INSTRUCTIONS:
1. Daily weights - call MD if weight gain >2 lbs in 24 hours
2. Fluid restriction 1.5L daily
3. Sodium restriction <2g daily
4. Ambulate as tolerated, avoid strenuous activity x 2 weeks
5. Monitor for signs of decompensation: increased SOB, orthopnea, LE edema

FOLLOW-UP:
- Cardiology clinic in 1 week
- PCP in 2 weeks
""",
        "id": "chf_case_01"
    },
    {
        "document_text": """
DISCHARGE SUMMARY

Patient: Jane Smith (De-identified)
Date: February 15, 2024

ADMISSION DIAGNOSIS:
Total knee replacement (TKR) - Right knee

PROCEDURE:
Right total knee arthroplasty performed without complications.

HOSPITAL COURSE:
65-year-old female with severe osteoarthritis underwent elective right TKR.
Post-op course was uncomplicated. Physical therapy initiated on POD1.
Patient achieved 90 degrees knee flexion by POD2.

DISCHARGE MEDICATIONS:
1. Oxycodone 5mg q6h PRN pain
2. Aspirin 325mg daily x 4 weeks (DVT prophylaxis)
3. Ferrous sulfate 325mg daily
4. Acetaminophen 1000mg q6h scheduled

WOUND CARE:
- Keep incision clean and dry
- Dressing change every 2 days
- No shower for 7 days, sponge bath only
- Staples removed at 2-week follow-up

ACTIVITY:
- Weight bearing as tolerated with walker
- Use walker for 2-4 weeks
- Home PT 3x/week starting day 3
- Ice 20 min q2h while awake for swelling

FOLLOW-UP:
- Orthopedic surgeon in 2 weeks for staple removal
- Physical therapy starts at home in 3 days
""",
        "id": "tkr_case_01"
    },
    {
        "document_text": """
DISCHARGE SUMMARY

Patient: Robert Johnson (De-identified)
Date: March 10, 2024

ADMISSION DIAGNOSIS:
Community-acquired pneumonia

HOSPITAL COURSE:
72-year-old male with COPD presented with 5 days of productive cough, fever, and dyspnea.
CXR revealed right lower lobe consolidation. Started on IV antibiotics.
Improved clinically over 3 days. O2 sat maintained >92% on room air.

DISCHARGE MEDICATIONS:
1. Azithromycin 250mg PO daily x 4 more days
2. Benzonatate 100mg TID PRN cough
3. Albuterol inhaler 2 puffs q4h PRN
4. Continue home medications (fluticasone, tiotropium)

INSTRUCTIONS:
1. Complete full course of antibiotics
2. Rest and increase fluid intake (8 glasses water daily)
3. Use humidifier if available
4. Avoid tobacco smoke and irritants
5. Return to ER if: fever >101F, worsening breathing, chest pain, confusion

FOLLOW-UP:
- PCP in 1 week
- Repeat chest X-ray in 6 weeks if not improved
""",
        "id": "pneumonia_case_01"
    },
    {
        "document_text": """
DISCHARGE SUMMARY

Patient: Maria Garcia (De-identified)  
Date: April 5, 2024

ADMISSION DIAGNOSIS:
Type 2 Diabetes Mellitus with hyperglycemic crisis

HOSPITAL COURSE:
45-year-old female with poorly controlled T2DM admitted with blood glucose 450mg/dL.
No ketoacidosis. Started insulin drip, transitioned to subcutaneous insulin.
HbA1c: 11.2%. Diabetes education provided.

DISCHARGE MEDICATIONS:
1. Metformin 1000mg PO BID
2. Glipizide 10mg PO daily before breakfast
3. Lantus 20 units subcutaneous at bedtime
4. Humalog sliding scale before meals (provided chart)

DIABETES MANAGEMENT:
1. Check blood sugar 4x daily (before meals and bedtime)
2. Target fasting glucose: 80-130 mg/dL
3. Target post-meal glucose: <180 mg/dL
4. Keep blood sugar log to bring to appointments
5. Recognize hypoglycemia signs: shakiness, sweating, confusion

DIET:
1. Low carbohydrate diet (45-60g carbs per meal)
2. Avoid sugary drinks and sweets
3. Eat regular meals, don't skip
4. Consult with nutritionist scheduled

FOLLOW-UP:
- Endocrinology in 1 week
- Diabetic eye exam within 3 months
- Podiatry referral for foot care
""",
        "id": "diabetes_case_01"
    },
    {
        "document_text": """
DISCHARGE SUMMARY

Patient: David Lee (De-identified)
Date: May 20, 2024

ADMISSION DIAGNOSIS:
Acute appendicitis - s/p laparoscopic appendectomy

PROCEDURE:
Laparoscopic appendectomy performed without complications.
Pathology: Acute suppurative appendicitis.

HOSPITAL COURSE:
32-year-old male with 2-day RLQ pain. CT confirmed appendicitis.
Laparoscopic appendectomy performed. Tolerated clear liquids POD0.
Advanced to regular diet POD1. Discharged home POD1.

DISCHARGE MEDICATIONS:
1. Ibuprofen 600mg q6h PRN pain (take with food)
2. Acetaminophen 1000mg q6h PRN (alternate with ibuprofen)
3. Ondansetron 4mg PRN nausea

WOUND CARE:
- 3 small incisions covered with steri-strips
- Keep dry for 48 hours
- May shower after 48 hours, pat dry
- Steri-strips will fall off in 7-10 days
- No submerging in bath/pool for 2 weeks

ACTIVITY:
- No heavy lifting (>15 lbs) for 2 weeks
- No strenuous exercise for 2 weeks
- May return to desk work in 3-5 days
- May drive when off pain medications

DIET:
- Start with bland foods
- Advance as tolerated
- Stay hydrated

FOLLOW-UP:
- Call if: fever >101.5F, increasing pain, redness at incision, drainage
- Surgeon office in 2 weeks
""",
        "id": "appendectomy_case_01"
    },
]


# =============================================================================
# Sample Education Contexts
# =============================================================================

SAMPLE_EDUCATION_CONTEXTS = [
    {"context": "Total Knee Replacement post-surgery", "id": "edu_tkr"},
    {"context": "Heart Failure management", "id": "edu_chf"},
    {"context": "Type 2 Diabetes newly diagnosed", "id": "edu_diabetes"},
    {"context": "Pneumonia recovery at home", "id": "edu_pneumonia"},
    {"context": "Post-appendectomy care", "id": "edu_appendectomy"},
    {"context": "High blood pressure lifestyle changes", "id": "edu_hypertension"},
    {"context": "Stroke rehabilitation exercises", "id": "edu_stroke"},
    {"context": "Back surgery recovery", "id": "edu_spine"},
]


# =============================================================================  
# Sample Safety Check Texts
# =============================================================================

SAMPLE_SAFETY_TEXTS = [
    {
        "text": "Patient has history of hypertension and diabetes. Currently on metformin 500mg BID.",
        "expected_is_safe": True,
        "id": "safe_medical"
    },
    {
        "text": "Patient name: John Doe. SSN: 123-45-6789. Credit card: 4111-1111-1111-1111.",
        "expected_is_safe": False,
        "id": "unsafe_pii"
    },
    {
        "text": "Discharge diagnosis: Congestive heart failure. Follow up with cardiology in 1 week.",
        "expected_is_safe": True,
        "id": "safe_discharge"
    },
    {
        "text": "The patient should be prescribed medications. Passport number: AB1234567.",
        "expected_is_safe": False,
        "id": "unsafe_passport"
    },
]


# =============================================================================
# Dataset Loader Functions  
# =============================================================================

def load_discharge_dataset(
    train_ratio: float = 0.7
) -> Tuple[List[DischargeTask], List[DischargeTask]]:
    """
    Load discharge document dataset for training.
    
    Args:
        train_ratio: Fraction of data for training (rest for validation)
        
    Returns:
        Tuple of (train_dataset, val_dataset)
    """
    # Convert to DischargeTask format
    all_tasks: List[DischargeTask] = [
        DischargeTask(
            document_text=note["document_text"],
            expected_output=None  # No ground truth for now
        )
        for note in SAMPLE_DISCHARGE_NOTES
    ]
    
    # Split into train/val
    split_idx = int(len(all_tasks) * train_ratio)
    train_dataset = all_tasks[:split_idx]
    val_dataset = all_tasks[split_idx:]
    
    # Ensure we have at least 1 sample in each
    if len(train_dataset) == 0:
        train_dataset = [all_tasks[0]]
    if len(val_dataset) == 0:
        val_dataset = [all_tasks[-1]]
    
    return train_dataset, val_dataset


def load_education_dataset(
    train_ratio: float = 0.7
) -> Tuple[List[EducationTask], List[EducationTask]]:
    """
    Load patient education dataset for training.
    """
    all_tasks: List[EducationTask] = [
        EducationTask(
            context=item["context"],
            expected_queries=None
        )
        for item in SAMPLE_EDUCATION_CONTEXTS
    ]
    
    split_idx = int(len(all_tasks) * train_ratio)
    return all_tasks[:split_idx] or [all_tasks[0]], all_tasks[split_idx:] or [all_tasks[-1]]


def load_safety_dataset(
    train_ratio: float = 0.7
) -> Tuple[List[SafetyTask], List[SafetyTask]]:
    """
    Load safety check dataset for training.
    """
    all_tasks: List[SafetyTask] = [
        SafetyTask(
            text=item["text"],
            expected_is_safe=item["expected_is_safe"]
        )
        for item in SAMPLE_SAFETY_TEXTS
    ]
    
    split_idx = int(len(all_tasks) * train_ratio)
    return all_tasks[:split_idx] or [all_tasks[0]], all_tasks[split_idx:] or [all_tasks[-1]]


def load_custom_discharge_documents(
    file_paths: List[str]
) -> List[DischargeTask]:
    """
    Load custom discharge documents from files.
    
    Args:
        file_paths: List of paths to discharge document files
        
    Returns:
        List of DischargeTask objects
    """
    from pathlib import Path
    
    tasks = []
    for path in file_paths:
        p = Path(path)
        if p.exists():
            text = p.read_text(encoding="utf-8")
            tasks.append(DischargeTask(
                document_text=text,
                expected_output=None
            ))
    
    return tasks
