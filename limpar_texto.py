import re
from typing import List
from image_utils import ImageProcessing
from app.utils import ComunicadoTextSplitter, tratar_linhas_texto
from rich import print

if __name__ == "__main__":
    img_processing = ImageProcessing()
    splitter = ComunicadoTextSplitter(chunk_size=300, chunk_overlap=0)
    img_processing.pdf_to_image('./files/pdfs/CCI1029.pdf', './files/to_img/CCI1029.png')
    texto = img_processing.get_text_from_image('./files/to_img/CCI1029_0.png')
    chunks = splitter.split_text(texto)
    print(tratar_linhas_texto(texto))
    print("#------------------")
    print(chunks)
