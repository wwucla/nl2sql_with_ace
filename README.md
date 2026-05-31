# nl2sql_with_ace

A tiny, runnable demo of **ACE — Agentic Context Engineering** applied to
**natural-language → SQL**.

Instead of fine-tuning a model, ACE *evolves the context*: it grows a
**playbook** of reusable strategies from its own successes and failures. The
loop has three roles:

- **Generator** — turns a question + the current playbook into SQL.
- **Reflector** — when an answer is wrong, diagnoses *why* and writes a general
  lesson.
- **Curator** — appends that lesson to the playbook as a small *delta* (never
  rewrites the whole thing — that's what avoids "context collapse").

The reward signal is free and automatic: run the generated SQL against a SQLite
database and compare the rows to the gold answer.

```
question ─▶ Generator ─▶ SQL ─▶ execute ─▶ compare to gold
                ▲                              │
            playbook ◀── Curator ◀── Reflector ◀ (on failure)
```

## 1. Get a free Gemini API key

The default provider is Google Gemini, which has a **free API tier** (great for
burning tokens while you iterate):

1. Go to **https://aistudio.google.com/**
2. Sign in with a Google account.
3. Click **"Get API key"** (left sidebar) → **"Create API key"**.
4. Pick/create a Google Cloud project when prompted. No billing needed for the
   free tier.
5. Copy the key.

Notes:
- The free tier has **rate limits** (requests/minute and /day) and **may use
  your prompts to improve Google's products** — fine for this demo's public
  sample data, but don't point it at anything private.
- Check current free-tier limits and model names on the AI Studio pricing page;
  they change over time.

## 2. Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste your key into GEMINI_API_KEY=
```

## 3. Run

```bash
# Run the ACE loop: attempt every task, learn from failures, grow the playbook.
python run.py train

# Ask a one-off question using the current (learned) playbook.
python run.py ask "What is the total revenue from completed orders?"

# Score the current playbook without learning.
python run.py eval
```

`train` prints accuracy per epoch and the playbook size — watch it climb as the
playbook fills with lessons. The learned playbook is saved to `playbook.json`
(gitignored).

## Switching providers

Everything goes through one function, `ace/llm.py::complete()`. To use Sonnet or
GPT instead of Gemini, just change two env vars in `.env`:

```
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=...
```

(and `pip install anthropic` or `openai`). The ACE logic never changes.

## Security / cost notes

- **Never commit your key.** `.env` is gitignored; only `.env.example` (no
  values) is tracked. If a key ever lands in a commit, treat it as compromised
  and **rotate it** — deleting the line later doesn't remove it from git history.
- Set a **spending cap** in your provider console as a backstop.
- The Gemini free tier keeps this demo at **$0** within its rate limits.

## Layout

```
ace/
  llm.py        # provider-agnostic LLM wrapper (one swappable function)
  playbook.py   # the evolving playbook: append-only delta updates + persistence
  roles.py      # Generator / Reflector / Curator
  db.py         # SQLite executor + the automatic grader (reward signal)
  loop.py       # the ACE train/eval loop
data/
  schema.sql    # sample e-commerce schema
  seed.sql      # sample rows
  tasks.jsonl   # NL question + gold SQL pairs
run.py          # CLI entrypoint
```
