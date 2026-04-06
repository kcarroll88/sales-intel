from dotenv import load_dotenv
load_dotenv()

print("1. Testing imports...")
from agent import index_documents, build_agent
print("2. Imports done")

print("3. Testing index_documents...")
index_documents()
print("4. Index done")

print("5. Testing build_agent...")
agent = build_agent()
print("6. Agent built")