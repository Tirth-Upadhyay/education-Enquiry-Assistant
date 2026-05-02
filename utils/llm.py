"""
LLM Integration Module
-----------------------
Provides AI-powered fallback responses using OpenAI / Groq API.
Falls back to intelligent template responses if no API key is configured.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

SYSTEM_PROMPT = """You are a friendly and professional AI assistant for TechEd Institute, 
a leading educational institution offering technology courses. Your role is to:

1. Answer questions about courses, admissions, fees, placements, and general queries
2. Be warm, helpful, and conversational
3. Encourage students to explore courses and share their interests
4. If you don't know something specific, suggest the student connect with an admissions counselor
5. Keep responses concise (2-4 sentences) and use a friendly tone
6. Use emojis occasionally to keep the conversation engaging

Available courses: AI & Machine Learning, Full-Stack Web Development, Data Science & Analytics, 
Cloud Computing & DevOps, Cybersecurity, Mobile App Development, UI/UX Design, Digital Marketing, 
Python Programming (Foundation), Blockchain & Web3 Development.

Key facts:
- 85% placement rate
- Average package: ₹4.5 LPA, top package: ₹12 LPA
- EMI and scholarship options available
- Online, offline, and hybrid modes
- Industry mentors from top companies
"""

# ---------------------------------------------------------------------------
# Template Responses (Fallback when no API key)
# ---------------------------------------------------------------------------

TEMPLATE_RESPONSES = [
    "That's a great question! 😊 While I don't have the specific answer right now, I'd love to connect you with our admissions team who can help in detail. Would you like to share your contact details?",
    "Thanks for asking! 🎓 I want to make sure you get the most accurate information. Let me recommend speaking with our counselor for detailed guidance. Meanwhile, is there anything else about our courses I can help with?",
    "I appreciate your curiosity! 💡 For this specific query, our admissions team would be the best to assist you. Would you like me to arrange a callback? Just share your name and phone number!",
    "That's an interesting question! 🤔 I'd suggest reaching out to our admissions desk for the most up-to-date information on this. In the meantime, would you like to know about our popular courses?",
    "Great question! 🌟 Let me connect you with someone who can provide detailed information. Would you be interested in a free counseling session? I can help set that up!",
]

_template_index = 0

def _get_template_response() -> str:
    """Cycle through template responses."""
    global _template_index
    response = TEMPLATE_RESPONSES[_template_index % len(TEMPLATE_RESPONSES)]
    _template_index += 1
    return response

# ---------------------------------------------------------------------------
# LLM API Call
# ---------------------------------------------------------------------------

async def get_llm_response(user_message: str, conversation_history: list[dict] = None) -> str:
    """
    Get an AI-generated response for the user's message.
    
    Tries OpenAI first, then Groq, then falls back to templates.
    
    Args:
        user_message: The user's message
        conversation_history: Optional list of previous messages for context
    
    Returns:
        AI-generated response string
    """
    
    # Build messages list
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if conversation_history:
        # Add last 6 messages for context
        for msg in conversation_history[-6:]:
            messages.append(msg)
    
    messages.append({"role": "user", "content": user_message})
    
    # Try OpenAI
    if OPENAI_API_KEY:
        try:
            return await _call_openai(messages)
        except Exception as e:
            print(f"[LLM] OpenAI error: {e}")
    
    # Try Groq
    if GROQ_API_KEY:
        try:
            return await _call_groq(messages)
        except Exception as e:
            print(f"[LLM] Groq error: {e}")
    
    # Fallback to templates
    print("[LLM] No API key configured, using template response")
    return _get_template_response()


async def _call_openai(messages: list[dict]) -> str:
    """Call OpenAI API."""
    import httpx
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": 200,
                "temperature": 0.7,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


async def _call_groq(messages: list[dict]) -> str:
    """Call Groq API (faster, free tier available)."""
    import httpx
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": messages,
                "max_tokens": 200,
                "temperature": 0.7,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
