# Supabase & Vector Memory (Supermemory)

## Database Schema

### `users` (Supabase Auth)
- Extension of auth.users: `full_name`, `avatar_url`.

### `teammate_accounts`
- `id`: uuid
- `user_id`: uuid (owner)
- `platform`: text (notion, google, linear)
- `email`: text (the teammate's dedicated email)
- `credentials_vault_id`: text (reference to encrypted storage for teammate login)

### `workflows`
- `id`: uuid
- `user_id`: uuid
- `temporal_workflow_id`: text
- `status`: enum (running, waiting_approval, completed, failed)
- `last_screenshot_url`: text (for dashboard)
- `current_goal`: text

### `memory` (The "Supermemory")
- `id`: uuid
- `user_id`: uuid
- `content`: text
- `embedding`: vector(1536)
- `metadata`: jsonb (platform, importance, type: "user_preference" | "sop" | "fact")
- `created_at`: timestamptz

### `task_logs`
- `id`: uuid
- `workflow_id`: uuid
- `action`: text
- `reasoning`: text
- `outcome`: text
- `screenshot_url`: text
