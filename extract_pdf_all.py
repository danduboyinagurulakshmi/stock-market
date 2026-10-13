from pathlib import Path
import pypdf

root = Path(__file__).resolve().parent
pdf_path = root / "SQL_Stock_Market_Analysis_Student_Guide.pdf"
out_path = root / "guide_text.txt"
reader = pypdf.PdfReader(str(pdf_path))
parts = []
for i, page in enumerate(reader.pages, start=1):
    text = page.extract_text() or ''
    parts.append(f'--- PAGE {i} ---\n{text}\n')
out_path.write_text('\n'.join(parts), encoding='utf-8')
print('pages', len(reader.pages), 'saved to', out_path)
