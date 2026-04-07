<img width="1707" height="1148" alt="Screenshot 2026-04-06 at 7 49 20 PM" src="https://github.com/user-attachments/assets/1f840071-01bf-443a-8e00-19924a0d8ae8" />



# Apex CRM Sales Intelligence

A RAG-powered sales intelligence assistant built with LangChain and Claude. It answers competitive questions by searching internal battlecards and playbooks, live web data, or both — depending on what the question needs.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-claude--opus--4-orange?style=flat)
![LangChain](https://img.shields.io/badge/LangChain-121212?style=flat)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-0B0D0E?style=flat&logo=railway&logoColor=white)

## Features

- **Hybrid retrieval** — combines a local vector knowledge base (battlecards, playbooks, win/loss reports) with live Tavily web search
- **ReAct agent** — uses Claude to reason step-by-step and pick the right tool(s) for each query
- **LLM-as-judge evals** — built-in eval suite that scores agent answers on relevance, groundedness, and completeness
- **Glassmorphism UI** — clean Streamlit interface with quick-action buttons for common queries
- **Password auth** — simple password gate to protect the demo
- **Demo guardrails** — rate limiting capped at 20 questions per session

## Stack

| Component | Tool |
|---|---|
| LLM | Claude (claude-opus-4-5) via `langchain-anthropic` |
| Embeddings | Voyage AI (`voyage-3`) |
| Vector store | ChromaDB (persistent, local) |
| Web search | Tavily |
| Agent framework | LangChain ReAct |
| UI | Streamlit |
| Deployment | Docker + Railway |

## Setup

### Local development

**1. Clone and install dependencies**

```bash
git clone https://github.com/kcarroll88/sales-intel.git
cd sales-intel
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Configure environment variables**

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_anthropic_api_key
VOYAGE_API_KEY=your_voyage_api_key
TAVILY_API_KEY=your_tavily_api_key
APP_PASSWORD=your_app_password   # optional, defaults to apex2026
```

**3. Add your documents**

Place PDF files (battlecards, playbooks, win/loss reports, etc.) in the `docs/` folder. They will be automatically indexed into ChromaDB on first run.

**4. Run the app**

```bash
streamlit run app.py
```

### Docker

```bash
docker build -t sales-intel .
docker run -p 8501:8501 --env-file .env sales-intel
```

### Deploy to Railway

1. Push the repo to GitHub.
2. Create a new Railway project and connect your repo.
3. Add the environment variables (`ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, `TAVILY_API_KEY`, `APP_PASSWORD`) in the Railway dashboard.
4. Railway will detect the `Dockerfile` and build automatically. The `$PORT` variable is handled in the `CMD`.

## Project Structure

```
sales-intel/
├── app.py            # Streamlit UI + auth + rate limiting
├── agent.py          # Document indexing, tools, and ReAct agent
├── evals.py          # LLM-as-judge eval suite
├── Dockerfile
├── requirements.txt
├── docs/             # PDF knowledge base (battlecards, playbooks, etc.)
└── chroma_db/        # Persistent vector store (auto-generated, gitignored)
```

## Evals

The eval suite (`evals.py`) runs 4 test cases covering competitive strategy, live news retrieval, internal metrics, and out-of-scope questions. Each answer is scored by Claude on three dimensions:

- **Relevance** — does it address the question?
- **Groundedness** — is it based on retrieved sources, not hallucination?
- **Completeness** — does it cover the key points?

A test passes if the average score across all three dimensions is ≥ 3.5/5. You can also trigger evals directly from the sidebar in the UI.
