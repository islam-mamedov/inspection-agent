import json
import re
from pathlib import Path

INPUT = "parse_preview.md"
OUTPUT = "data/chunks.json"

MAX_CHARS = 3000      # ~800 tokens: max chunk size
OVERLAP_CHARS = 400   # tail of previous piece carried into the next
MIN_CHUNK_CHARS = 200 # anything shorter is caption/garbage, drop it

# "## Chapter 3 Causes of Distress..." -> new chapter
chapter_re = re.compile(r"^##\s+Chapter\s+(\d+)\s*(.*)", re.IGNORECASE)
# "## 3-2. Causes of Distress..." -> new section ([-–] handles both dash types OCR produces)
section_re = re.compile(r"^##\s+(\d+)[-–](\d+)\.?\s+(.*)")


def split_long(text: str) -> list[str]:
    """Split long text at paragraph boundaries, with overlap between pieces."""
    if len(text) <= MAX_CHARS:
        return [text]
    paragraphs = text.split("\n\n")
    pieces, buf = [], ""
    for p in paragraphs:
        if buf and len(buf) + len(p) > MAX_CHARS:
            pieces.append(buf.strip())
            buf = buf[-OVERLAP_CHARS:] + "\n\n" + p  # carry overlap tail
        else:
            buf = (buf + "\n\n" + p) if buf else p
    if buf.strip():
        pieces.append(buf.strip())
    return pieces


def main():
    lines = Path(INPUT).read_text().splitlines()

    chunks = []
    chapter = None          # e.g. "3"
    section = None          # e.g. "3-2"
    section_title = ""
    buffer: list[str] = []

    def flush():
        """Turn the current buffer into one or more chunks."""
        nonlocal buffer
        text = "\n".join(buffer).strip()
        buffer = []
        if not section or len(text) < MIN_CHUNK_CHARS:
            return
        header = f"[EM 1110-2-2002 §{section} {section_title}]"
        for i, piece in enumerate(split_long(text)):
            chunks.append({
                "id": f"em2002_{section}_part{i}",
                "text": f"{header}\n{piece}",
                "meta": {
                    "doc": "EM 1110-2-2002",
                    "chapter": chapter,
                    "section": section,
                    "section_title": section_title,
                },
            })

    for line in lines:
        ch = chapter_re.match(line)
        sec = section_re.match(line)
        if ch:
            flush()
            chapter = ch.group(1)
            # chapter intro text (before first numbered section) gets section "N-0"
            section = f"{chapter}-0"
            section_title = ch.group(2).strip() or f"Chapter {chapter}"
        elif sec:
            flush()
            section = f"{sec.group(1)}-{sec.group(2)}"
            section_title = sec.group(3).strip()
        elif chapter is None:
            continue  # still in TOC / front matter -> skip
        elif line.startswith("## "):
            buffer.append(line[3:])  # fake heading (figure caption etc) -> body text
        else:
            buffer.append(line)
    flush()  # don't forget the last section

    Path("data").mkdir(exist_ok=True)
    Path(OUTPUT).write_text(json.dumps(chunks, indent=2))

    # summary
    per_chapter = {}
    for c in chunks:
        per_chapter[c["meta"]["chapter"]] = per_chapter.get(c["meta"]["chapter"], 0) + 1
    print(f"Total chunks: {len(chunks)}")
    print(f"Avg length: {sum(len(c['text']) for c in chunks) // len(chunks)} chars")
    print("Per chapter:", dict(sorted(per_chapter.items(), key=lambda x: int(x[0]))))


if __name__ == "__main__":
    main()