# Agentic Multimodal Inspection Intelligence

One-paragraph pitch: what it does, whose model it orchestrates, what the knowledge base is.

## Demo
(placeholder — HF Spaces link + GIF go here later today)

## Architecture
START → [image?] → Vision tool (fine-tuned YOLOv8s) → Query planner → Retrieve (Chroma)
→ Grade chunks (LLM) → [weak? rewrite ×2] → Generate with §-citations → Answer / Refusal

## Evaluation (35-question verified dataset)
| Metric | Score |
|---|---|
| Retrieval hit rate | 28/28 |
| Citation validity | 33/33 |
| Faithfulness (LLM-judge + manual audit) | 31/32 |
| Refusal correctness | 33/35 |

## Findings
- (flowchart discovery → VLM transcription pipeline)
- (clean-image false positive → honesty test)
- (i10: citation-backed confabulation, caught by judge)
- (u04: grounded-but-off-target answer — faithfulness checks can't catch it)
- (judge truncation lesson: 3 false "unfaithful" verdicts)

## Limitations
- severity heuristic = bbox area, not calibrated measurement
- report template pressures answers on out-of-scope questions
- free-tier token limits shaped the provider split

## Stack
LangGraph · YOLOv8s (own 1,770-image dataset) · Chroma · Groq Llama-3.3-70B / Llama-3.1-8B · Gemini Flash (figure transcription) · Gradio

## Setup
(clone, pip install, .env keys, where to get weights — link your model repo)