import chromadb
from src.agent.state import AgentState
from src.agent.llm import llm_fast, llm_main
from src.tools.defect_detector import detect_defects

client = chromadb.PersistentClient(path="data/chroma")
collection = client.get_collection("standards")

TOP_K = 6


def retrieve(state: AgentState) -> dict:
    """Search the vector store with the current queries."""
    seen, results = set(), []
    for q in state["queries"]:
        res = collection.query(query_texts=[q], n_results=TOP_K)
        for id_, text, meta in zip(res["ids"][0], res["documents"][0], res["metadatas"][0]):
            if id_ not in seen:
                seen.add(id_)
                results.append({"id": id_, "text": text, "meta": meta})
    return {"retrieved": results}

GRADE_PROMPT = """You are grading whether a document chunk is relevant to a question.

Question: {question}

Chunk:
{chunk}

Does this chunk contain information that helps answer the question?
Answer with exactly one word: yes or no."""


def grade(state: AgentState) -> dict:
    """Keep only chunks the LLM judges relevant."""
    relevant = []
    for chunk in state["retrieved"]:
        verdict = llm_fast.invoke(
            GRADE_PROMPT.format(question=state["question"], chunk=chunk["text"][:2000])
        ).content.strip().lower()
        if verdict.startswith("yes"):
            relevant.append(chunk)
    return {"relevant": relevant}

REWRITE_PROMPT = """A search over a concrete repair manual (EM 1110-2-2002) failed to find good results.

Original question: {question}
Queries already tried: {queries}

Write 2 NEW search queries using different technical vocabulary that an engineering
manual would use (think: synonyms, causes, mechanisms, related repair methods).
Return exactly 2 queries, one per line, nothing else."""


def rewrite(state: AgentState) -> dict:
    """Generate alternative queries when retrieval was weak."""
    out = llm_fast.invoke(REWRITE_PROMPT.format(
        question=state["question"], queries=state["queries"]
    )).content.strip()
    new_queries = [q.strip("-• ").strip() for q in out.splitlines() if q.strip()][:2]
    return {
        "queries": new_queries,
        "rewrite_count": state["rewrite_count"] + 1,
    }

GENERATE_PROMPT = """You are an assistant for concrete structure inspection, answering
STRICTLY from the provided excerpts of EM 1110-2-2002.

{findings_block}Question: {question}

Excerpts:
{context}

Rules:
1. Answer using ONLY information from the excerpts above.
2. If defect detection findings are present, structure your answer as an inspection report:
   (a) state what the detection model found;
   (b) present the manual's guidance for those defect types — if the repair choice depends
       on conditions the model cannot determine (e.g. active vs dormant crack, pattern vs
       isolated, water condition), present the options CONDITIONALLY ("If the cracks are
       dormant and isolated with no water present, the manual recommends...");
   (c) end with a short "Field verification needed" list of the conditions an inspector
       must determine on site to finalize the repair selection.
   Missing classification info is NOT a reason to refuse when the manual's decision
   framework itself can be presented.
3. After every factual claim from the excerpts, cite the section in brackets, e.g. [§3-2].
4. Refer to detection results as "the defect detection model found..." - these come
   from a computer vision model, not the manual.
5. If the excerpts do not contain enough information, say exactly:
   "The available documents do not contain sufficient information to answer this."

Answer:"""


def generate(state: AgentState) -> dict:
    if not state["relevant"]:
        return {"answer": "The available documents do not contain sufficient information to answer this."}
    findings_block = ""
    if state["defect_findings"] and state["defect_findings"].get("defects_found", 0) > 0:
        import json as _json
        findings_block = f"Defect detection model findings for the uploaded image:\n{_json.dumps(state['defect_findings']['findings'], indent=2)}\n\n"
    context = "\n\n---\n\n".join(c["text"] for c in state["relevant"])
    answer = llm_main.invoke(GENERATE_PROMPT.format(
        findings_block=findings_block, question=state["question"], context=context
    )).content
    return {"answer": answer}

def analyze_image(state: AgentState) -> dict:
    """Run the trained CV model on the uploaded image."""
    findings = detect_defects(state["image_path"])
    return {"defect_findings": findings}


def plan_queries(state: AgentState) -> dict:
    """Turn CV findings + question into targeted search queries."""
    f = state["defect_findings"]
    if not f or f["defects_found"] == 0:
        return {"queries": [state["question"]]}

    # summarize findings: {"crack": "medium", "spalling": "high"} style
    worst = {}
    rank = {"low": 0, "medium": 1, "high": 2}
    for d in f["findings"]:
        t = d["defect_type"]
        if t not in worst or rank[d["severity"]] > rank[worst[t]]:
            worst[t] = d["severity"]

    queries = [state["question"]]
    for defect, sev in worst.items():
        queries.append(f"{defect} in concrete causes evaluation repair methods")
        queries.append(f"repair method selection for {defect} {sev} severity")
    return {"queries": queries[:5]}