# Mentalist

I built Mentalist because I wanted something I could genuinely call my own — not just a chat window wired up to someone else's API, but an actual retrieval-augmented system with a real backend, real authentication, and a knowledge base I put together myself.

Mentalist is a supportive listening companion. You talk to **Jane**, and behind the scenes, your message gets checked against a vector database of psychology reference material I wrote and chunked myself, and the most relevant pieces of that material get pulled into context before Jane responds. It's not just an LLM improvising — it's actually retrieving from something real before it answers.

## Why I built it this way

I didn't want to just call an AI API and dress it up in a nice UI. I wanted to understand and build every layer:

- **The knowledge base is mine.** 17 documents I wrote myself, covering anxiety, depression, PTSD, grief, CBT, DBT, mindfulness, relationships, substance use, and a proper crisis-response protocol. It's sitting right in this repo at `backend/app/rag/corpus/` — nothing hidden, nothing fetched from somewhere else at runtime. You can open any of those `.md` files and read exactly what Jane draws from.
- **The retrieval is real.** I chunk each document by its section headers, embed every chunk locally using a sentence-transformer model (no API call, no cost), and store the vectors in ChromaDB. When you send a message, it gets embedded the same way and matched by cosine similarity against everything in that store.
- **The generation is free, on purpose.** Jane's actual replies come from Llama 3.3 70B through Groq's free tier. No credit card, no billing, and no chance of the whole thing dying mid-demo because a free trial expired.
- **The backend is real.** FastAPI, with actual bcrypt-hashed passwords and JWT tokens — not `localStorage` pretending to be an account system.
- **Every session can end with a real report.** After you're done talking to Jane, you can generate a written summary of what was actually discussed — the themes that came up, how the tone shifted, and a couple of gentle next steps. It's generated fresh from the transcript every time, not a template.

## What's in the repo

```
mentalist/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entrypoint
│   │   ├── auth.py               # JWT + bcrypt auth
│   │   ├── database.py           # SQLAlchemy setup
│   │   ├── models.py             # User, ChatSession, Message
│   │   ├── schemas.py            # request/response models
│   │   ├── crisis.py             # crisis keyword detection + Pakistan helpline resources
│   │   ├── rag/
│   │   │   ├── chunker.py        # splits the corpus into retrievable chunks
│   │   │   ├── embeddings.py     # local sentence-transformer embeddings
│   │   │   ├── vectorstore.py    # ChromaDB wrapper
│   │   │   ├── retriever.py      # similarity search + context formatting
│   │   │   ├── ingest.py         # builds the vector index from the corpus
│   │   │   └── corpus/           # the 17 source documents — the actual data
│   │   ├── llm/
│   │   │   └── groq_client.py    # generation via Groq's free tier
│   │   └── routers/
│   │       ├── auth_router.py    # /auth/signup, /auth/login, /auth/me
│   │       └── chat_router.py    # /chat, /chat/sessions, session reports
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── render.yaml
│   └── .env.example
├── frontend/
│   ├── index.html                # the whole UI, talks to the real backend
│   └── assets/images/            # the visuals used throughout the app
└── README.md
```

## The corpus — yes, it's included

I know a lot of "RAG projects" quietly leave out the actual data. I didn't want to do that. Every document Jane retrieves from is sitting in `backend/app/rag/corpus/` in this repo, in plain markdown, fully readable. It chunks down to 80 pieces of retrievable content once you run the ingest script. If you want to extend it, drop another `.md` file in that folder following the same `# Title` / `## Section` structure and re-run:

```bash
python -m app.rag.ingest
```

## Running it locally

```bash
cd backend
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt

cp .env.example .env
# open .env and paste in your free Groq key from console.groq.com

python -m app.rag.ingest        # builds the vector index
uvicorn app.main:app --reload
```

Then open `frontend/index.html` in a browser. It's set to talk to `http://127.0.0.1:8000` by default, which matches local dev.

## Deploying for free

**Backend → Render.com.** Push this repo to GitHub, then in Render pick "New +" → "Blueprint" and point it at the repo — it reads `render.yaml` automatically. Set `GROQ_API_KEY` in Render's dashboard once. It builds the vector index during the Docker build, so it's ready the moment the service starts.

**Frontend → Vercel or Netlify.** Deploy the `frontend/` folder as a static site, and update `API_BASE_URL` near the top of `index.html`'s script tag to point at your Render URL.

One honest thing worth knowing: Render's free tier spins the backend down after inactivity, so the first request after a while takes 30-60 seconds to wake it back up. It won't ever bill you or hard-fail — it just needs a moment. Worth mentioning that up front if you're demoing it live.

## A note on the crisis protocol

If Jane detects language suggesting someone might be in crisis, she surfaces real support resources rather than trying to handle it alone. I've set this up with Pakistan-based resources — Umang Pakistan's helpline and Rozan's counselling line — since that's who this is actually for. Helpline numbers do change over time, so if you're relying on this for anything real, it's worth double-checking them against the organizations' own pages before you lean on them.

## Everything here is real, and I know where each piece could break

I'd rather say this plainly than pretend it's flawless: this is a genuine, working RAG system, not a shell around an API call. But it also has the honest limits of a free-tier, self-built project — Render's cold starts, Groq's rate limits if you hammer it, and a corpus that's a solid starting set rather than an exhaustive clinical reference. I built it to be something I can explain end to end, not something I'm pretending is bigger than it is.

— Hatim
