from docling.document_converter import DocumentConverter
import sys

pdf_path = "data/raw_docs/em_1110-2-2002.pdf"

print("Parsing... (this is a scanned PDF, may take several minutes)")
converter = DocumentConverter()
result = converter.convert(pdf_path)
doc = result.document

# Export to markdown so we can eyeball the structure
with open("parse_preview.md", "w") as f:
    f.write(doc.export_to_markdown())

print("Done. Open parse_preview.md and review it.")