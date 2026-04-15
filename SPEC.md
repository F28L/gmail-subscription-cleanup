# Gmail Subscription Cleanup - Technical Specification

## Overview

A web application that scans Gmail for promotional/subscription emails, extracts unsubscribe links, and provides an interface to review and manage subscriptions with AI-generated descriptions.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│   FastAPI       │────▶│   Gmail API     │
│   (Frontend)    │     │   (Backend)     │     │                 │
│   Port: 8501    │     │   Port: 8000    │     │   OAuth2 Auth   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   SQLite DB     │
                        │  (Subscriptions)│
                        └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   OpenAI API    │
                        │ (Descriptions)  │
                        └─────────────────┘
```

## Tech Stack

| Component | Package | Purpose |
|-----------|---------|---------|
| Package Manager | `uv` | Fast Python package manager |
| Backend Framework | `fastapi` + `uvicorn` | REST API |
| Frontend | `streamlit` | UI framework |
| Gmail API | `google-api-python-client` | Gmail access |
| OpenAI | `openai` | AI description generation |
| Database | `sqlite` + `aiosqlite` | Async local persistence |
| HTML Parsing | `beautifulsoup4` + `lxml` | Extract unsubscribe links, render emails |
| HTTP Client | `httpx` | Async HTTP for unsubscribe |
| Email Parsing | `email` (stdlib) | Parse email MIME content |
| Testing | `pytest` + `pytest-asyncio` | Unit tests |

## Project Structure

```
gmail-subscription-cleanup/
├── pyproject.toml              # UV project config
├── uv.lock
├── SPEC.md                     # This file
├── README.md
│
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Settings (env vars)
│   ├── auth/
│   │   ├── __init__.py
│   │   └── gmail_auth.py       # OAuth2 flow
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gmail_service.py    # Gmail API interactions
│   │   ├── unsubscribe.py      # Extract & open links
│   │   └── openai_service.py   # AI description generation
│   ├── models/
│   │   ├── __init__.py
│   │   └── subscription.py     # Pydantic models
│   └── db/
│       ├── __init__.py
│       └── database.py         # SQLite operations
│
├── frontend/
│   ├── __init__.py
│   ├── app.py                  # Streamlit entry
│   ├── components/
│   │   ├── __init__.py
│   │   └── subscription_card.py # Expandable card component
│   └── config.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_unsubscribe.py     # Unsubscribe link extraction
│   ├── test_openai_service.py  # OpenAI service tests
│   ├── test_database.py        # Database operations
│   └── test_models.py          # Pydantic model tests
│
└── credentials/
    └── .gitkeep                # For credentials.json
```

## Data Models

### Subscription
```python
{
    "id": str,                  # UUID
    "name": str,                # From sender domain or AI
    "email": str,               # From email address
    "domain": str,              # Sender domain
    "unsubscribe_url": str,     # Primary unsubscribe link
    "description": str | None,  # AI-generated description
    "email_count": int,         # Total emails from sender
    "last_email_date": datetime,
    "created_at": datetime,
    "updated_at": datetime
}
```

### EmailExample
```python
{
    "id": str,                  # UUID
    "subscription_id": str,     # Foreign key
    "gmail_message_id": str,    # Original Gmail message ID
    "subject": str,
    "snippet": str,             # First 200 chars
    "date": datetime,
    "body_preview": str         # First 500 chars, simplified HTML
}
```

## API Endpoints

### Health & Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/auth/url` | Get Gmail OAuth URL |
| `GET` | `/auth/callback` | OAuth callback handler |
| `GET` | `/auth/status` | Check if authenticated |

### Scanning
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/scan` | Trigger email scan |
| `GET` | `/scan/status` | Get current scan status |

### Subscriptions
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/subscriptions` | List all subscriptions |
| `GET` | `/subscriptions/{id}` | Get subscription + 5 email examples |
| `POST` | `/subscriptions/{id}/generate-description` | AI generate description |
| `POST` | `/subscriptions/{id}/unsubscribe` | Open unsubscribe link |
| `DELETE` | `/subscriptions/{id}` | Remove subscription |

### Request/Response Models

**POST /scan**
```json
{
    "days": 30  // 30, 60, or 90
}
```

**POST /subscriptions/{id}/generate-description**
```json
{
    "emails": [
        {"subject": "...", "body_preview": "..."},
        ...
    ]
}
```

## Frontend UI

### Layout
- **Header**: App title, Re-scan button, Scan days dropdown (30/60/90), Logout
- **Main Area**: List of subscription cards
- **Status Bar**: Subscription count, marked for removal count

### Subscription Card Component
- **Collapsed State**:
  - Subscription name
  - Description (or "Generating..." placeholder)
  - Stats: email count, last email date
  - Buttons: [Keep] [Remove]
  - Expand toggle (▼/▲)

- **Expanded State**:
  - Last 5 email examples in a collapsible list
  - Each email shows: subject, date, body preview

### Actions
- **Keep**: Default state, no action
- **Remove**: Marks for removal, enables unsubscribe button
- **Unsubscribe Selected**: Opens unsubscribe URL in browser

## Implementation Phases

### Phase 1: Project Setup
- [ ] Initialize UV project
- [ ] Configure pyproject.toml with dependencies
- [ ] Set up directory structure
- [ ] Create .gitignore

### Phase 2: Backend Core
- [ ] Config module (settings from env)
- [ ] Pydantic models
- [ ] SQLite database layer
- [ ] Unit tests for database

### Phase 3: Gmail Integration
- [ ] OAuth2 authentication flow
- [ ] Gmail service (fetch emails, extract links)
- [ ] Unsubscribe link extraction (headers + body)
- [ ] Unit tests for Gmail service

### Phase 4: OpenAI Integration
- [ ] OpenAI service for descriptions
- [ ] Unit tests for OpenAI service

### Phase 5: FastAPI Backend
- [ ] All API endpoints
- [ ] Integration with services
- [ ] Error handling

### Phase 6: Frontend
- [ ] Streamlit app structure
- [ ] Subscription card component
- [ ] API integration
- [ ] UI state management

### Phase 7: Integration & Polish
- [ ] End-to-end testing
- [ ] README documentation
- [ ] Environment setup instructions

## Environment Variables

```bash
# Backend (.env)
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
REDIRECT_URI=http://localhost:8000/auth/callback
DATABASE_URL=sqlite+aiosqlite:///./subscriptions.db

# Frontend (.streamlit/secrets.toml)
API_BASE_URL=http://localhost:8000
```

## Gmail API Setup Instructions

1. Go to Google Cloud Console
2. Create new project or select existing
3. Enable Gmail API
4. Configure OAuth consent screen
5. Create OAuth 2.0 credentials (Desktop app)
6. Download credentials.json to `credentials/` folder

## Running the Application

```bash
# Terminal 1 - Backend
uv run uvicorn backend.main:app --reload --port 8000

# Terminal 2 - Frontend
uv run streamlit run frontend/app.py --port 8501
```

## Security Considerations

- OAuth tokens stored locally in `token.json`
- API keys loaded from environment variables
- No credentials in code or git
- SQLite database is local file only

## Testing Strategy

Each component should have unit tests:
- **test_unsubscribe.py**: Link extraction from headers and HTML
- **test_openai_service.py**: Description generation mock tests
- **test_database.py**: CRUD operations with in-memory DB
- **test_models.py**: Pydantic validation tests

## Constants

- **OpenAI Model**: `gpt-4o-mini`
- **Default Scan Days**: 30
- **Email Examples Per Subscription**: 5
- **Body Preview Length**: 500 characters
- **Snippet Length**: 200 characters
