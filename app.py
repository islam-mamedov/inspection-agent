from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Generator

import gradio as gr

from src.agent.graph import build_graph


app_graph = build_graph()

APP_TITLE = "Concrete Inspection Agent"
PLACEHOLDER = """
### Ready for an inspection

Upload a concrete image, choose a demo, or ask a manual-only question.  
The final response will combine **visual defect findings** with **clause-grounded guidance** from the USACE repair manual.
"""

STATUS_READY = """
<div class="status-pill ready">
  <span class="status-dot"></span>
  <span><strong>Ready</strong> · Add an image or question to begin</span>
</div>
"""

STATUS_RUNNING = """
<div class="status-pill running">
  <span class="status-dot"></span>
  <span><strong>Running inspection</strong> · The agent is analysing and retrieving evidence</span>
</div>
"""

STATUS_COMPLETE = """
<div class="status-pill complete">
  <span class="status-dot"></span>
  <span><strong>Inspection complete</strong> · Review the assessment and supporting activity below</span>
</div>
"""

STATUS_ERROR = """
<div class="status-pill error">
  <span class="status-dot"></span>
  <span><strong>Inspection stopped</strong> · Check the message below and try again</span>
</div>
"""

DEMO_CASES = {
    "Crack repair — image + manual": (
        "data/test_images/crack_0548.jpg",
        "What repair methods does the manual recommend for the defects in this image?",
    ),
    "Corrosion — image + repair guidance": (
        "data/test_images/corrosion_0184.jpg",
        "What does this image show, and what does the manual say about repairing it?",
    ),
    "Spalling — likely causes": (
        "data/test_images/spalling_0372.jpg",
        "What could have caused the defect shown in this image?",
    ),
    "Dormant cracks — manual only": (
        None,
        "What repair methods are suitable for dormant cracks?",
    ),
    "Unsupported question — refusal demo": (
        None,
        "What is the airspeed velocity of an unladen swallow?",
    ),
}

# Keep the interface visually consistent when Hugging Face or Gradio is in
# dark mode. The application itself intentionally uses a light inspection UI,
# so the dark-mode variables mirror the light-mode palette.
APP_THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.blue,
    neutral_hue=gr.themes.colors.slate,
).set(
    body_background_fill="#f3f6fa",
    body_background_fill_dark="#f3f6fa",
    body_text_color="#0d1728",
    body_text_color_dark="#0d1728",
    body_text_color_subdued="#66758a",
    body_text_color_subdued_dark="#66758a",

    background_fill_primary="#ffffff",
    background_fill_primary_dark="#ffffff",
    background_fill_secondary="#f9fbfd",
    background_fill_secondary_dark="#f9fbfd",

    border_color_primary="#dce4ee",
    border_color_primary_dark="#dce4ee",
    border_color_accent="#2f66b1",
    border_color_accent_dark="#2f66b1",

    block_background_fill="#ffffff",
    block_background_fill_dark="#ffffff",
    block_border_color="#dce4ee",
    block_border_color_dark="#dce4ee",
    block_label_background_fill="#ffffff",
    block_label_background_fill_dark="#ffffff",
    block_label_border_color="#dce4ee",
    block_label_border_color_dark="#dce4ee",
    block_label_text_color="#42536a",
    block_label_text_color_dark="#42536a",
    block_title_text_color="#42536a",
    block_title_text_color_dark="#42536a",

    panel_background_fill="#ffffff",
    panel_background_fill_dark="#ffffff",
    panel_border_color="#dce4ee",
    panel_border_color_dark="#dce4ee",

    accordion_text_color="#40536b",
    accordion_text_color_dark="#40536b",

    input_background_fill="#fbfcfe",
    input_background_fill_dark="#fbfcfe",
    input_background_fill_focus="#ffffff",
    input_background_fill_focus_dark="#ffffff",
    input_background_fill_hover="#ffffff",
    input_background_fill_hover_dark="#ffffff",
    input_border_color="#d3deea",
    input_border_color_dark="#d3deea",
    input_border_color_focus="#2f66b1",
    input_border_color_focus_dark="#2f66b1",
    input_border_color_hover="#b7c7da",
    input_border_color_hover_dark="#b7c7da",
    input_placeholder_color="#9aa7b8",
    input_placeholder_color_dark="#9aa7b8",

    button_primary_background_fill="#2f66b1",
    button_primary_background_fill_dark="#2f66b1",
    button_primary_background_fill_hover="#275a9e",
    button_primary_background_fill_hover_dark="#275a9e",
    button_primary_border_color="#2f66b1",
    button_primary_border_color_dark="#2f66b1",
    button_primary_text_color="#ffffff",
    button_primary_text_color_dark="#ffffff",

    button_secondary_background_fill="#ffffff",
    button_secondary_background_fill_dark="#ffffff",
    button_secondary_background_fill_hover="#f7f9fc",
    button_secondary_background_fill_hover_dark="#f7f9fc",
    button_secondary_border_color="#cfdae7",
    button_secondary_border_color_dark="#cfdae7",
    button_secondary_text_color="#4d5f75",
    button_secondary_text_color_dark="#4d5f75",

    link_text_color="#2f66b1",
    link_text_color_dark="#2f66b1",
    code_background_fill="#eef3f8",
    code_background_fill_dark="#eef3f8",
)


CSS = """
:root {
  --cia-ink: #0d1728;
  --cia-navy: #17345f;
  --cia-blue: #2f66b1;
  --cia-blue-soft: #eaf2ff;
  --cia-amber: #c87818;
  --cia-paper: #ffffff;
  --cia-canvas: #f3f6fa;
  --cia-line: #dce4ee;
  --cia-muted: #66758a;
  --cia-success: #17734a;
  --cia-danger: #b33a3a;
}


/*
  Hugging Face follows the viewer's system/site theme. These overrides keep
  this deliberately light interface readable even when the surrounding page
  is dark. Both the normal and "-dark" Gradio variables are pinned here as a
  second layer of protection for embedded Spaces.
*/
html.dark,
body.dark,
.gradio-container.dark,
.dark .gradio-container,
[data-theme="dark"] .gradio-container {
  color-scheme: light !important;

  --body-background-fill: #f3f6fa !important;
  --body-background-fill-dark: #f3f6fa !important;
  --body-text-color: #0d1728 !important;
  --body-text-color-dark: #0d1728 !important;
  --body-text-color-subdued: #66758a !important;
  --body-text-color-subdued-dark: #66758a !important;

  --background-fill-primary: #ffffff !important;
  --background-fill-primary-dark: #ffffff !important;
  --background-fill-secondary: #f9fbfd !important;
  --background-fill-secondary-dark: #f9fbfd !important;

  --block-background-fill: #ffffff !important;
  --block-background-fill-dark: #ffffff !important;
  --block-border-color: #dce4ee !important;
  --block-border-color-dark: #dce4ee !important;
  --block-label-background-fill: #ffffff !important;
  --block-label-background-fill-dark: #ffffff !important;
  --block-label-text-color: #42536a !important;
  --block-label-text-color-dark: #42536a !important;
  --block-title-text-color: #42536a !important;
  --block-title-text-color-dark: #42536a !important;

  --panel-background-fill: #ffffff !important;
  --panel-background-fill-dark: #ffffff !important;
  --panel-border-color: #dce4ee !important;
  --panel-border-color-dark: #dce4ee !important;

  --input-background-fill: #fbfcfe !important;
  --input-background-fill-dark: #fbfcfe !important;
  --input-border-color: #d3deea !important;
  --input-border-color-dark: #d3deea !important;
  --input-placeholder-color: #9aa7b8 !important;
  --input-placeholder-color-dark: #9aa7b8 !important;

  --button-secondary-background-fill: #ffffff !important;
  --button-secondary-background-fill-dark: #ffffff !important;
  --button-secondary-text-color: #4d5f75 !important;
  --button-secondary-text-color-dark: #4d5f75 !important;
}

html, body, .gradio-container {
  margin: 0 !important;
  min-height: 100% !important;
  background: var(--cia-canvas) !important;
  color: var(--cia-ink) !important;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

.gradio-container {
  max-width: 100% !important;
  padding: 0 !important;
}

footer { display: none !important; }

#app-shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at 92% 0%, rgba(47, 102, 177, 0.10), transparent 27rem),
    var(--cia-canvas);
}

/* Header */
#topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 18px 28px;
  color: white;
  background: linear-gradient(110deg, #0d1728 0%, #17345f 62%, #234e84 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.10);
}

.brand-wrap {
  display: flex;
  align-items: center;
  gap: 13px;
  min-width: 0;
}

.brand-icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  border-radius: 11px;
  background: linear-gradient(145deg, #f3ae42, #c87818);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.20);
  font-size: 0.80rem;
  font-weight: 800;
  letter-spacing: 0.06em;
}

.brand-copy h1 {
  margin: 0;
  color: white;
  font-size: 1.16rem;
  font-weight: 720;
  letter-spacing: -0.015em;
}

.brand-copy p {
  margin: 3px 0 0;
  color: #b9c9dd;
  font-size: 0.76rem;
  line-height: 1.35;
}

.header-meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 7px;
}

.meta-chip {
  padding: 5px 10px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 999px;
  color: #dce8f7;
  background: rgba(255, 255, 255, 0.07);
  font-size: 0.66rem;
  font-weight: 650;
  letter-spacing: 0.025em;
  white-space: nowrap;
}

.meta-chip.primary {
  color: #ffe4b7;
  border-color: rgba(243, 174, 66, 0.42);
  background: rgba(200, 120, 24, 0.18);
}

/* Simple workflow strip */
#workflow {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0;
  max-width: 1120px;
  margin: 0 auto;
  padding: 14px 28px 4px;
}

.workflow-step {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  color: #5d6f86;
  font-size: 0.76rem;
  font-weight: 650;
}

.workflow-step:not(:last-child)::after {
  content: "";
  position: absolute;
  top: 50%;
  right: -14%;
  width: 28%;
  height: 1px;
  background: #ccd7e4;
}

.step-number {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  color: white;
  background: var(--cia-navy);
  font-size: 0.70rem;
  font-weight: 800;
}

/* Main workspace */
#workspace {
  max-width: 1480px;
  margin: 0 auto;
  padding: 14px 24px 24px;
  gap: 18px !important;
}

.panel-card {
  height: calc(100vh - 162px);
  min-height: 680px;
  overflow: hidden;
  border: 1px solid var(--cia-line) !important;
  border-radius: 16px !important;
  background: rgba(255, 255, 255, 0.96) !important;
  box-shadow: 0 12px 35px rgba(21, 45, 76, 0.08) !important;
}

.panel-card > div {
  height: 100%;
}

#input-panel, #result-panel {
  padding: 18px !important;
}

.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 13px;
}

.section-heading h2 {
  margin: 0;
  color: var(--cia-ink);
  font-size: 0.98rem;
  font-weight: 750;
  letter-spacing: -0.01em;
}

.section-heading p {
  margin: 4px 0 0;
  color: var(--cia-muted);
  font-size: 0.74rem;
  line-height: 1.45;
}

.section-kicker {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 5px;
  color: var(--cia-blue);
  font-size: 0.66rem;
  font-weight: 800;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.section-kicker::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--cia-amber);
}

.field-label {
  margin: 12px 0 6px 2px;
  color: #42536a;
  font-size: 0.71rem;
  font-weight: 750;
  letter-spacing: 0.025em;
}

/* Components */
#image-input {
  overflow: hidden !important;
  border: 1px dashed #aebdd0 !important;
  border-radius: 12px !important;
  background: #f9fbfd !important;
}

#image-input > div {
  border: 0 !important;
  background: transparent !important;
}


/* Explicit text protection for Gradio internals in dark mode */
#image-input,
#image-input button,
#image-input label,
#image-input span,
#image-input p,
#demo-select,
#demo-select input,
#demo-select button,
#question-input,
#question-input textarea {
  color: var(--cia-ink) !important;
}

#image-input svg,
#demo-select svg {
  color: var(--cia-muted) !important;
  stroke: currentColor !important;
}

#question-input textarea::placeholder,
#demo-select input::placeholder {
  color: #9aa7b8 !important;
  opacity: 1 !important;
}

#demo-select, #question-input {
  border-radius: 10px !important;
}

#demo-select input,
#question-input textarea {
  color: var(--cia-ink) !important;
  background: #fbfcfe !important;
  border-color: #d3deea !important;
  font-size: 0.86rem !important;
}

#question-input textarea {
  line-height: 1.5 !important;
}

#action-row {
  margin-top: 10px;
  gap: 10px !important;
}

#run-button {
  min-height: 44px !important;
  border: 0 !important;
  border-radius: 10px !important;
  color: white !important;
  background: linear-gradient(110deg, #17345f, #2f66b1) !important;
  box-shadow: 0 8px 18px rgba(47, 102, 177, 0.18) !important;
  font-size: 0.88rem !important;
  font-weight: 750 !important;
}

#run-button:hover {
  background: linear-gradient(110deg, #102848, #275a9e) !important;
}

#clear-button {
  min-height: 44px !important;
  border: 1px solid #cfdae7 !important;
  border-radius: 10px !important;
  color: #4d5f75 !important;
  background: white !important;
  font-size: 0.84rem !important;
  font-weight: 700 !important;
}

.helper-card {
  margin-top: 12px;
  padding: 11px 12px;
  border: 1px solid #dce8f5;
  border-radius: 10px;
  color: #52677f;
  background: #f5f9ff;
  font-size: 0.71rem;
  line-height: 1.5;
}

.helper-card strong { color: #234e84; }

/* Status */
#status-output {
  margin: 0 0 11px;
}

.status-pill {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 9px 12px;
  border-radius: 10px;
  font-size: 0.73rem;
}

.status-pill .status-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 8px;
  border-radius: 50%;
}

.status-pill.ready {
  color: #4d627a;
  border: 1px solid #d8e1eb;
  background: #f7f9fc;
}
.status-pill.ready .status-dot { background: #7a8ba0; }

.status-pill.running {
  color: #765018;
  border: 1px solid #f0d6ad;
  background: #fff8ec;
}
.status-pill.running .status-dot {
  background: var(--cia-amber);
  box-shadow: 0 0 0 4px rgba(200, 120, 24, 0.12);
  animation: pulse 1.25s infinite;
}

.status-pill.complete {
  color: #1e6547;
  border: 1px solid #bfe3d0;
  background: #f1fbf6;
}
.status-pill.complete .status-dot { background: var(--cia-success); }

.status-pill.error {
  color: #8d3030;
  border: 1px solid #eccaca;
  background: #fff4f4;
}
.status-pill.error .status-dot { background: var(--cia-danger); }

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.55; transform: scale(0.82); }
}

/* Assessment */
#answer-output {
  min-height: 430px;
  max-height: calc(100vh - 400px);
  overflow-y: auto;
  padding: 17px 19px;
  border: 1px solid #dbe4ee;
  border-left: 4px solid var(--cia-blue);
  border-radius: 12px;
  color: #1a293d;
  background: #f9fbfd;
  font-size: 0.86rem;
  line-height: 1.65;
}

#answer-output h1,
#answer-output h2,
#answer-output h3 {
  color: #17345f;
  letter-spacing: -0.01em;
}

#answer-output h1 { font-size: 1.10rem; }
#answer-output h2 { font-size: 1.00rem; }
#answer-output h3 { font-size: 0.93rem; }
#answer-output strong { color: #142b4c; }
#answer-output code { font-size: 0.79rem; }

#answer-output::-webkit-scrollbar,
#activity-output textarea::-webkit-scrollbar {
  width: 8px;
}

#answer-output::-webkit-scrollbar-thumb,
#activity-output textarea::-webkit-scrollbar-thumb {
  border-radius: 10px;
  background: #c4d0de;
}

/* Agent activity accordion */
#activity-accordion {
  margin-top: 11px;
  border: 1px solid var(--cia-line) !important;
  border-radius: 11px !important;
  background: white !important;
}

#activity-accordion > div:first-child {
  color: #40536b !important;
  font-size: 0.76rem !important;
  font-weight: 750 !important;
}

#activity-output,
#activity-output > div {
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

#activity-output textarea {
  min-height: 112px !important;
  max-height: 150px !important;
  border: 0 !important;
  border-radius: 9px !important;
  color: #b7d2ef !important;
  background: #101b2e !important;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
  font-size: 0.70rem !important;
  line-height: 1.75 !important;
}

.disclaimer {
  margin-top: 9px;
  color: #78879a;
  font-size: 0.66rem;
  line-height: 1.45;
}

@media (max-width: 980px) {
  #topbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-meta { justify-content: flex-start; }

  #workspace {
    padding: 12px 14px 20px;
  }

  .panel-card {
    height: auto;
    min-height: 0;
  }

  #answer-output {
    max-height: none;
    min-height: 360px;
  }
}

@media (max-width: 640px) {
  #topbar { padding: 16px; }
  #workflow { padding: 12px 12px 2px; }
  .workflow-step { font-size: 0.67rem; }
  .workflow-step:not(:last-child)::after { display: none; }
  .brand-copy p { display: none; }
  .meta-chip:nth-child(n+3) { display: none; }
}
"""


HEADER_HTML = """
<div id="topbar">
  <div class="brand-wrap">
    <div class="brand-icon">AI</div>
    <div class="brand-copy">
      <h1>Concrete Inspection Agent</h1>
      <p>Visual defect detection with evidence-grounded repair guidance</p>
    </div>
  </div>
  <div class="header-meta">
    <span class="meta-chip primary">USACE EM 1110-2-2002</span>
    <span class="meta-chip">YOLOv8s vision</span>
    <span class="meta-chip">LangGraph workflow</span>
    <span class="meta-chip">Clause-cited answers</span>
  </div>
</div>
"""

WORKFLOW_HTML = """
<div id="workflow">
  <div class="workflow-step"><span class="step-number">1</span><span>Upload or choose a demo</span></div>
  <div class="workflow-step"><span class="step-number">2</span><span>Ask an inspection question</span></div>
  <div class="workflow-step"><span class="step-number">3</span><span>Review findings and evidence</span></div>
</div>
"""

INPUT_HEADER = """
<div class="section-heading">
  <div>
    <div class="section-kicker">Inspection input</div>
    <h2>Start with a photo or a manual question</h2>
    <p>The image is optional. Demo cases are included for a fast walkthrough.</p>
  </div>
</div>
"""

RESULT_HEADER = """
<div class="section-heading">
  <div>
    <div class="section-kicker">Inspection result</div>
    <h2>Field assessment</h2>
    <p>Defect findings, relevant manual guidance, and refusal when evidence is insufficient.</p>
  </div>
</div>
"""

HELPER_HTML = """
<div class="helper-card">
  <strong>For the clearest result:</strong> use a well-lit close-up of one concrete surface and ask one focused question about defect type, cause, severity, or repair.
</div>
"""

DISCLAIMER_HTML = """
<div class="disclaimer">
  Decision-support demo only. A qualified engineer should verify site conditions, measurements, and final repair decisions.
</div>
"""


def safe_count(value: Any) -> int:
    """Return len(value) when possible, otherwise zero."""
    try:
        return len(value) if value is not None else 0
    except TypeError:
        return 0


def load_demo(selection: str | None) -> tuple[str | None, str]:
    """Populate the image and question fields from a selected demo case."""
    if not selection or selection not in DEMO_CASES:
        return None, ""

    image_path, question = DEMO_CASES[selection]
    if image_path and not Path(image_path).exists():
        # Keep the question usable even if a demo image is absent in a deployment.
        image_path = None
    return image_path, question


def reset_interface() -> tuple[str, None, str, str, str, str]:
    """Reset all visible UI components to their initial state."""
    return "", None, "", PLACEHOLDER, "", STATUS_READY


def run_agent(
    image: str | None,
    question: str | None,
) -> Generator[tuple[str, str, str], None, None]:
    """Stream a concise user-facing activity log while the agent runs."""
    clean_question = (question or "").strip()
    if not clean_question:
        yield (
            "### Add a question\nType a focused inspection question or choose one of the demo cases.",
            "No inspection started.",
            STATUS_READY,
        )
        return

    state = {
        "question": clean_question,
        "queries": [clean_question],
        "image_path": image or "",
        "defect_findings": {},
        "retrieved": [],
        "relevant": [],
        "rewrite_count": 0,
        "answer": "",
    }

    activity: list[str] = ["01  Inspection request received"]
    answer = "_Preparing the inspection workflow…_"
    yield answer, "\n".join(activity), STATUS_RUNNING

    try:
        for step in app_graph.stream(state):
            for node, update in step.items():
                update = update or {}

                if node == "analyze_image":
                    findings = update.get("defect_findings") or {}
                    detected = findings.get("findings") or []
                    labels = []
                    for item in detected:
                        defect_type = str(item.get("defect_type", "defect")).title()
                        severity = str(item.get("severity", "unrated")).title()
                        labels.append(f"{defect_type} ({severity})")
                    summary = ", ".join(labels) if labels else "no visual defect returned"
                    activity.append(
                        f"02  Vision analysis · {findings.get('defects_found', len(detected))} finding(s) · {summary}"
                    )

                elif node == "plan_queries":
                    query_count = safe_count(update.get("queries"))
                    activity.append(f"03  Evidence plan · {query_count} manual search query/queries prepared")

                elif node == "retrieve":
                    activity.append(
                        f"04  Manual retrieval · {safe_count(update.get('retrieved'))} candidate passage(s) found"
                    )

                elif node == "grade":
                    activity.append(
                        f"05  Evidence check · {safe_count(update.get('relevant'))} passage(s) retained"
                    )

                elif node == "rewrite":
                    queries = update.get("queries") or []
                    readable_queries = "; ".join(str(query) for query in queries)
                    activity.append(f"06  Search refinement · {readable_queries or 'query rewritten'}")

                elif node == "generate":
                    answer = update.get("answer") or "No final assessment was returned."
                    activity.append("07  Assessment generated · complete")

            current_status = STATUS_COMPLETE if answer and not answer.startswith("_") else STATUS_RUNNING
            yield answer, "\n".join(activity), current_status

        if answer.startswith("_"):
            answer = "### No final assessment returned\nThe workflow finished without producing a final response."
        yield answer, "\n".join(activity), STATUS_COMPLETE

    except Exception as exc:
        message = str(exc)
        activity.append(f"XX  Workflow stopped · {message[:180]}")

        if "rate_limit" in message.lower() or "429" in message:
            user_message = (
                "### Free-tier quota reached\n"
                "The language-model provider temporarily rejected this request because its free quota was reached. "
                "Please retry after the quota resets."
            )
        else:
            user_message = (
                "### The inspection could not be completed\n"
                f"`{html.escape(message[:300])}`"
            )

        yield user_message, "\n".join(activity), STATUS_ERROR


with gr.Blocks(
    title=APP_TITLE,
    theme=APP_THEME,
    css=CSS,
) as demo:
    with gr.Column(elem_id="app-shell"):
        gr.HTML(HEADER_HTML)
        gr.HTML(WORKFLOW_HTML)

        with gr.Row(elem_id="workspace", equal_height=True):
            with gr.Column(scale=4, min_width=360, elem_classes="panel-card"):
                with gr.Column(elem_id="input-panel"):
                    gr.HTML(INPUT_HEADER)

                    gr.HTML('<div class="field-label">1 · Inspection photo <span style="font-weight:500;color:#8290a2">(optional)</span></div>')
                    image_in = gr.Image(
                        type="filepath",
                        show_label=False,
                        height=248,
                        sources=["upload", "clipboard"],
                        elem_id="image-input",
                    )

                    gr.HTML('<div class="field-label">Demo scenario</div>')
                    demo_select = gr.Dropdown(
                        choices=[("Choose a prepared example", "")] + [
                            (name, name) for name in DEMO_CASES
                        ],
                        value="",
                        show_label=False,
                        allow_custom_value=False,
                        elem_id="demo-select",
                    )

                    gr.HTML('<div class="field-label">2 · Inspection question</div>')
                    question_in = gr.Textbox(
                        show_label=False,
                        lines=3,
                        max_lines=4,
                        placeholder="Example: What repair method does the manual recommend for the defect in this image?",
                        elem_id="question-input",
                    )

                    with gr.Row(elem_id="action-row"):
                        clear_btn = gr.Button("Clear", elem_id="clear-button", scale=1)
                        run_btn = gr.Button("Run inspection", elem_id="run-button", scale=3)

                    gr.HTML(HELPER_HTML)

            with gr.Column(scale=6, min_width=520, elem_classes="panel-card"):
                with gr.Column(elem_id="result-panel"):
                    gr.HTML(RESULT_HEADER)
                    status_out = gr.HTML(STATUS_READY, elem_id="status-output")
                    answer_out = gr.Markdown(PLACEHOLDER, elem_id="answer-output")

                    with gr.Accordion("Agent activity · visual analysis and evidence retrieval", open=True, elem_id="activity-accordion"):
                        activity_out = gr.Textbox(
                            value="",
                            show_label=False,
                            lines=5,
                            max_lines=7,
                            interactive=False,
                            elem_id="activity-output",
                        )

                    gr.HTML(DISCLAIMER_HTML)

    demo_select.change(
        fn=load_demo,
        inputs=demo_select,
        outputs=[image_in, question_in],
        show_progress="hidden",
    )

    run_event = run_btn.click(
        fn=run_agent,
        inputs=[image_in, question_in],
        outputs=[answer_out, activity_out, status_out],
        show_progress="hidden",
    )

    question_in.submit(
        fn=run_agent,
        inputs=[image_in, question_in],
        outputs=[answer_out, activity_out, status_out],
        show_progress="hidden",
    )

    clear_btn.click(
        fn=reset_interface,
        inputs=None,
        outputs=[demo_select, image_in, question_in, answer_out, activity_out, status_out],
        show_progress="hidden",
        cancels=[run_event],
    )


if __name__ == "__main__":
    demo.launch(
        show_error=True,
    )