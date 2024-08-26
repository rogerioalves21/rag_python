import easyocr
from rich import print

reader = easyocr.Reader(['pt','en'])
result = reader.readtext('./files/to_img/CIRCULARSUP_6_GRAY.png', detail=0, paragraph=True, text_threshold=0.2)
print(result)