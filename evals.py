import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import anthropic
from agent import search_knowledge_base, search_web

load_dotenv()

client = anthropic.Anthropic()

# ── LLM AS JUDGE ─────────────────────────────────────────────────────────────
def evaluate_answer(question: str, answer: str, context: str = "") -> dict:
    """Use Claude to evaluate the quality of an agent answer."""
    
    context_section = f"Source Documents Retrieved:\n{context}\n\n" if context else ""

    prompt = (
        "You are an expert evaluator for AI agent responses. \n"
        "Evaluate the following answer based on three criteria.\n\n"
        f"Question: {question}\n\n"
        f"Answer: {answer}\n\n"
        + context_section +
        "Score the answer on each criterion from 1-5:\n\n"
        "1. RELEVANCE (1-5): Does the answer directly address the question asked?\n"
        "   1 = Completely off topic\n"
        "   3 = Partially addresses the question\n"
        "   5 = Directly and fully addresses the question\n\n"
        "2. GROUNDEDNESS (1-5): Is the answer based on the source documents provided above?\n"
        "   1 = Contradicts or ignores the sources\n"
        "   3 = Partially uses the sources\n"
        "   5 = Fully grounded in the provided sources\n\n"
        "3. COMPLETENESS (1-5): Does the answer cover the key points needed to fully answer the question?\n"
        "   1 = Missing most key information\n"
        "   3 = Covers some key points\n"
        "   5 = Comprehensive and complete\n\n"
        "Respond in this exact format:\n"
        "RELEVANCE: [score]\n"
        "GROUNDEDNESS: [score]\n"
        "COMPLETENESS: [score]\n"
        "REASONING: [one sentence explaining the scores]\n"
        "OVERALL: [PASS if average >= 3.5, FAIL if average < 3.5]"
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
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
            "description": "Out of scope — should gracefully handle irrelevant question",
            "out_of_scope": True
        }
    ]

    def run_single_eval(args):
        i, test = args
        answer = agent_executor(test["input"])

        if test.get("out_of_scope"):
            refused = any(phrase in answer.lower() for phrase in [
                "focused on sales", "can't help with", "outside",
                "not able to", "sales intelligence"
            ])
            scores = {
                "relevance": 5 if refused else 1,
                "groundedness": 5,
                "completeness": 5 if refused else 1,
                "average": 5.0 if refused else 1.0,
                "reasoning": "Agent correctly refused out-of-scope question" if refused else "Agent should have refused",
                "passed": refused
            }
            return i, test, scores

        web_search_keywords = ["news", "recent", "announced", "latest", "2026"]
        is_web_question = any(word in test["input"].lower() for word in web_search_keywords)

        if is_web_question:
            context = search_web(test["input"])  # pass actual web results as context
        else:
            context = search_knowledge_base(test["input"])

        scores = evaluate_answer(test["input"], answer, context)
        return i, test, scores

    results_map = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(run_single_eval, (i, test)): i for i, test in enumerate(test_cases)}
        for future in as_completed(futures):
            i, test, scores = future.result()
            results_map[i] = (test, scores)

    results = []
    for i in range(len(test_cases)):
        test, scores = results_map[i]
        print(f"\nEval {i+1}: {test['description']}")
        print(f"Q: {test['input']}")
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