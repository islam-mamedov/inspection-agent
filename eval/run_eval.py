import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json, time
from src.agent.graph import build_graph

dataset = json.load(open(sys.argv[2] if len(sys.argv) > 2 else "data/eval/qa_dataset.json"))
app = build_graph()
results = []

for item in dataset:
    state = {
        "question": item["question"], "queries": [item["question"]],
        "image_path": item.get("image_path", ""), "defect_findings": {},
        "retrieved": [], "relevant": [], "rewrite_count": 0, "answer": "",
    }
    t0 = time.time()
    try:
        final = app.invoke(state)
        results.append({
            "id": item["id"], "type": item["type"], "question": item["question"],
            "answer": final["answer"],
            "kept_sections": sorted({c["meta"]["section"] for c in final["relevant"]}),
            "kept_ids": [c["id"] for c in final["relevant"]],
            "rewrites": final["rewrite_count"],
            "latency_s": round(time.time() - t0, 1),
            "error": None,
        })
        print(f"[{item['id']}] ok ({results[-1]['latency_s']}s, {final['rewrite_count']} rewrites)")
    except Exception as e:
        results.append({"id": item["id"], "type": item["type"],
                        "question": item["question"], "answer": "", "kept_sections": [],
                        "kept_ids": [], "rewrites": 0, "latency_s": 0, "error": str(e)})
        print(f"[{item['id']}] ERROR: {e}")
    time.sleep(6)  # respect Groq's tokens-per-minute cap

Path("eval/results").mkdir(exist_ok=True)
out = sys.argv[1] if len(sys.argv) > 1 else "eval/results/run_full.json"
json.dump(results, open(out, "w"), indent=2)
print(f"\nSaved {len(results)} results to {out}")