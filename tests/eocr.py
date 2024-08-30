import easyocr
from rich import print

reader = easyocr.Reader(['pt','en'])
result = reader.readtext('./files/to_img/CCI1.081_2024_0_GRAY.png', detail=0, paragraph=True, text_threshold=0.2)
print(result)