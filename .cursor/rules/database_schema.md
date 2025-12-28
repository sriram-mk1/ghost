# Supabase Schema & Job Tracking

## Database Tables

### `profiles`
```sql
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  full_name TEXT,
  email_address TEXT UNIQUE,
  persona_config JSONB DEFAULT '{"style": "professional", "verbosity": "medium"}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### `workspaces`
```sql
CREATE TABLE workspaces (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  platform_name TEXT NOT NULL, -- 'Notion', 'GoogleDocs', 'Linear'
  agent_email TEXT, -- The assistant's dedicated account email for this platform
  credentials_vault_id UUID, -- Reference to an encrypted secret store or separate table
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### `jobs`
```sql
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id),
  temporal_workflow_id TEXT UNIQUE, -- ID used in Temporal
  status TEXT DEFAULT 'pending', -- 'running', 'waiting_approval', 'completed', 'failed'
  last_resend_thread_id TEXT, -- Maps the job to a Resend email thread
  steel_session_id TEXT, -- ID to reconnect to the virtual browser
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### `approvals`
```sql
CREATE TABLE approvals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(id),
  action_type TEXT, -- 'delete', 'update', 'payment'
  description TEXT, -- "Delete the 'Old Specs' folder"
  screenshot_url TEXT, -- Visual proof from Steel
  status TEXT DEFAULT 'pending', -- 'approved', 'rejected'
  resend_message_id TEXT, -- ID of the approval email sent
  decided_at TIMESTAMPTZ
);
```

### `memories` (Supermemory Complement)
- While primary memory lives in Supermemory, we can store local vector backups if needed.
```sql
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE TABLE memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id),
  content TEXT NOT NULL,
  metadata JSONB,
  embedding VECTOR(1536),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```
