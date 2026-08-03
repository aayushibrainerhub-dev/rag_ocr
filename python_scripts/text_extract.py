import os
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

# 1. Point to your root tessdata directory
# (Since tessdata is in your root OCR-RAG folder, go up one directory from python_scripts)
current_dir = os.path.dirname(os.path.abspath(__file__))
tessdata_dir = os.path.abspath(os.path.join(current_dir, "..", "tessdata"))

custom_config = f'--tessdata-dir "{tessdata_dir}"'

# 2. Path to the PDF file relative to python_scripts
pdf_path = "images/documento_prueba_ocr.pdf"
pages = convert_from_path(pdf_path)

all_text = ""

# 3. Loop through pages correctly
for page_num, page in enumerate(pages):
    # Pass lang='spa' AND custom_config to use your local Spanish model
    text = pytesseract.image_to_string(page, lang='spa', config=custom_config)
    
    all_text += f"\n----- Page {page_num} -----\n"
    all_text += text

print(all_text)