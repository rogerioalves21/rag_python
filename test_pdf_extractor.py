from app.api.extractors.pdf_extractor import PdfExtractor
from rich import print
import warnings
warnings.filterwarnings("ignore")

if __name__ == "__main__":
    extract = PdfExtractor('./files/pdfs/0702763-79.2024.8.07.0014_0005.pdf')
    documents = extract.extract()
    print(documents)