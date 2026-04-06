import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()

# ── LLM AS JUDGE ─────────────────────────────────────────────────────────────
def evaluate_answer(question: str, answer: str, context: str = "") -> dict:
    """Use Claude to evaluate the quality of an agent answer."""
    
    prompt = f"""You are an expert evaluator for AI agent responses. 
Evaluate the following answer based on three criteria.

Question: {question}

Answer: {answer}

{f"Context/Sources Used: {context}" if context else ""}

Score the answer on each criterion from 1-5:

1. RELEVANCE (1-5): Does the answer directly address the question asked?
   1 = Completely off topic
   3 = Partially addresses the question  
   5 = Directly and fully addresses the question

2. GROUNDEDNESS (1-5): Is the answer based on actual retrieved information rather than hallucination?
   1 = Completely fabricated
   3 = Mix of retrieved and assumed information
   5 = Fully grounded in retrieved sources

3. COMPLETENESS (1-5): Does the answer cover the key points needed to fully answer the question?
   1 = Missing most key information
   3 = Covers some key points
   5 = Comprehensive and complete

Respond in this exact format:
RELEVANCE: [score]
GROUNDEDNESS: [score]
COMPLETENESS: [score]
REASONING: [one sentence explaining the scores]
OVERALL: [PASS if average >= 3.5, FAIL if average < 3.5]"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    
    result = response.content[0].text
    lines = result.strip().split("\n")
    
    scores = {}
    for line in lines:
        if line.startswith("RELEVANCE:"):
            scores["relevance"] = int(line.split(":")[1].strip())
        elif line.startswith("GROUNDEDNESS:"):
            scores["groundedness"] = int(line.split(":")[1].strip())
        elif line.startswith("COMPLETENESS:"):
            scores["completeness"] = int(line.split(":")[1].strip())
        elif line.startswith("REASONING:"):
            scores["reasoning"] = line.split(":", 1)[1].strip()
        elif line.startswith("OVERALL:"):
            scores["passed"] = "PASS" in line

    scores["average"] = round(
        (scores.get("relevance", 0) + 
         scores.get("groundedness", 0) + 
         scores.get("completeness", 0)) / 3, 2
    )
    
    return scores

# ── EVAL SUITE ────────────────────────────────────────────────────────────────
def run_evals(agent_executor):
    print("\n" + "="*60)
    print("RUNNING LLM-AS-JUDGE EVALS")
    print("="*60)

    test_cases = [
        {
            "input": "How do we beat Salesforce in a deal?",
            "description": "Competitive strategy — should use internal battlecards"
        },
        {
            "input": "What has HubSpot announced recently in 2026?",
            "description": "Current news — should use web search"
        },
        {
            "input": "What is our win rate and what are the top reasons we lose deals?",
            "description": "Internal metrics — should use win/loss analysis"
        },
        {
            "input": "What is the weather like today?",
            "description": "Out of scope — should gracefully handle irrelevant question"
        }
    ]

    results = []
    for i, test in enumerate(test_cases):
        print(f"\nEval {i+1}: {test['description']}")
        print(f"Q: {test['input']}")
        
        result = agent_executor.invoke({"input": test["input"]})
        answer = result["output"]
        
        scores = evaluate_answer(
            question=test["input"],
            answer=answer
        )
        
        results.append(scores["passed"])
        
        print(f"Relevance:     {scores.get('relevance')}/5")
        print(f"Groundedness:  {scores.get('groundedness')}/5")
        print(f"Completeness:  {scores.get('completeness')}/5")
        print(f"Average:       {scores.get('average')}/5")
        print(f"Reasoning:     {scores.get('reasoning')}")
        print(f"Result:        {'✅ PASS' if scores['passed'] else '❌ FAIL'}")

    score = sum(results) / len(results)
    print(f"\n{'='*60}")
    print(f"EVAL SUMMARY: {score:.0%} ({sum(results)}/{len(results)} passed)")
    print(f"{'='*60}")
    return score