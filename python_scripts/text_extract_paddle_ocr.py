from paddleocr import PaddleOCR

ocr = PaddleOCR(lang='es', use_doc_orientation_classify = False, use_doc_unwarping = False)
result = ocr.predict("images/spanish_text.jpeg")
for page in result:
    for text in page["rec_texts"]:
        print(text)