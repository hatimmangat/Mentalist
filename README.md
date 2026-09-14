

https://github.com/user-attachments/assets/5bad35ed-2724-4933-bfb6-1ab77b15f311






## 🚀 Getting Started

### Prerequisites
- Python 3.11+ (works on 3.13 too)
- A free Groq API key from [console.groq.com](https://console.groq.com) — no card required
- A modern browser

### Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

Open `.env` and set:
- `GROQ_API_KEY` — your free key from console.groq.com
- `GROQ_MODEL` — a current chat model your key has access to (check `console.groq.com/docs/models`; model availability changes over time)
- `JWT_SECRET_KEY` — generate one with `python -c "import secrets; print(secrets.token_hex(32))"`

### Build the index and run

```bash
python -m app.rag.ingest      # chunks + embeds the corpus into ChromaDB
uvicorn app.main:app --reload
```

Then open `frontend/index.html` in a browser — it's pre-configured to talk to `http://127.0.0.1:8000`.

## 💻 Usage

1. Sign up with any email and an 8+ character password.
2. Talk to Jane — she'll respond with real retrieved context, visible as small source tags under each reply.
3. Click **Generate Session Report** at any point to get a freshly written summary of the conversation so far — themes discussed, tone shifts, and gentle next steps.

## 🧩 How the RAG Pipeline Works

1. **Chunking** — each corpus document is split by its `##` section headers, then any long section is further packed into ~900-character pieces along sentence boundaries with overlap, so context never gets cut mid-sentence.
2. **Embedding** — every chunk is embedded locally using `all-MiniLM-L6-v2`, no API call involved.
3. **Storage** — vectors and their source metadata are stored in a persistent ChromaDB collection.
4. **Retrieval** — an incoming message is embedded the same way and matched by cosine similarity against the corpus; a similarity floor filters out weak matches.
5. **Crisis override** — if crisis language is detected, relevant support resources are force-injected into context regardless of what retrieval returns.
6. **Generation** — the retrieved context, conversation history, and system prompt are sent to an open-weight model via Groq for the actual reply.

## 📚 The Corpus

17 original documents, written by me, sitting in `backend/app/rag/corpus/` in plain markdown — fully readable, nothing hidden or fetched at runtime. They cover generalized anxiety, panic disorder, social anxiety, major depression, PTSD/trauma, grief, CBT, DBT, mindfulness, stress management, sleep, anger, self-esteem, relationships/attachment, substance use, active listening, and a dedicated crisis-response protocol. They chunk down to 80 retrievable pieces.

To extend it: add another `.md` file following the same `# Title` / `## Section` structure, then re-run `python -m app.rag.ingest`.

## ⚠️ Known Limitations

This is a genuine, working system — but it also has the honest limits of a free-tier, self-built project, and I'd rather say that plainly than oversell it:

- Not a licensed therapist and does not diagnose — it's a supportive listening tool, explicitly framed that way in Jane's system prompt.
- Corpus is a solid starting set (17 documents, 80 chunks), not an exhaustive clinical reference.
- Free-tier hosting (where deployed) may cold-start after inactivity.
- Crisis detection is regex-based — deliberately biased toward over-triggering, but not a substitute for real crisis intervention infrastructure.
- Helpline numbers referenced in the crisis protocol should be periodically verified against the organizations' own pages, since they can change.
- Single SQLite file for storage — fine for a portfolio/demo scale, not yet built for concurrent high-volume production use.

## 🗺️ Roadmap

- [ ] Swap SQLite for Postgres for real concurrent-user scale
- [ ] Add conversation memory summarization for very long sessions
- [ ] Expand the corpus beyond the initial 17 documents
- [ ] Add password reset flow
- [ ] Rate limiting on the chat endpoint
- [ ] Optional voice input/output

---

Made by **Hatim**
