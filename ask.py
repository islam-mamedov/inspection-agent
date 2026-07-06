import argparse
from src.agent.graph import build_graph

parser = argparse.ArgumentParser()
parser.add_argument("question")
parser.add_argument("--image", default="")
args = parser.parse_args()

app = build_graph()
state = {
    "question": args.question, "queries": [args.question],
    "image_path": args.image, "defect_findings": {},
    "retrieved": [], "relevant": [], "rewrite_count": 0, "answer": "",
}

print(f"Q: {args.question}" + (f"  [image: {args.image}]" if args.image else ""))
print("=" * 70)
for step in app.stream(state):
    for node_name, update in step.items():
        if node_name == "analyze_image":
            f = update["defect_findings"]
            print(f"[vision] {f['defects_found']} defects: "
                  f"{[(d['defect_type'], d['severity']) for d in f['findings']]}")
        elif node_name == "plan_queries":
            print(f"[plan] queries: {update['queries']}")
        elif node_name == "retrieve":
            print(f"[retrieve] got {len(update['retrieved'])} chunks")
        elif node_name == "grade":
            print(f"[grade] kept {len(update['relevant'])}")
        elif node_name == "rewrite":
            print(f"[rewrite] new queries: {update['queries']}")
        elif node_name == "generate":
            print("=" * 70 + "\n" + update["answer"])