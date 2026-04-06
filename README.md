# Apex CRM Sales Intelligence

A RAG-powered sales intelligence assistant built with LangChain and Claude. It answers competitive questions by searching internal battlecards and playbooks, live web data, or both — depending on what the question needs.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-claude--opus--4-orange?style=flat)
![LangChain](https://img.shields.io/badge/LangChain-121212?style=flat)

## Features

- **Hybrid retrieval** — combines a local vector knowledge base (battlecards, playbooks, win/loss reports) with live Tavily web search
- **ReAct agent** — uses Claude to reason step-by-step and pick the right tool(s) for each query
- **LLM-as-judge evals** — built-in eval suite that scores agent answers on relevance, groundedness, and completeness
- **Glassmorphism UI** — clean Streamlit interface with quick-action buttons for common queries

## Stack

| Component | Tool |
|---|---|
| LLM | Claude (claude-opus-4-5) via `langchain-anthropic` |
| Embeddings | Voyage AI (`voyage-3`) |
| Vector store | ChromaDB (persistent, local) |
| Web search | Tavily |
| Agent framework | LangChain ReAct |
| UI | Streamlit |

## Setup

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
```

**3. Add your documents**

Place PDF files (battlecards, playbooks, win/loss reports, etc.) in the `docs/` folder. They will be automatically indexed into ChromaDB on first run.

**4. Run the app**

```bash
streamlit run app.py
```

## Project Structure

```
sales-intel/
├── app.py            # Streamlit UI
├── agent.py          # Document indexing, tools, and ReAct agent
├── evals.py          # LLM-as-judge eval suite
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
