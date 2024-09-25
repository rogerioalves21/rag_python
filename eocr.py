import easyocr
from rich import print

reader = easyocr.Reader(['pt','en'])
result = reader.readtext('./files/old_to_img/CCI1.301_2024_0_GRAY.jpeg', detail=0, paragraph=False, text_threshold=0.2)
print(result)