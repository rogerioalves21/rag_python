from app.api.prepdoclib.image_utils import PyTesseractLoader
from app.api.extractors.pdf_to_text import PdfToTextExtrator
import asyncio
import codecs

async def extrair_imagens(file_path: str) -> None:
    loader    = PyTesseractLoader(file_path)
    documents = loader.load()
    print(documents)

async def extrair_textos(file_path: str) -> None:
    __loader       = PdfToTextExtrator()
    __document = __loader.extrair_texto(file_path)
    with codecs.open('50059699220248210038.txt', 'w', encoding='utf-8') as f:
        f.write(__document.conteudo)

if __name__ == '__main__':
    file_path = "./files/old_pdfs/CCI1.301_2024.pdf"
    loop = asyncio.get_event_loop()
    loop.run_until_complete(extrair_imagens(file_path))
    