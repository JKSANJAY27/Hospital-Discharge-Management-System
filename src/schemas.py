"""
Data schemas for Discharge Simplification System
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ActionPlanItem(BaseModel):
    """
    A single day/phase in the action plan.
    
    Example:
        {
            "day": "Day 1 (Today)",
            "tasks": ["Take 1 blue pill with breakfast", "Change bandage at 8 PM"],
            "medications": ["Metformin 500mg", "Aspirin 81mg"]
        }
    """
    day: str = Field(
        description="Day label (e.g., 'Day 1 (Today)', 'Day 2', 'Week 1', 'Week 2')"
    )
    tasks: List[str] = Field(
        description="Specific actions/tasks for this timeframe with times when possible"
    )
    medications: List[str] = Field(
        default_factory=list,
        description="Medications to take during this timeframe"
    )


class FollowUpAppointment(BaseModel):
    """
    A follow-up appointment.
    
    Example:
        {
            "specialist": "Cardiologist",
            "when": "Within 2 weeks",
            "purpose": "Check heart function and adjust medications"
        }
    """
    specialist: str = Field(
        description="Who to see (e.g., 'Cardiologist', 'Primary Care Doctor', 'Surgeon')"
    )
    when: str = Field(
        description="Timeframe or specific date (e.g., 'Within 1 week', 'In 2 weeks', 'January 15')"
    )
    purpose: str = Field(
        description="Reason for the visit (e.g., 'Check heart function', 'Remove stitches')"
    )


class DischargeOutputSchema(BaseModel):
    """
    Complete structured output for simplified discharge instructions.
    
    This schema ensures all required information is captured:
    - Plain-language summary (6th-8th grade level)
    - Day-by-day action plan
    - Danger signs (red flags)
    - Medication list
    - Wound care (if applicable)
    - Activity restrictions
    - Follow-up schedule
    - Lifestyle changes
    - Citations to trusted sources
    """
    
    # REQUIRED: Plain-language summary
    simplified_summary: str = Field(
        description="Plain language summary at 6th-8th grade reading level. "
                    "Explains why admitted and what happened. No medical jargon."
    )
    
    # REQUIRED: Day-by-day action plan
    action_plan: List[ActionPlanItem] = Field(
        description="Day-by-day or phased action plan with specific tasks and times"
    )
    
    # REQUIRED: Danger signs (red flags)
    danger_signs: List[str] = Field(
        description="Red flags/Warning signs requiring immediate medical attention. "
                    "Be specific (e.g., 'Fever over 101°F', 'Chest pain')"
    )
    
    # REQUIRED: Simplified medication list
    medication_list: List[str] = Field(
        description="Simplified list of medications. "
                    "Format: 'Name - Purpose - Usage' "
                    "(e.g., 'Metformin - For blood sugar - Take 1 with breakfast')"
    )
    
    # OPTIONAL: Wound care instructions
    wound_care: Optional[str] = Field(
        default=None,
        description="Specific wound care instructions if applicable. "
                    "Include frequency and technique."
    )
    
    # OPTIONAL: Activity restrictions
    activity_restrictions: Optional[str] = Field(
        default=None,
        description="Activity limits or rehabilitation steps. "
                    "What they CANNOT do (e.g., 'No lifting over 5 lbs for 2 weeks')"
    )
    
    # REQUIRED: Follow-up appointments
    follow_up_schedule: List[FollowUpAppointment] = Field(
        description="Follow-up appointments with specialists"
    )
    
    # REQUIRED: Lifestyle changes
    lifestyle_changes: List[str] = Field(
        description="Dietary or lifestyle modifications. "
                    "Be specific and actionable (e.g., 'Reduce salt intake', 'Quit smoking')"
    )
    
    # REQUIRED: Citations to trusted sources
    citations: List[str] = Field(
        description="Links to public care instructions from trusted sources "
                    "(CDC/MedlinePlus) relevant to the condition. "
                    "Format: 'Source: Topic' (e.g., 'MedlinePlus: Heart Failure Care')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "simplified_summary": "You were in the hospital because your heart was not pumping blood well (heart failure). The doctors gave you medicine and monitored you for 3 days. You are now stable and can go home.",
                "action_plan": [
                    {
                        "day": "Day 1 (Today)",
                        "tasks": [
                            "Take 1 blue pill (Furosemide) with breakfast",
                            "Weigh yourself in the morning",
                            "Rest - no heavy activity"
                        ],
                        "medications": ["Furosemide 40mg", "Lisinopril 10mg"]
                    },
                    {
                        "day": "Week 1",
                        "tasks": [
                            "Continue daily weighing",
                            "Walk for 10 minutes twice a day",
                            "Track your weight - call doctor if gain over 2 lbs"
                        ],
                        "medications": ["Furosemide 40mg", "Lisinopril 10mg"]
                    }
                ],
                "danger_signs": [
                    "Fever over 101°F",
                    "Chest pain or pressure",
                    "Difficulty breathing or shortness of breath",
                    "Swelling in legs gets worse",
                    "Weight gain of 2+ pounds in one day"
                ],
                "medication_list": [
                    "Furosemide (water pill) - Helps remove extra fluid - Take 1 pill every morning",
                    "Lisinopril - For blood pressure and heart - Take 1 pill every morning"
                ],
                "wound_care": None,
                "activity_restrictions": "No heavy lifting over 10 pounds for 2 weeks. No strenuous exercise. Rest when tired.",
                "follow_up_schedule": [
                    {
                        "specialist": "Cardiologist (Heart Doctor)",
                        "when": "Within 1 week",
                        "purpose": "Check how your heart is doing and adjust medications if needed"
                    },
                    {
                        "specialist": "Primary Care Doctor",
                        "when": "Within 2 weeks",
                        "purpose": "General checkup and review all medications"
                    }
                ],
                "lifestyle_changes": [
                    "Reduce salt - no more than 1 teaspoon per day",
                    "Drink less fluid - no more than 6 cups per day",
                    "Quit smoking if you smoke",
                    "Eat more fruits and vegetables"
                ],
                "citations": [
                    "MedlinePlus: Heart Failure",
                    "CDC: Heart Disease Prevention",
                    "American Heart Association: Living with Heart Failure"
                ]
            }
        }
