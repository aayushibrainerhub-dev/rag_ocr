import fitz
from PIL import Image
from paddleocr import PaddleOCR
import os
import tempfile

ocr = PaddleOCR(
    lang = "es",
    use_doc_orientation_classify = False,
    use_doc_unwarping = False
)

pdf_path = "images/documento_prueba_ocr.pdf"
doc = fitz.open(pdf_path)
for page_num in range(len(doc)):
    page = doc.load_page(page_num)
    pix = page.get_pixmap()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        temp_img = tmp.name
    pix.save(temp_img)
    print(f"\n======== Page {page_num + 1} ========")
    result = ocr.predict(temp_img)
    for page in result:
        for text in page["rec_texts"]:
            print(text)
    os.remove(temp_img)