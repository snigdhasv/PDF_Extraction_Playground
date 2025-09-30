from docling.document_converter import DocumentConverter

pdf_path = r"D:\College\CognitiveLab\PDF_Extraction_Playground\backend\test.pdf"
converter = DocumentConverter()
result = converter.convert(pdf_path)
print(result)