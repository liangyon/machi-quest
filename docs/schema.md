
---

## Table: `users`

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| `id` | UUID | PK, default gen_random_uuid() | Unique user ID |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User’s email address |
| `hashed_password` | TEXT | NOT NULL | Argon2 or bcrypt hash |
| `display_name` | VARCHAR(100) |  | Public display name |
| `avatar_url` | TEXT |  | Optional user avatar |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT now() | Creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT now() | Last update |

---

## Table: `pets`

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| `id` | UUID | PK, default gen_random_uuid() | Pet ID |
| `user_id` | UUID | FK → users.id, NOT NULL | Owner of the pet |
| `name` | VARCHAR(100) |  | Pet name |
| `species` | VARCHAR(50) | DEFAULT 'default' | Pet type or model ID |
| `state_json` | JSONB | DEFAULT '{}'::jsonb | Current pet state (energy, hunger, level, mood) |
| `version` | INT | DEFAULT 1 | State versioning for idempotent updates |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT now() | Creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT now() | Update time |

---

## Table: `integrations`

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| `id` | UUID | PK | Integration ID |
| `user_id` | UUID | FK → users.id | Owner |
| `provider` | VARCHAR(50) | NOT NULL | e.g. `'github'`, `'fitbit'`, `'notion'` |
| `access_token_encrypted` | BYTEA |  | Encrypted OAuth token |
| `refresh_token_encrypted` | BYTEA |  | Encrypted refresh token |
| `metadata` | JSONB | DEFAULT '{}'::jsonb | Provider-specific metadata (e.g. repo name) |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT now() | Created timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT now() | Updated timestamp |

---

## Table: `event_raw`

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| `id` | UUID | PK | EventRaw ID |
| `integration_id` | UUID | FK → integrations.id | Source integration |
| `external_event_id` | VARCHAR(255) | UNIQUE | Provider event ID (for deduplication) |
| `payload` | JSONB | NOT NULL | Original webhook or API payload |
| `received_at` | TIMESTAMP WITH TIME ZONE | DEFAULT now() | When received |
| `processed` | BOOLEAN | DEFAULT false | Whether normalization processed it |

---

## Table: `events` (normalized form)

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| `id` | UUID | PK | Event ID |
| `event_raw_id` | UUID | FK → event_raw.id | Source event |
| `user_id` | UUID | FK → users.id | Who generated it |
| `pet_id` | UUID | FK → pets.id | Which pet it affects |
| `type` | VARCHAR(100) | NOT NULL | Normalized event type (e.g. `'commit.push'`, `'goal.completed'`) |
| `value` | FLOAT | DEFAULT 1.0 | Event score weight |
| `meta` | JSONB | DEFAULT '{}'::jsonb | Normalized metadata (repo, filename, etc.) |
| `scored` | BOOLEAN | DEFAULT false | Whether scoring has run |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT now() | Created timestamp |

---

## Table: `goals`

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| `id` | UUID | PK | Goal ID |
| `user_id` | UUID | FK → users.id | Owner |
| `name` | VARCHAR(200) | NOT NULL | Goal title |
| `description` | TEXT |  | Optional description |
| `target_value` | FLOAT | DEFAULT 1.0 | Target amount (e.g. 10 commits/week) |
| `current_value` | FLOAT | DEFAULT 0 | Current progress |
| `unit` | VARCHAR(50) |  | Unit label |
| `is_completed` | BOOLEAN | DEFAULT false | Completion status |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT now() | Created timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT now() | Updated timestamp |

---

## Table: `audit_logs` (optional, for observability)

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| `id` | BIGSERIAL | PK | Log ID |
| `user_id` | UUID | FK → users.id | Actor |
| `action` | VARCHAR(100) | NOT NULL | Action keyword |
| `target_type` | VARCHAR(50) |  | Affected model |
| `target_id` | UUID |  | Affected ID |
| `metadata` | JSONB |  | Optional metadata |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT now() | Time of log |

---

## Table: `metrics_cache` (for fast dashboard access)

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| `key` | VARCHAR(100) | PK | Metric key |
| `value` | FLOAT |  | Cached metric value |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT now() | Last refresh |

---

## Index Recommendations

| Table | Index | Purpose |
|--------|--------|---------|
| `events` | (user_id, created_at DESC) | Fast user event queries |
| `event_raw` | (external_event_id) UNIQUE | Deduplication |
| `pets` | (user_id) | Retrieve all pets for a user |
| `integrations` | (user_id, provider) | Quick lookup for token refresh |
| `goals` | (user_id, is_completed) | Quick goal status lookups |

---

## JSON Schema for `pets.state_json`

```json
{
  "energy": 45,
  "hunger": 12,
  "level": 2,
  "xp": 124,
  "last_event_id": "uuid",
  "last_update": "timestamp",
  "traits": {
    "color": "green",
    "mood": "happy"
  }
}
