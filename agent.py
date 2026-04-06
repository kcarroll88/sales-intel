import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from tavily import TavilyClient
import chromadb
import voyageai

load_dotenv()

# ── CLIENTS ───────────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

voyage_client = voyageai.Client()
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
chroma_client = chromadb.PersistentClient(
    path=os.path.join(_BASE_DIR, "chroma_db"),
    settings=chromadb.Settings(anonymized_telemetry=False)
)
collection = chroma_client.get_or_create_collection(name="sales_intel")
llm = ChatAnthropic(model="claude-opus-4-5", max_tokens=1000)

# ── 1. LOAD + INDEX ───────────────────────────────────────────────────────────
def index_documents(folder_path=None):
    if folder_path is None:
        folder_path = os.path.join(_BASE_DIR, "docs")
    if collection.count() > 0:
        print(f"Knowledge base ready with {collection.count()} chunks")
        return

    docs = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(folder_path, filename))
            pages = loader.load()
            docs.extend(pages)
            print(f"Loaded: {filename}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    texts = [c.page_content for c in chunks]
    sources = [c.metadata.get("source", "unknown") for c in chunks]

    batch_size = 50
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        batch_sources = sources[i:i+batch_size]
        batch_ids = [f"chunk_{i+j}" for j in range(len(batch_texts))]
        response = voyage_client.embed(batch_texts, model="voyage-3")
        collection.add(
            documents=batch_texts,
            embeddings=response.embeddings,
            metadatas=[{"source": s} for s in batch_sources],
            ids=batch_ids
        )
    print(f"Indexed {len(chunks)} chunks")

# ── 2. TOOLS ──────────────────────────────────────────────────────────────────
def search_knowledge_base(query: str) -> str:
    """Search internal sales documents, battlecards and playbooks."""
    query_embedding = voyage_client.embed([query], model="voyage-3").embeddings[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=3)

    if not results["documents"][0]:
        return "No relevant information found in the knowledge base."

    output = ""
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        source = os.path.basename(meta["source"])
        output += f"[Source: {source}]\n{doc}\n\n"
    return output

def search_web(query: str) -> str:
    """Search the web for current competitor news and market intelligence."""
    response = tavily_client.search(query, max_results=3)
    results = response.get("results", [])
    if not results:
        return "No results found."
    output = ""
    for r in results:
        output += f"Title: {r['title']}\n{r['content']}\n\n"
    return output

tools = [
    Tool(
        name="SalesKnowledgeBase",
        func=search_knowledge_base,
        description="""Search internal sales documents including battlecards, 
        playbooks, positioning guides, and win/loss analysis. Use this for 
        questions about our product, competitors, objection handling, pricing, 
        and sales strategy."""
    ),
    Tool(
        name="WebSearch",
        func=search_web,
        description="""Search the web for current competitor news, recent 
        product announcements, pricing changes, and market intelligence. 
        Always include the current year 2026 in queries for recent news."""
    )
]

# ── 3. AGENT ──────────────────────────────────────────────────────────────────
def build_agent():
    template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

    prompt = PromptTemplate.from_template(template)
    agent = create_react_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True
    )

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from evals import run_evals
    index_documents()
    agent_executor = build_agent()

    # test question
    print("\n" + "="*60)
    print("Q: How do we beat Salesforce in a competitive deal?")
    print("="*60)
    result = agent_executor.invoke({
        "input": "How do we beat Salesforce in a competitive deal?"
    })
    print(f"\nFinal Answer: {result['output']}")

    # run evals
    run_evals(agent_executor)