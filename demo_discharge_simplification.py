"""
Test script for Discharge Simplification System

This demonstrates:
1. Loading a discharge summary from a file
2. Generating simplified instructions
3. Creating a calendar reminder file (.ics)
4. Evaluating output quality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import HealthcareConfig
from src.workflow import DischargeWorkflow


# Sample de-identified discharge note
SAMPLE_DISCHARGE_NOTE = """
DISCHARGE SUMMARY

Patient: John Doe (De-identified)
Date: January 1, 2024
MRN: XXXX

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

DANGER SIGNS - CALL 911:
- Severe chest pain
- Difficulty breathing at rest
- Confusion or altered mental status

PATIENT EDUCATION:
Discussed heart failure management, medication compliance, dietary restrictions, and warning signs.
Patient verbalized understanding.
"""


async def main():
    print("=" * 80)
    print("DISCHARGE SIMPLIFICATION SYSTEM - TEST")
    print("=" * 80)
    print()
    
    # Initialize system
    print("Initializing system...")
    config = HealthcareConfig()
    workflow = DischargeWorkflow(config)
    print()
    
    # Create a temporary sample file
    sample_file_path = "sample_discharge_note.txt"
    with open(sample_file_path, "w", encoding="utf-8") as f:
        f.write(SAMPLE_DISCHARGE_NOTE)
    print(f"📝 Created sample file: {sample_file_path}")
    
    # Process discharge note from file
    print("Processing discharge note from file...")
    print("-" * 80)
    
    # Use the new process_file method
    result = await workflow.process_file(sample_file_path)
    print()
    
    # Display results
    if result.get("status") == "success":
        print("✅ SUCCESS! Discharge instructions simplified.")
        print("=" * 80)
        print()
        
        # 1. Simplified Summary
        print("📝 SIMPLIFIED SUMMARY (6th-8th Grade Level):")
        print("-" * 80)
        print(result["simplified_summary"])
        print()
        
        # 2. Action Plan
        print("📅 DAY-BY-DAY ACTION PLAN:")
        print("-" * 80)
        for day_plan in result["action_plan"]:
            print(f"\n{day_plan['day']}:")
            for task in day_plan["tasks"]:
                print(f"  ☐ {task}")
            if day_plan.get("medications"):
                print(f"  💊 Medications: {', '.join(day_plan['medications'])}")
        print()
        
        # 3. Danger Signs
        print("🚨 DANGER SIGNS - CALL DOCTOR/911 IF YOU SEE THESE:")
        print("-" * 80)
        for sign in result["danger_signs"]:
            print(f"  ⚠️  {sign}")
        print()
        
        # 4. Medications
        print("💊 MEDICATION LIST:")
        print("-" * 80)
        for med in result["medication_list"]:
            print(f"  • {med}")
        print()
        
        # 5. Follow-up
        print("📆 FOLLOW-UP APPOINTMENTS:")
        print("-" * 80)
        for appt in result["follow_up_schedule"]:
            print(f"  • {appt['specialist']}")
            print(f"    When: {appt['when']}")
            print(f"    Why: {appt['purpose']}")
            print()
            
        # 6. ICS File Generation
        if "ics_content" in result:
            ics_filename = "patient_schedule.ics"
            with open(ics_filename, "w", encoding="utf-8") as f:
                f.write(result["ics_content"])
            print(f"📅 CALENDAR FILE GENERATED: {ics_filename}")
            print(f"   (You can open this in Outlook/Google Calendar)")
            print("-" * 80)
            print()
        
        # 7. Evaluation Metrics
        if "evaluation" in result:
            eval_data = result["evaluation"]
            print("=" * 80)
            print("📊 EVALUATION METRICS:")
            print("-" * 80)
            print(f"  Readability Score: {eval_data['readability_score']:.1f} (Target: 6-8)")
            print(f"  Safety Warnings Present: {'✅ Yes' if eval_data['safety_warnings_present'] else '❌ No'}")
            print()
            print("  Completeness Check:")
            for key, value in eval_data['completeness'].items():
                status = "✅" if value else "❌"
                print(f"    {status} {key.replace('_', ' ').title()}")
            print()
            print("  Plan Usability:")
            usability = eval_data['plan_usability']
            print(f"    Total Days: {usability.get('total_days', 0)}")
            print(f"    Total Tasks: {usability.get('total_tasks', 0)}")
            print(f"    Has Specific Times: {'✅ Yes' if usability.get('has_specific_times') else '❌ No'}")
            print()
        
    else:
        print("❌ FAILED!")
        print(f"Error: {result.get('error')}")
        print(f"Reason: {result.get('reason')}")
        
    # Cleanup
    if os.path.exists(sample_file_path):
        os.remove(sample_file_path)
        print(f"🗑️  Cleaned up temporary file: {sample_file_path}")


if __name__ == "__main__":
    asyncio.run(main())
