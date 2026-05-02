"""
Lead Capture & Management Module
---------------------------------
Implements a state machine for capturing leads through conversation,
and persists them to a JSON file.
"""

import json
import os
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
LEADS_FILE = os.path.join(DATA_DIR, "leads.json")

# ---------------------------------------------------------------------------
# Lead State Machine
# ---------------------------------------------------------------------------

# States: idle -> ask_name -> ask_interest -> ask_contact -> complete
LEAD_STATES = {
    "idle": {
        "prompt": None,
        "next": "ask_name",
    },
    "ask_name": {
        "prompt": "I'd love to help you get started! 😊 Could you please share your **name**?",
        "next": "ask_interest",
        "field": "name",
    },
    "ask_interest": {
        "prompt": "Nice to meet you, {name}! 🎓 Which **course or area** are you interested in? (e.g., AI/ML, Web Development, Data Science, etc.)",
        "next": "ask_contact",
        "field": "interest",
    },
    "ask_contact": {
        "prompt": "Great choice! 🌟 Could you share your **phone number or email** so our counselor can reach out to you?",
        "next": "complete",
        "field": "contact",
    },
    "complete": {
        "prompt": "Thank you, {name}! ✅ Your details have been captured successfully.\n\n📋 **Your Enquiry Summary:**\n• Name: {name}\n• Interest: {interest}\n• Contact: {contact}\n\nOur admissions team will reach out to you within 24 hours. Is there anything else I can help you with?",
        "next": "idle",
    },
}


def get_lead_state(session: dict) -> str:
    """Get the current lead capture state for a session."""
    return session.get("lead_state", "idle")


def set_lead_state(session: dict, state: str):
    """Set the lead capture state for a session."""
    session["lead_state"] = state


def is_in_lead_capture(session: dict) -> bool:
    """Check if a session is currently in a lead capture flow."""
    state = get_lead_state(session)
    return state not in ("idle", None)


def process_lead_capture(session: dict, user_message: str) -> dict:
    """
    Process a lead capture step.
    
    Args:
        session: The current session dict (mutable)
        user_message: The user's response
    
    Returns:
        dict with:
            - response: str (the bot's response)
            - complete: bool (whether lead capture is complete)
            - lead: dict or None (the captured lead if complete)
    """
    state = get_lead_state(session)

    # If not in lead capture, initiate it
    if state == "idle":
        set_lead_state(session, "ask_name")
        if "lead_data" not in session:
            session["lead_data"] = {}
        prompt = LEAD_STATES["ask_name"]["prompt"]
        return {"response": prompt, "complete": False, "lead": None}

    # Process current state
    state_config = LEAD_STATES[state]
    
    # Save the user's input for the current field
    if "field" in state_config:
        if "lead_data" not in session:
            session["lead_data"] = {}
        session["lead_data"][state_config["field"]] = user_message.strip()

    # Move to next state
    next_state = state_config["next"]
    set_lead_state(session, next_state)

    # Generate prompt for next state
    next_config = LEAD_STATES[next_state]
    lead_data = session.get("lead_data", {})

    if next_state == "complete":
        # Save the lead
        lead = save_lead(lead_data)
        
        # Format the completion message
        prompt = next_config["prompt"].format(**lead_data)
        
        # Reset state
        set_lead_state(session, "idle")
        session.pop("lead_data", None)
        
        return {"response": prompt, "complete": True, "lead": lead}
    else:
        prompt = next_config["prompt"].format(**lead_data)
        return {"response": prompt, "complete": False, "lead": None}


def start_lead_capture(session: dict) -> str:
    """
    Start the lead capture process.
    Returns the initial prompt.
    """
    result = process_lead_capture(session, "")
    return result["response"]

# ---------------------------------------------------------------------------
# Lead Persistence
# ---------------------------------------------------------------------------

def _load_leads() -> list[dict]:
    """Load leads from the JSON file."""
    if not os.path.exists(LEADS_FILE):
        return []
    try:
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_leads(leads: list[dict]):
    """Save leads to the JSON file."""
    os.makedirs(os.path.dirname(LEADS_FILE), exist_ok=True)
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)


def save_lead(lead_data: dict) -> dict:
    """
    Save a new lead to the database.
    
    Args:
        lead_data: dict with name, interest, contact
    
    Returns:
        The saved lead dict with id and timestamp
    """
    leads = _load_leads()
    
    new_lead = {
        "id": len(leads) + 1,
        "name": lead_data.get("name", "Unknown"),
        "interest": lead_data.get("interest", "General"),
        "contact": lead_data.get("contact", "N/A"),
        "timestamp": datetime.now().isoformat(),
        "status": "new",
        "followup_sent": False,
    }
    
    leads.append(new_lead)
    _save_leads(leads)
    
    print(f"[LEADS] New lead captured: {new_lead['name']} - {new_lead['interest']}")
    return new_lead


def get_all_leads() -> list[dict]:
    """Get all captured leads."""
    return _load_leads()


def get_lead_count() -> int:
    """Get the total number of leads."""
    return len(_load_leads())
