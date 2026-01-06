"""
Data schemas for healthcare workflow
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ClassificationSchema(BaseModel):
    """Schema for intent classification"""
    classification: str = Field(
        description="One of: discharge_simplification, action_planning, general_query, facility_locator_support"
    )
    reasoning: str = Field(description="Why this classification was chosen")


class SymptomCheckerSchema(BaseModel):
    """Schema for symptom information"""
    symptoms: List[str] = Field(description="List of symptoms")
    duration: str = Field(description="How long symptoms have persisted")
    severity: float = Field(description="Severity rating 0-10")
    age: float = Field(description="Patient age")
    comorbidities: List[str] = Field(description="Existing conditions", default_factory=list)
    triggers: str = Field(description="Symptom triggers if any", default="")
    additional_details: str = Field(description="Any other relevant info", default="")
    is_emergency: bool = Field(description="Whether this is an emergency")


class ActionPlanItem(BaseModel):
    day: str = Field(description="Day label, e.g., 'Day 1', 'Day 2', 'Week 1'")
    tasks: List[str] = Field(description="List of specific actions/tasks for this timeframe")
    medications: List[str] = Field(description="Medications to take during this timeframe")

class FollowUpAppointment(BaseModel):
    specialist: str = Field(description="Who to see (e.g., Cardiologist, PCP)")
    when: str = Field(description="Timeframe or specific date")
    purpose: str = Field(description="Reason for the visit")

class DischargeOutputSchema(BaseModel):
    """Schema for simplified discharge instructions"""
    simplified_summary: str = Field(description="Plain language summary (6th-8th grade level)")
    action_plan: List[ActionPlanItem] = Field(description="Day-by-day or phased action plan")
    danger_signs: List[str] = Field(description="Red flags/Warning signs requiring immediate help")
    medication_list: List[str] = Field(description="Simplified list of medications with instructions")
    wound_care: Optional[str] = Field(description="Specific wound care instructions if applicable")
    activity_restrictions: Optional[str] = Field(description="Activity limits or rehabilitation steps")
    follow_up_schedule: List[FollowUpAppointment] = Field(description="Follow-up appointments")
    lifestyle_changes: List[str] = Field(description="Dietary or lifestyle modifications")
    citations: List[str] = Field(description="Links to public care instructions (CDC/MedlinePlus) if relevant")
