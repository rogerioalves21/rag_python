import re
from typing import List
from app.api.prepdoclib.image_utils import ImageProcessing
from rich import print

if __name__ == "__main__":
    img_processing = ImageProcessing()
    img_processing.pdf_to_image('./files/pdfs/CCI500_2023.pdf', './files/to_img/CCI500_2023.png')
