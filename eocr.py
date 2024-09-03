import easyocr
from rich import print

reader = easyocr.Reader(['pt','en'])
result = reader.readtext('./files/to_img/CCI500_2023_2.png', detail=0, paragraph=False, text_threshold=0.2)
print(result)