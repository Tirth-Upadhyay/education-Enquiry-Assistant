# 🎓 AI Enquiry Assistant for Educational Institutes

> An AI-powered enquiry assistant that handles student queries, provides course recommendations, captures leads, and automates follow-ups — all through a WhatsApp-style chat interface.


**Problem Statement:** Educational Institutions – Enquiry Assistant

---

## 🎯 Problem

Many educational institutes lose potential students because of:
- ❌ Slow response to enquiries
- ❌ Repetitive manual answering of the same questions
- ❌ Poor lead capture and follow-up systems

## ✅ Solution

An AI-powered enquiry assistant that:
- 🤖 **Instantly answers** common queries (fees, placements, timings, etc.)
- 📚 **Recommends courses** based on student interests
- 📋 **Captures leads** (name, interest, contact) through conversational flow
- 🔄 **Provides follow-up** automation with stored lead data
- 💬 **WhatsApp-style UI** for familiar, engaging interaction

---

## 🏗️ Architecture

```
User (WhatsApp-style Chat UI)
         │
         ▼
   Frontend (HTML/CSS/JS)
         │
         ▼
   FastAPI Backend (/chat endpoint)
         │
         ▼
   Intent Detection Engine
   (Keyword + Fuzzy Matching)
         │
    ┌────┴────┐
    │         │
    ▼         ▼
 FAQ Data   LLM Fallback
 Course DB  (OpenAI/Groq)
    │         │
    └────┬────┘
         │
         ▼
   Response Generator
         │
         ▼
   Lead Capture State Machine
   (Name → Interest → Contact)
         │
         ▼
   JSON Database (leads.json)
         │
         ▼
   User Response + Quick Replies
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Intent Detection** | Keyword + fuzzy matching to classify user queries |
| 📚 **FAQ Matching** | 20 pre-built FAQs covering admissions, fees, placements |
| 🎯 **Course Recommendations** | Smart matching from 10-course catalog |
| 🤖 **LLM Fallback** | OpenAI/Groq API for unknown queries |
| 📋 **Lead Capture** | Conversational state machine (name → interest → contact) |
| 💾 **Data Persistence** | Leads stored in JSON for easy access |
| 🎨 **Premium Chat UI** | WhatsApp-style dark theme with animations |
| ⚡ **Quick Replies** | Context-aware suggestion buttons |
| 📊 **Admin Panel** | View captured leads via built-in modal |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, FastAPI |
| **AI/LLM** | OpenAI API / Groq API (with template fallback) |
| **NLP** | Custom intent detection + fuzzy matching |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Database** | JSON file storage |
| **Design** | WhatsApp-inspired dark theme, Inter font |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-enquiry-assistant.git
cd ai-enquiry-assistant

# Install dependencies
pip install -r requirements.txt

# (Optional) Set up API keys for LLM fallback
cp .env.example .env
# Edit .env and add your OpenAI or Groq API key
```

### Run the Application

```bash
# Start the server
uvicorn app:app --reload --port 8000

# Open in browser
# http://localhost:8000
```

### Test Conversation Flows

1. **Greeting**: "Hi" → Welcome message with quick replies
2. **Course Enquiry**: "What courses do you offer?" → Full course catalog
3. **Course Recommendation**: "I want to learn AI" → AI/ML course details
4. **FAQ**: "What are the placement stats?" → Placement information
5. **Lead Capture**: "I want to enroll" → Name → Interest → Contact flow
6. **LLM Fallback**: Any unknown query → AI-generated response

---

## 📁 Project Structure

```
ai-enquiry-assistant/
├── app.py                  # FastAPI backend server
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore
├── README.md
├── architecture.md        # Detailed architecture document
│
├── data/
│   ├── faq.json           # FAQ dataset (20 entries)
│   ├── courses.json       # Course catalog (10 courses)
│   └── leads.json         # Captured leads (auto-generated)
│
├── utils/
│   ├── __init__.py
│   ├── intent.py          # Intent detection engine
│   ├── llm.py             # LLM integration (OpenAI/Groq)
│   └── leads.py           # Lead capture state machine
│
└── frontend/
    ├── index.html          # Chat UI
    ├── style.css           # WhatsApp-style dark theme
    └── script.js           # Frontend chat logic
```

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send a message and get AI response |
| `GET` | `/leads` | View all captured leads |
| `GET` | `/health` | Health check |
| `GET` | `/` | Serve the chat UI |

### Chat Request Body
```json
{
    "message": "What courses do you offer?",
    "session_id": "optional-uuid"
}
```

### Chat Response
```json
{
    "response": "Here are our available courses...",
    "session_id": "uuid",
    "intent": "course_enquiry",
    "quick_replies": ["📚 View Courses", "📝 Enroll Now"],
    "courses": []
}
```

---

## 🎥 Demo

[Add your demo video link here]

---

## 📝 Key Design Decisions

1. **Fuzzy matching over strict NLP** — Lightweight, fast, no heavy ML models needed
2. **State machine for lead capture** — Deterministic flow ensures all data is collected
3. **LLM as fallback, not primary** — Reduces API costs, improves response speed
4. **Template responses when no API key** — Works out-of-the-box without external dependencies
5. **WhatsApp-style UI** — Familiar interface reduces user friction

---

## 🔮 Future Improvements

- WhatsApp Business API integration for real-time messaging
- Google Sheets / Firebase for lead storage
- Email/SMS notification on lead capture
- Multi-language support (Hindi, regional languages)
- Analytics dashboard for lead conversion tracking
- Appointment booking for demo classes

---

## 👤 Author

**Tirth Upadhyay**  


---

*This project demonstrates practical AI application in educational institute operations, focusing on automation, lead management, and intelligent query handling.*
