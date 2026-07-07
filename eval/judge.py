import sys, json, re, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.agent.llm import llm_fast

REFUSAL = "do not contain sufficient information"

chunks = {c["id"]: c for c in json.load(open("data/chunks.json"))}
dataset = {d["id"]: d for d in json.load(open("data/eval/qa_dataset.json"))}
results = json.load(open("eval/results/run_full.json"))

FAITH_PROMPT = """You are checking whether an answer is faithful to its source excerpts.

Source excerpts:
{context}

Answer to check:
{answer}

Does the answer contain any factual claim that is NOT supported by the excerpts?
Ignore statements attributed to a "defect detection model" and generic advice to verify on site.
Reply with exactly one word: faithful or unfaithful."""

rows = []
for r in results:
    if r.get("error"):
        rows.append({"id": r["id"], "type": r["type"], "status": "ERROR"})
        continue
    item = dataset[r["id"]]
    refused = REFUSAL in r["answer"]

    # retrieval hit: any expected section among kept sections
    if item["expected_sections"]:
        hit = any(s in r["kept_sections"] for s in item["expected_sections"])
    else:
        hit = None  # not applicable

    # refusal correctness
    refusal_ok = (not item["answerable"] and refused) or (item["answerable"] and not refused)

    # citation validity: every cited section must be among kept sections
    cited = set(re.findall(r"\[§\s*([\w-]+)", r["answer"]))
    cited_base = {c.split()[0] for c in cited}
    kept_base = {s for s in r["kept_sections"]}
    citation_ok = cited_base.issubset(kept_base) if cited_base else None

    # faithfulness via LLM judge (only for non-refusals)
    faithful = None
    if not refused and r["kept_ids"]:
        ctx = "\n\n".join(chunks[cid]["text"][:3000] for cid in r["kept_ids"][:5] if cid in chunks)
        verdict = llm_fast.invoke(FAITH_PROMPT.format(context=ctx, answer=r["answer"])).content.strip().lower()
        faithful = verdict.startswith("faithful")
        time.sleep(2)

    rows.append({"id": r["id"], "type": r["type"], "status": "ok",
                 "retrieval_hit": hit, "refusal_ok": refusal_ok,
                 "citation_ok": citation_ok, "faithful": faithful,
                 "rewrites": r["rewrites"], "latency_s": r["latency_s"]})
    print(rows[-1])

def rate(key, subset):
    vals = [x[key] for x in subset if x.get(key) is not None and x["status"] == "ok"]
    return f"{sum(vals)}/{len(vals)}" if vals else "n/a"

print("\n===== SUMMARY =====")
for t in ["text", "image", "unanswerable"]:
    sub = [x for x in rows if x["type"] == t]
    print(f"{t:14s} retrieval={rate('retrieval_hit', sub):7s} refusal_ok={rate('refusal_ok', sub):7s} "
          f"citations={rate('citation_ok', sub):7s} faithful={rate('faithful', sub)}")
all_ok = [x for x in rows if x["status"] == "ok"]
print(f"{'ALL':14s} retrieval={rate('retrieval_hit', all_ok):7s} refusal_ok={rate('refusal_ok', all_ok):7s} "
      f"citations={rate('citation_ok', all_ok):7s} faithful={rate('faithful', all_ok)}")

json.dump(rows, open("eval/results/judged.json", "w"), indent=2)