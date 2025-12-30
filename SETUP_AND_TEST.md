# Ghost Teammate - Setup & Testing Guide

## Prerequisites

1. **Temporal** - Install the Temporal CLI:
   ```bash
   # macOS
   brew install temporal
   
   # Or download from https://temporal.io/download
   ```

2. **ngrok** - For exposing webhooks:
   ```bash
   brew install ngrok
   # Or download from https://ngrok.com/download
   ```

3. **Node.js 18+** - For the frontend

4. **Python 3.11+** - For the backend

---

## Step 1: Configure Environment Variables

### Backend (`backend/.env`)

```bash
# Copy example and fill in your keys
cp backend/.env.example backend/.env
```

Fill in these values:

```env
# Gemini (get from https://aistudio.google.com/apikey)
GEMINI_API_KEY=your-gemini-api-key

# Temporal (local dev server)
TEMPORAL_ADDRESS=localhost:7233
TEMPORAL_NAMESPACE=default

# Supabase (get from your project settings)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Resend (get from https://resend.com/api-keys)
RESEND_API_KEY=re_xxxxxxxxxxxxx
RESEND_WEBHOOK_SECRET=  # Leave empty for now

# Steel (get from https://app.steel.dev/settings/api-keys)
STEEL_API_KEY=your-steel-api-key
STEEL_CONNECT_URL=wss://connect.steel.dev/

# Supermemory (optional - get from https://supermemory.ai)
SUPERMEMORY_API_KEY=

# App URLs (update BACKEND_URL after starting ngrok)
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

### Frontend (`frontend/.env.local`)

```bash
cd frontend
cp .env.example .env.local  # Or create manually
```

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_STEEL_API_KEY=your-steel-api-key
```

---

## Step 2: Set Up Database

Push the schema to Supabase:

```bash
cd /Users/sriram.mk/Downloads/ghost

# Login to Supabase CLI
npx supabase login

# Link to your project
npx supabase link --project-ref your-project-ref

# Push the schema
npx supabase db push
```

---

## Step 3: Start All Services

Open **5 terminal windows/tabs**:

### Terminal 1: Temporal Server
```bash
temporal server start-dev
```
This starts Temporal on `localhost:7233` with the Web UI at `localhost:8233`

### Terminal 2: Backend Worker
```bash
cd /Users/sriram.mk/Downloads/ghost
export PYTHONPATH=$PYTHONPATH:$(pwd)
source venv/bin/activate
python -m backend.worker
```

### Terminal 3: Backend API
```bash
cd /Users/sriram.mk/Downloads/ghost
export PYTHONPATH=$PYTHONPATH:$(pwd)
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

### Terminal 4: ngrok (for Resend webhooks)
```bash
ngrok http 8000
```
Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

**Important:** Update `backend/.env` with the ngrok URL:
```env
BACKEND_URL=https://abc123.ngrok.io
```
Then restart the API server (Terminal 3)

### Terminal 5: Frontend
```bash
cd /Users/sriram.mk/Downloads/ghost/frontend
npm install  # First time only
npm run dev
```

---

## Step 4: Configure Resend Webhook

1. Go to [Resend Webhooks](https://resend.com/webhooks)
2. Add a new webhook:
   - **URL:** `https://your-ngrok-url.ngrok.io/webhooks/resend/inbound`
   - **Events:** Select `email.received` (for inbound emails)
3. Copy the webhook secret and add to `backend/.env`:
   ```env
   RESEND_WEBHOOK_SECRET=whsec_xxxxx
   ```

---

## Step 5: Testing

### Test 1: Health Check
```bash
curl http://localhost:8000/
# Should return: {"message":"The Ghost Teammate is active.","version":"1.0.0"}
```

### Test 2: Launch Task from Dashboard
1. Open http://localhost:3000
2. Click "NEW_TASK.EXE"
3. Enter a test goal: "Go to google.com and search for 'hello world'"
4. Click "Execute Protocol"
5. Watch the job appear and the Steel live view activate!

### Test 3: Launch Task via API
```bash
curl -X POST "http://localhost:8000/tasks/launch?goal=Go%20to%20google.com&user_id=test-user&user_email=your-email@example.com"
```

### Test 4: Create Agent Account
```bash
curl -X POST "http://localhost:8000/agent/accounts/create?user_id=test-user&platform=TestSite&platform_url=https://example.com"
```

### Test 5: View Temporal Workflows
Open http://localhost:8233 to see:
- Running workflows
- Activity history
- Signal/Query capabilities

### Test 6: Email Trigger (requires Resend domain)
Send an email to `assistant+test-user@your-verified-domain.com`
- This triggers a new workflow
- Check Temporal UI for the workflow

---

## Troubleshooting

### "No module named 'backend'"
Make sure you set PYTHONPATH:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### "Connection refused" to Temporal
Make sure Temporal server is running:
```bash
temporal server start-dev
```

### Steel session not showing
- Check Steel API key is correct
- Make sure `NEXT_PUBLIC_STEEL_API_KEY` is set in frontend

### Resend webhooks not working
- Verify ngrok is running and URL is correct
- Check webhook secret matches
- Test with: `curl -X POST https://your-ngrok-url/webhooks/resend/inbound -H "Content-Type: application/json" -d '{"from":"test@test.com","to":["assistant+test@domain.com"],"subject":"Test","text":"Hello"}'`

### Database errors
- Make sure schema is pushed: `npx supabase db push`
- Check Supabase dashboard for any migration errors

---

## Quick Reference: URLs

| Service | URL |
|---------|-----|
| Frontend Dashboard | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Temporal Web UI | http://localhost:8233 |
| API Docs (Swagger) | http://localhost:8000/docs |
| ngrok Inspector | http://127.0.0.1:4040 |

---

## Quick Reference: Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/tasks/launch` | POST | Launch a new task |
| `/webhooks/resend/inbound` | POST | Receive inbound emails |
| `/webhooks/resend/approve` | GET | Approve HITL action |
| `/webhooks/resend/reject` | GET | Reject HITL action |
| `/agent/accounts/create` | POST | Create agent account |
| `/agent/accounts` | GET | List agent accounts |

