---
name: telegram-bot-memory-integration
description: Implement memory/identity features in an existing Telegram bot with LLM integration
source: auto-skill
extracted_at: '2026-06-07T00:00:00.000Z'
---

## When to apply

Adding user memory, identity recognition, or personalized context to an existing Telegram bot that already uses LLM providers for responses, especially when integrating with an existing enrollment form sheet that has 300+ existing records.

## Approach

### 1. Analyze existing codebase first
- Read the main bot entry point to understand handler registration
- Read the LLM integration module to understand provider signatures
- Read the provider implementations (gemini, deepseek, etc.) to check how system prompts are passed
- Read any existing data layer (sheets, db) to understand the schema
- Read the sheet headers via `get_headers()` to map existing columns

### 2. Map to existing sheet columns — don't assume a schema
- Read the actual header row to understand column names (e.g., "What fields are u interested in?" not "Interests")
- Match columns by **header name** (case-insensitive), not by position
- If new columns are needed (Telegram ID, Last Summary, Last Updated), instruct the user to add them as headers — the code should find them by name
- Use the enrollment form's field names as-is for reading; map them to internal names (e.g., form field "What fields are u interested in?" → `interests`)

### 3. Implement 3-tier profile matching (handles wrong usernames)
Users often submit incorrect Telegram usernames in forms. Use a fallback chain:

1. **Telegram ID** — most stable, primary key. Check if the row already has a linked ID.
2. **Telegram username** — match against form-submitted username. Fast but fragile (typos, username changes).
3. **Name** — match the user's Telegram `first_name` against the sheet's Name column. If multiple rows share the same name, return None (ambiguous).

On first successful match via username or name, **auto-link** the Telegram ID by writing it into the sheet. Future lookups will then use the stable ID.

### 4. Create the memory manager
- Build a `MemoryManager` class with: `get_profile()`, `create_profile()`, `update_profile()`, `build_context()`, and fact extraction
- `get_profile(user_id, username, first_name)` implements the 3-tier lookup and auto-linking
- Use a sliding window for short-term chat history (in-memory, per-user)
- Use persistent storage (Google Sheets, database) for long-term memory (name, interests, summaries)
- Provide an `async_update_profile()` method using `run_in_executor` to avoid blocking the polling loop

### 5. Update LLM provider interfaces
- Add an optional `system_prompt` parameter to `BaseLLM.generate(prompt, system_prompt=None)`
- Each provider should use the custom system prompt when provided, fall back to the default constant when None
- This allows injecting dynamic, user-specific context into the system prompt per request

### 6. Create prompt templates
- Define `build_system_prompt(profile, user_context)` that combines:
  - Base personality prompt
  - Memory-aware context instructions (known user vs new user)
  - The user's profile and recent chat history
- Use string templates with clear sections separated by delimiters
- For identity responses (`/knowme`), use **tiered responses**: rich (name+major+interests), standard (name+interests), basic (name only)

### 7. Wire into the AI manager
- Before calling the LLM: fetch profile → build context → build system prompt → combine into full prompt
- Pass `user.first_name` from the Telegram update to `get_profile()` for name-based matching
- After LLM response: record message in history → extract new facts → async update persistent storage
- Handle the "do you know me?" scenario explicitly with a dedicated method

### 8. Register new commands
- Add a `/knowme` command to test identity resolution
- Update handler imports in `main.py`

## Token optimization patterns

| Memory type | Storage | When loaded | Token cost |
|------------|---------|-------------|------------|
| Long-term (name, interests) | Persistent store | Once per message | Only fetched data, not in prompt |
| Short-term (recent chat) | In-memory sliding window | Every message | Last N turns in prompt |
| Context summary | Persistent store + in-memory | When conversation gets long | Compressed string |

## Key design decisions

- **3-tier matching** (ID → username → Name) — handles wrong usernames submitted in enrollment forms
- **Auto-link Telegram ID** on first match — stabilizes future lookups
- **Match by header name, not position** — sheet columns can vary; use case-insensitive header lookup
- **Profile lookup by Telegram ID** (not username) as primary — more stable, usernames can change
- **Fact extraction via heuristic patterns** first ("my name is X", "I love X") — cheaper than an extra LLM call
- **Graceful degradation** — if the persistent store is unavailable, the bot continues chatting without memory updates
- **Separation of concerns** — `MemoryManager` handles data, `prompts.py` handles templates, LLM providers handle generation
- **Async sheet updates** — prevent blocking the polling loop during writes
- **Ambiguous name handling** — if multiple users share the same name, don't guess; return None and wait for ID/username match
