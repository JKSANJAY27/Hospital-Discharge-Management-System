import datetime
from typing import List, Dict, Any
import uuid

class CalendarGenerator:
    """
    Generates ICS calendar files for discharge action plans and follow-ups.
    """
    
    @staticmethod
    def generate_ics(action_plan: List[Dict[str, Any]], follow_up_schedule: List[Dict[str, Any]]) -> str:
        """
        Generate ICS content string from action plan and follow-up schedule.
        
        Args:
            action_plan: List of action plan items (from DischargeOutputSchema)
            follow_up_schedule: List of follow-up appointments
            
        Returns:
            String content of .ics file
        """
        events = []
        now = datetime.datetime.now()
        
        # 1. Action Plan Events (assuming relative dates starting from "today")
        # Note: This is a simplification. "Day 1" is assumed to be today or tomorrow.
        for item in action_plan:
            day_label = item.get('day', '')
            tasks = item.get('tasks', [])
            meds = item.get('medications', [])
            
            # Determine date offset
            offset = 0
            if "Day 1" in day_label or "Today" in day_label:
                offset = 0
            elif "Day 2" in day_label:
                offset = 1
            elif "Week 1" in day_label:
                # Add a recurring event for the week? Or just a one-time reminder?
                # For simplicity in this demo, we'll set it for Day 3
                offset = 3 
            
            event_date = now + datetime.timedelta(days=offset)
            date_str = event_date.strftime("%Y%m%d")
            
            # Create a summary event for the day's tasks
            if tasks or meds:
                description = "TASKS:\n" + "\n".join([f"- {t}" for t in tasks])
                if meds:
                    description += "\n\nMEDICATIONS:\n" + "\n".join([f"- {m}" for m in meds])
                
                events.append(CalendarGenerator._create_event_block(
                    uid=str(uuid.uuid4()),
                    start_dt=date_str, # All day event
                    summary=f"Health Plan: {day_label}",
                    description=description
                ))

        # 2. Follow-Up Appointments
        for appt in follow_up_schedule:
            specialist = appt.get('specialist', 'Doctor')
            when = appt.get('when', '')
            purpose = appt.get('purpose', '')
            
            # Estimate date for "In 1 week" etc.
            offset = 7 # Default
            if "2 weeks" in when:
                offset = 14
            elif "1 week" in when:
                offset = 7
            elif "month" in when:
                offset = 30
                
            appt_date = now + datetime.timedelta(days=offset)
            date_str = appt_date.strftime("%Y%m%d")
            
            events.append(CalendarGenerator._create_event_block(
                uid=str(uuid.uuid4()),
                start_dt=date_str,
                summary=f"Appt: {specialist}",
                description=f"When: {when}\nPurpose: {purpose}"
            ))

        # Wrap in VCALENDAR
        ics_content = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Discharge Simplifier//Healthcare AI//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]
        ics_content.extend(events)
        ics_content.append("END:VCALENDAR")
        
        return "\n".join(ics_content)

    @staticmethod
    def _create_event_block(uid: str, start_dt: str, summary: str, description: str) -> str:
        """Helper to create a VEVENT block."""
        # Simple all-day event
        # Escape newlines in description
        safe_desc = description.replace("\n", "\\n")
        
        return "\n".join([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART;VALUE=DATE:{start_dt}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{safe_desc}",
            "STATUS:CONFIRMED",
            "TRANSP:TRANSPARENT",
            "END:VEVENT"
        ])
