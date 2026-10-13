from pathlib import Path

pdf_path = Path(__file__).resolve().parent / "SQL_Stock_Market_Analysis_Student_Guide.pdf"
print('exists', pdf_path.exists(), 'size', pdf_path.stat().st_size if pdf_path.exists() else 'missing')

try:
    import pypdf
    reader = pypdf.PdfReader(str(pdf_path))
    print('pages', len(reader.pages))
    for i, page in enumerate(reader.pages[:10], start=1):
        text = page.extract_text() or ''
        print(f'--- PAGE {i} ---')
        print(text[:2500])
except Exception as e:
    print('ERROR', type(e).__name__, e)
