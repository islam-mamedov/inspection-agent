from typing import TypedDict


class AgentState(TypedDict):
    question: str            # the user's question
    queries: list[str]       # current search queries (rewritten over time)
    retrieved: list[dict]    # chunks from Chroma: {id, text, meta}
    relevant: list[dict]     # chunks that survived grading
    rewrite_count: int       # loop guard - max 2 rewrites
    answer: str              # final generated answer
    image_path: str          # "" if no image provided
    defect_findings: dict  