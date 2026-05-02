"""
Intent Detection Module
-----------------------
Detects user intent from messages using keyword matching and fuzzy matching.
Supports intents: greeting, farewell, faq, course_enquiry, course_recommendation,
lead_capture, followup, help, and unknown.
"""
from __future__ import annotations

import json
import os
import re
from difflib import SequenceMatcher

# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def _load_json(filename: str):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

FAQ_DATA = _load_json("faq.json")
COURSE_DATA = _load_json("courses.json")

# ---------------------------------------------------------------------------
# Keyword Banks
# ---------------------------------------------------------------------------

GREETING_KEYWORDS = [
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "greetings", "namaste", "hola", "sup", "yo", "howdy", "what's up",
    "whats up", "hii", "hiii", "helloo", "hellooo",
]

FAREWELL_KEYWORDS = [
    "bye", "goodbye", "see you", "thanks", "thank you", "thank", "ok bye",
    "take care", "later", "tata", "cya", "farewell",
]

HELP_KEYWORDS = [
    "help", "assist", "support", "guide", "how does this work", "menu",
    "options", "what can you do",
]

LEAD_INTENT_KEYWORDS = [
    "interested", "enroll", "enrol", "join", "sign up", "register",
    "admission", "admit", "i want to join", "i want to enroll",
    "book a demo", "callback", "call me", "contact me",
    "i am interested", "i'm interested", "want to apply",
]

COURSE_ENQUIRY_KEYWORDS = [
    "course", "courses", "program", "programs", "what do you offer",
    "what do you teach", "curriculum", "syllabus", "subjects", "all courses",
    "available courses", "list of courses",
]

COURSE_RECOMMENDATION_KEYWORDS = [
    "recommend", "suggest", "best course", "which course", "suitable",
    "right course", "career", "should i learn", "i want to learn",
    "interested in", "want to study", "looking for",
]

# ---------------------------------------------------------------------------
# Fuzzy Matching Helpers
# ---------------------------------------------------------------------------

def _similarity(a: str, b: str) -> float:
    """Return similarity ratio between two strings (0-1)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _keyword_match(message: str, keywords: list[str], threshold: float = 0.75) -> float:
    """
    Return the best match score for the message against a list of keywords.
    Uses exact substring check first, then fuzzy matching for longer words.
    """
    msg_lower = message.lower().strip()
    best_score = 0.0

    for kw in keywords:
        # Exact substring match (most reliable)
        if kw in msg_lower:
            score = 1.0
        else:
            # For multi-word keywords, check phrase similarity
            if " " in kw:
                phrase_score = _similarity(kw, msg_lower)
                score = phrase_score if phrase_score >= 0.75 else 0.0
            else:
                # Single-word keyword: fuzzy match against each word in message
                # Only consider words with 4+ characters to avoid false matches
                words = msg_lower.split()
                word_scores = []
                for w in words:
                    if len(w) >= 4 and len(kw) >= 4:
                        sim = _similarity(w, kw)
                        # Require high similarity for fuzzy match
                        if sim >= 0.85:
                            word_scores.append(sim)
                score = max(word_scores) if word_scores else 0.0

        best_score = max(best_score, score)

    return best_score

# ---------------------------------------------------------------------------
# FAQ Matching
# ---------------------------------------------------------------------------

def match_faq(message: str) -> dict | None:
    """
    Try to match the user message against the FAQ dataset.
    Returns the best matching FAQ entry or None.
    """
    msg_lower = message.lower().strip()
    best_match = None
    best_score = 0.0

    for faq in FAQ_DATA:
        # Check keyword overlap
        kw_score = _keyword_match(msg_lower, faq["keywords"])

        # Check question similarity
        q_score = _similarity(msg_lower, faq["question"].lower())

        score = max(kw_score, q_score)

        if score > best_score:
            best_score = score
            best_match = faq

    if best_score >= 0.70:
        return {"faq": best_match, "confidence": round(best_score, 3)}

    return None

# ---------------------------------------------------------------------------
# Course Matching
# ---------------------------------------------------------------------------

def match_course(message: str) -> list[dict]:
    """
    Find courses that match the user's interest.
    Returns a list of matching courses sorted by relevance.
    """
    msg_lower = message.lower().strip()
    scored_courses = []

    for course in COURSE_DATA:
        kw_score = _keyword_match(msg_lower, course["keywords"])
        name_score = _similarity(msg_lower, course["name"].lower())
        score = max(kw_score, name_score)

        if score >= 0.50:
            scored_courses.append({"course": course, "score": score})

    scored_courses.sort(key=lambda x: x["score"], reverse=True)
    return scored_courses[:3]  # Return top 3 matches

# ---------------------------------------------------------------------------
# Main Intent Detection
# ---------------------------------------------------------------------------

def detect_intent(message: str) -> dict:
    """
    Detect the intent of a user message.

    Returns:
        dict with keys:
            - intent: str (greeting, farewell, faq, course_enquiry,
                          course_recommendation, lead_capture, help, unknown)
            - confidence: float (0-1)
            - data: dict (extra data depending on intent, e.g. matched FAQ or course)
    """
    msg = message.strip()
    if not msg:
        return {"intent": "unknown", "confidence": 0.0, "data": {}}

    msg_lower = msg.lower()
    word_count = len(msg_lower.split())

    # 1. Greeting check (short messages only)
    greeting_score = _keyword_match(msg_lower, GREETING_KEYWORDS)
    if greeting_score >= 0.85 and word_count <= 4:
        return {"intent": "greeting", "confidence": greeting_score, "data": {}}

    # 2. Farewell check (short messages only)
    farewell_score = _keyword_match(msg_lower, FAREWELL_KEYWORDS)
    if farewell_score >= 0.80 and word_count <= 5:
        return {"intent": "farewell", "confidence": farewell_score, "data": {}}

    # 3. Help check
    help_score = _keyword_match(msg_lower, HELP_KEYWORDS)
    if help_score >= 0.85:
        return {"intent": "help", "confidence": help_score, "data": {}}

    # 4. Score all competing intents and pick the best
    rec_score = _keyword_match(msg_lower, COURSE_RECOMMENDATION_KEYWORDS)
    enq_score = _keyword_match(msg_lower, COURSE_ENQUIRY_KEYWORDS)
    lead_score = _keyword_match(msg_lower, LEAD_INTENT_KEYWORDS)

    # Build candidates list: (intent_name, score, min_threshold)
    candidates = []

    if enq_score >= 0.65:
        candidates.append(("course_enquiry", enq_score))
    if rec_score >= 0.65:
        candidates.append(("course_recommendation", rec_score))
    if lead_score >= 0.80:
        candidates.append(("lead_capture", lead_score))

    # Pick the best scoring intent
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        winner, score = candidates[0]

        if winner == "course_enquiry":
            return {
                "intent": "course_enquiry",
                "confidence": score,
                "data": {"courses": COURSE_DATA},
            }
        elif winner == "course_recommendation":
            courses = match_course(msg_lower)
            return {
                "intent": "course_recommendation",
                "confidence": score,
                "data": {"courses": courses},
            }
        elif winner == "lead_capture":
            return {"intent": "lead_capture", "confidence": score, "data": {}}

    # 5. FAQ matching
    faq_result = match_faq(msg_lower)
    if faq_result:
        return {
            "intent": "faq",
            "confidence": faq_result["confidence"],
            "data": faq_result,
        }

    # 6. Try course matching as fallback (direct subject match)
    courses = match_course(msg_lower)
    if courses and courses[0]["score"] >= 0.60:
        return {
            "intent": "course_recommendation",
            "confidence": courses[0]["score"],
            "data": {"courses": courses},
        }

    # 7. If lead intent had a weaker score, still try it
    if lead_score >= 0.65:
        return {"intent": "lead_capture", "confidence": lead_score, "data": {}}

    # 8. Unknown — will go to LLM fallback
    return {"intent": "unknown", "confidence": 0.0, "data": {}}

