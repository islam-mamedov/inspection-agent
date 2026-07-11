# Concrete Inspection Agent

**A multimodal AI agent for concrete defect detection and evidence-grounded repair guidance.**

[Live demo](https://huggingface.co/spaces/islam-mamedov/inspection-agent) · [Source code](https://github.com/islam-mamedov/inspection-agent)
![Concrete Inspection Agent interface](assets/inspection-agent-demo.png)


> This project is a technical demonstration. Its output is not a substitute for an assessment by a qualified structural engineer.

## Overview

I built this project to explore how computer vision and retrieval-augmented generation can work together in a practical engineering workflow.

A user can upload a concrete inspection image or ask a question about concrete repair. A fine-tuned YOLOv8 model detects cracks, corrosion, and spalling. A LangGraph agent then searches a knowledge base built from **USACE EM 1110-2-2002**, grades the retrieved evidence, rewrites weak searches when necessary, and produces an answer with section-level citations.

When the manual does not support an answer, the system is designed to say that the available evidence is insufficient rather than inventing a recommendation.

## What the system does

- Detects **cracks, corrosion, and spalling** in uploaded images.
- Reports detection confidence and an estimated severity level.
- Converts image findings into targeted technical search queries.
- Retrieves relevant passages from a ChromaDB knowledge base.
- Grades retrieved passages before using them as evidence.
- Rewrites weak queries up to two times.
- Produces inspection-style answers with manual section citations.
- Refuses unrelated or unsupported questions.

## Demo

The deployed Gradio application includes ready-made examples for crack, corrosion, spalling, text-only questions, and an intentionally unsupported question.

[Open the live inspection demo](https://huggingface.co/spaces/islam-mamedov/inspection-agent)

## Architecture

```text
User question
     |
     +---- image supplied? ---- yes ----> YOLOv8 defect analysis
     |                                      |
     |                                      v
     +------------------------------> query planning
                                            |
                                            v
                                  ChromaDB retrieval
                                            |
                                            v
                                    relevance grading
                                      /           \
                              strong evidence   weak evidence
                                    |                |
                                    |          query rewriting
                                    |          (maximum 2)
                                    |                |
                                    +-------<--------+
                                            |
                                            v
                              cited answer or refusal
```

The graph is conditional rather than a single fixed chain. Image analysis runs only when an image is supplied, and the rewrite loop is used only when the first retrieval attempt does not return enough relevant evidence.

## Knowledge base

The knowledge base is based on **USACE EM 1110-2-2002: Evaluation and Repair of Concrete Structures**.

The document was processed into section-aware chunks that retain document, chapter, section, and title metadata. Two important repair-selection flowcharts were also converted into explicit text paths because their logic was not available through normal text extraction.

The final retrieval collection contains **292 chunks**:

- 290 section-aware document chunks
- 2 manually checked figure-transcription chunks

## Model and data

The detector was fine-tuned on a custom structural-defect dataset containing:

- **1,770 images**
- **5,897 annotated objects**
- Three classes: **crack, corrosion, and spalling**

The trained checkpoint is expected at:

```text
models/YOLOv8s_v24.pt
```

Model weights are not committed to normal Git history.

## Evaluation

I evaluated the complete system with 35 manually verified questions:

- 20 text-only questions
- 10 image-and-text questions
- 5 deliberately unanswerable questions

| Metric | Result |
|---|---:|
| Retrieval hit rate | 28 / 28 |
| Citation validity | 33 / 33 |
| Faithfulness | 31 / 32 |
| Refusal correctness | 33 / 35 |

The evaluation combines deterministic checks, an LLM-based faithfulness judge, and manual review of flagged failures.

Raw evaluation scripts and results are available in `eval/`.

## What I learned

### Important information was hidden inside figures

Some of the manual's most useful repair guidance appears in decision-tree flowcharts rather than normal paragraphs. Text-only retrieval could not answer those questions reliably, so I added a figure-transcription step and manually checked the extracted decision paths before indexing them.

### A confident detector can still be wrong

The detector produced a false positive on a defect-free concrete image. I kept that example in the evaluation set because it is a useful honesty test: the language model should distinguish between a model prediction and confirmed physical damage.

### Grounded does not always mean relevant

One out-of-scope question produced an answer that was supported by a retrieved passage but did not truly answer the user's question. This showed that faithfulness and answer relevance are different problems. A future version should include a dedicated answer-relevance check before returning the final response.

### Evaluation models also need auditing

Several answers were initially marked unfaithful because the judge received truncated evidence. After reviewing the failures and widening the evidence window, the incorrect flags disappeared. I therefore treat LLM-based evaluation as a tool that still requires manual verification.

## Limitations

- Severity is estimated from relative bounding-box area. It is not a calibrated crack-width or structural-severity measurement.
- The knowledge base currently covers one concrete-repair manual.
- Detection quality depends on image quality, lighting, angle, and similarity to the training data.
- The workflow uses external language-model APIs, so latency and availability depend on provider limits.
- The application provides decision support only and should not be treated as a professional engineering diagnosis.

## Technology

- Python
- LangGraph
- LangChain
- YOLOv8 / Ultralytics
- ChromaDB
- Groq-hosted Llama models
- Gemini 2.5 Flash
- Gradio
- Hugging Face Spaces

## Repository structure

```text
inspection-agent/
├── app.py                  # Gradio application
├── ask.py                  # Command-line interface
├── data/
│   ├── chunks.json         # Processed knowledge-base chunks
│   ├── eval/               # Evaluation questions
│   └── test_images/        # Demo and evaluation images
├── eval/
│   ├── run_eval.py         # Evaluation runner
│   ├── judge.py            # Faithfulness evaluation
│   └── results/            # Saved evaluation outputs
├── src/
│   ├── agent/              # LangGraph state, nodes, and routing
│   ├── ingestion/          # Parsing, chunking, and indexing
│   └── tools/              # Defect detector
└── requirements.txt
```

## Run locally

Python **3.11** is recommended.

```bash
git clone https://github.com/islam-mamedov/inspection-agent.git
cd inspection-agent

python3.11 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key
```

Place the trained model at:

```text
models/YOLOv8s_v24.pt
```

Build the local Chroma index from the committed chunks when needed:

```bash
python src/ingestion/index.py
```

Start the web interface:

```bash
python app.py
```

You can also run a question from the terminal:

```bash
python ask.py "What repair methods are suitable for dormant cracks?"
```

For an image-based query:

```bash
python ask.py \
  "What does this image show, and what repair guidance is relevant?" \
  --image data/test_images/corrosion_0184.jpg
```

## Evaluation commands

Run the complete evaluation:

```bash
python eval/run_eval.py eval/results/run_full.json
python eval/judge.py eval/results/run_full.json
```

To disable query rewriting for an ablation experiment:

```bash
MAX_REWRITES=0 python eval/run_eval.py \
  eval/results/run_ablation.json \
  data/eval/qa_subset.json
```

## Security

API keys must be stored in `.env` locally or as Hugging Face Space secrets. Do not place credentials in source files, notebooks, terminal screenshots, or documentation.

## Author

**Islam Mamedov**  
Bachelor of Computer Science — Artificial Intelligence and Cybersecurity

## License

This project is released under the [MIT License](LICENSE).

```text
Copyright (c) 2026 Islam Mamedov