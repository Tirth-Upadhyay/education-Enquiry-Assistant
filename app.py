"""
AI Enquiry Assistant - Main Application
========================================
FastAPI backend for the AI-powered educational enquiry assistant.
Handles chat interactions, intent detection, FAQ matching, LLM fallback,
lead capture, and session management.
"""
from __future__ import annotations

import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List

from utils.intent import detect_intent, COURSE_DATA
from utils.llm import get_llm_response
from utils.leads import (
    is_in_lead_capture,
    process_lead_capture,
    start_lead_capture,
    get_all_leads,
    get_lead_count,
)

# ---------------------------------------------------------------------------
# App Setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Enquiry Assistant",
    description="AI-powered enquiry assistant for educational institutions",
    version="1.0.0",
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# ---------------------------------------------------------------------------
# Session Management (in-memory)
# ---------------------------------------------------------------------------

sessions: dict[str, dict] = {}


def get_session(session_id: str) -> dict:
    """Get or create a session."""
    if session_id not in sessions:
        sessions[session_id] = {
            "id": session_id,
            "history": [],
            "lead_state": "idle",
            "user_name": None,
        }
    return sessions[session_id]

# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: str
    quick_replies: List[str] = []
    courses: List[dict] = []

# ---------------------------------------------------------------------------
# Response Builders
# ---------------------------------------------------------------------------

def _build_greeting_response(session: dict) -> str:
    name = session.get("user_name")
    if name:
        return f"Welcome back, {name}! 👋 How can I help you today? You can ask me about our courses, fees, placements, or anything else!"
    return "Hello! 👋 Welcome to **TechEd Institute**! I'm your AI assistant, here to help you explore our courses, answer questions, and get you started on your learning journey. 🎓\n\nHow can I help you today?"


def _build_farewell_response(session: dict) -> str:
    name = session.get("user_name")
    if name:
        return f"Goodbye, {name}! 😊 It was great chatting with you. Feel free to come back anytime. Wishing you all the best! 🌟"
    return "Thank you for chatting with us! 😊 Feel free to come back anytime you have questions. Have a wonderful day! 🌟"


def _build_help_response() -> str:
    return """I'm here to help! 🤖 Here's what I can assist you with:

📚 **Courses** — Browse our course catalog and get recommendations
💰 **Fees** — Learn about our fee structure and payment plans
🎯 **Placements** — Check our placement stats and hiring partners
📋 **Admissions** — Understand the admission process
⏰ **Timings** — Know our batch schedules
🎓 **Scholarships** — Explore financial aid options
📝 **Enroll** — Start the enrollment process

Just ask me anything, or tap one of the quick replies below! 👇"""


def _build_course_list_response() -> str:
    lines = ["Here are our available courses! 📚\n"]
    for i, course in enumerate(COURSE_DATA, 1):
        lines.append(f"**{i}. {course['name']}**")
        lines.append(f"   ⏱️ {course['duration']} | 💰 {course['fee_display']} | 📊 {course['level']}")
        lines.append("")
    lines.append("Would you like details about any specific course? Or I can recommend one based on your interests! 🎯")
    return "\n".join(lines)


def _build_course_recommendation_response(courses: list[dict]) -> str:
    if not courses:
        return "I'd love to help you find the right course! 🤔 Could you tell me more about your interests or career goals?"

    lines = ["Based on your interest, here are my top recommendations! 🎯\n"]
    for i, item in enumerate(courses, 1):
        c = item["course"]
        lines.append(f"**{i}. {c['name']}** ⭐")
        lines.append(f"   📝 {c['description'][:100]}...")
        lines.append(f"   ⏱️ Duration: {c['duration']} | 💰 Fee: {c['fee_display']}")
        lines.append(f"   🎯 Careers: {', '.join(c['career_paths'][:3])}")
        lines.append("")

    lines.append("Would you like more details about any of these, or would you like to **enroll**? 😊")
    return "\n".join(lines)


def _build_faq_response(faq_data: dict) -> str:
    faq = faq_data["faq"]
    return f"{faq['answer']}\n\nDo you have any other questions? 😊"


def _get_quick_replies(intent: str) -> list[str]:
    """Return context-appropriate quick reply suggestions."""
    base = {
        "greeting": ["📚 View Courses", "💰 Fee Structure", "🎯 Placements", "📝 Enroll Now"],
        "farewell": [],
        "help": ["📚 View Courses", "💰 Fees", "🎯 Placements", "📝 Enroll"],
        "course_enquiry": ["🤖 AI & ML Course", "💻 Web Development", "📊 Data Science", "📝 Enroll Now"],
        "course_recommendation": ["📝 Enroll Now", "📚 More Courses", "💰 Fee Details", "❓ More Info"],
        "faq": ["📚 View Courses", "📝 Enroll Now", "❓ More Questions"],
        "lead_capture": [],
        "unknown": ["📚 View Courses", "💰 Fees", "🎯 Placements", "❓ Help"],
    }
    return base.get(intent, ["📚 View Courses", "❓ Help"])

# ---------------------------------------------------------------------------
# Main Chat Endpoint
# ---------------------------------------------------------------------------

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return a response."""
    
    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())
    session = get_session(session_id)
    message = request.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Add user message to history
    session["history"].append({"role": "user", "content": message})

    # --- Check if we're in lead capture flow ---
    if is_in_lead_capture(session):
        result = process_lead_capture(session, message)
        response_text = result["response"]
        intent = "lead_capture"
        
        # Store user name if captured
        if session.get("lead_data", {}).get("name"):
            session["user_name"] = session["lead_data"]["name"]
        
        quick_replies = [] if not result["complete"] else ["📚 View Courses", "❓ More Questions"]
        
        session["history"].append({"role": "assistant", "content": response_text})
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            intent=intent,
            quick_replies=quick_replies,
        )

    # --- Normal intent detection ---
    intent_result = detect_intent(message)
    intent = intent_result["intent"]
    data = intent_result["data"]
    courses_list = []

    if intent == "greeting":
        response_text = _build_greeting_response(session)

    elif intent == "farewell":
        response_text = _build_farewell_response(session)

    elif intent == "help":
        response_text = _build_help_response()

    elif intent == "course_enquiry":
        response_text = _build_course_list_response()
        courses_list = [{"name": c["name"], "slug": c["slug"]} for c in COURSE_DATA]

    elif intent == "course_recommendation":
        courses = data.get("courses", [])
        response_text = _build_course_recommendation_response(courses)
        courses_list = [{"name": c["course"]["name"], "slug": c["course"]["slug"]} for c in courses]

    elif intent == "faq":
        response_text = _build_faq_response(data)

    elif intent == "lead_capture":
        response_text = start_lead_capture(session)
        intent = "lead_capture"

    else:
        # LLM Fallback for unknown intents
        response_text = await get_llm_response(
            message,
            session["history"][-6:] if len(session["history"]) > 1 else None,
        )

    quick_replies = _get_quick_replies(intent)

    # Save assistant response to history
    session["history"].append({"role": "assistant", "content": response_text})

    return ChatResponse(
        response=response_text,
        session_id=session_id,
        intent=intent,
        quick_replies=quick_replies,
        courses=courses_list,
    )

# ---------------------------------------------------------------------------
# Admin Endpoints
# ---------------------------------------------------------------------------

@app.get("/leads")
async def list_leads():
    """Get all captured leads."""
    leads = get_all_leads()
    return {
        "total": len(leads),
        "leads": leads,
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Enquiry Assistant",
        "leads_captured": get_lead_count(),
    }


# Serve frontend
@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML."""
    return FileResponse("frontend/index.html")
