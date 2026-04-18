# Gmail Subscription Cleanup

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
                        └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   OpenAI API    │
                        └─────────────────┘
```

## Features

- **OAuth2 Gmail Authentication** - Secure access to your Gmail
- **Smart Scanning** - Scans Promotions and Updates categories
- **Unsubscribe Link Extraction** - Automatically finds unsubscribe links from headers and email bodies
- **AI Descriptions** - Uses OpenAI GPT-4o-mini to generate subscription descriptions
- **Interactive UI** - Review subscriptions with email previews
- **Manual Unsubscribe** - Opens unsubscribe links in browser for safe manual completion

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Google Cloud project with Gmail API enabled
- OpenAI API key

## Setup

### 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to APIs & Services > Library
   - Search for "Gmail API"
   - Click Enable

4. Configure OAuth consent screen:
   - Go to APIs & Services > OAuth consent screen
   - Choose "External" type
   - Fill in app name and user support email
   - Add your email as a test user

5. Create OAuth credentials:
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Gmail Subscription Cleanup"
   - Download the JSON file

6. Move credentials:
   ```bash
   mv ~/Users/sandeep/Downloads/client_secret_gmail_api.json credentials/credentials.json
   ```

### 2. Environment Variables

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=sk-your-openai-api-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
REDIRECT_URI=http://localhost:8000/auth/callback
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Run the Application

You'll need two terminal windows:

**Terminal 1 - Backend:**
```bash
uv run uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
uv run streamlit run frontend/app.py --port 8501
```

### 5. Authenticate

1. Open http://localhost:8501 in your browser
2. Click "Authenticate with Gmail"
3. Complete the OAuth flow in the browser
4. Return to the app and refresh

## Usage

### Scanning Subscriptions

1. Select scan period (30, 60, or 90 days)
2. Click "Scan" to find subscriptions
3. Wait for the scan to complete
4. Review each subscription with email previews

### Managing Subscriptions

- **Show emails** - Expand to see recent email examples
- **Keep** - Mark subscription as one you want to keep
- **Remove** - Mark subscription for removal
- **Generate Description** - Get AI-generated description
- **Unsubscribe** - Opens unsubscribe link in browser

### Batch Unsubscribe

After marking subscriptions for removal, click "Unsubscribe from X Marked" to open all unsubscribe links in your browser.

## Running Tests

```bash
uv run pytest tests/ -v
```

## Project Structure

```
gmail-subscription-cleanup/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── auth/
│   │   └── gmail_auth.py    # OAuth2 authentication
│   ├── services/
│   │   ├── gmail_service.py # Gmail API integration
│   │   ├── unsubscribe.py    # Link extraction
│   │   └── openai_service.py # AI descriptions
│   ├── models/
│   │   └── subscription.py   # Pydantic models
│   └── db/
│       └── database.py       # SQLite operations
├── frontend/
│   ├── app.py               # Streamlit application
│   ├── config.py            # Frontend config
│   └── components/
│       └── subscription_card.py
├── tests/                   # Unit tests
├── credentials/             # OAuth credentials (gitignored)
└── SPEC.md                  # Technical specification
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/auth/url` | Get OAuth URL |
| GET | `/auth/callback` | OAuth callback |
| GET | `/auth/status` | Check auth status |
| POST | `/auth/logout` | Logout |
| POST | `/scan` | Scan emails |
| GET | `/scan/status` | Scan status |
| GET | `/subscriptions` | List subscriptions |
| GET | `/subscriptions/{id}` | Get subscription with emails |
| POST | `/subscriptions/{id}/generate-description` | AI description |
| POST | `/subscriptions/{id}/unsubscribe` | Open unsubscribe link |
| DELETE | `/subscriptions/{id}` | Remove subscription |

## Security Notes

- OAuth tokens are stored locally in `token.json`
- No credentials are stored in the database
- All API keys are loaded from environment variables
- The `.env` file is gitignored

## Troubleshooting

### "Credentials file not found"
Make sure you've downloaded OAuth credentials and placed them at `credentials/credentials.json`

### "Authentication failed"
1. Check that you're using a test account added to OAuth consent screen
2. Verify your credentials.json is correctly formatted
3. Try deleting `token.json` and re-authenticating

### Scan returns no subscriptions
1. Make sure you have emails in Promotions or Updates categories
2. Check the scan date range (try 90 days)
3. Verify Gmail API is enabled in your project

## License

MIT
