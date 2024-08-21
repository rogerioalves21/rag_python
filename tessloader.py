from langchain_core.documents import Document
from langchain_core.document_loaders.base import BaseBlobParser
from langchain_core.document_loaders.blob_loaders import Blob
from langchain_community.document_loaders.pdf import BasePDFLoader
from typing import Iterator, List, Union
from image_utils import ImageProcessing

class PyTesseractParser(BaseBlobParser):
    """Carga un PDF con pdf2image y extrae texto usando pytesseract."""
    def __init__(self, pdf_path: str):
        self._img_processing = ImageProcessing()
        self._pdf_path       = pdf_path

    def lazy_parse(self, blob: Union[Blob, None] = None) -> Iterator[Document]:
        # recupera somente o nome do arquivo
        __split       = self._pdf_path.split("/")
        # cria o nome base da imagem
        __nome_imagem = __split[-1].replace('.pdf', '.png')
        # converte em imagem cada página
        __imagens     = self._img_processing.pdf_to_image(self._pdf_path, './files/to_img/' + __nome_imagem)
        yield from [
            Document(
                page_content=self._img_processing.get_text_from_image(img_path=img_path),
                metadata={"source": img_path, "page": page_number+1},
            )
            for img_path, page_number in __imagens
        ]

class PyTesseractLoader(BasePDFLoader):
    def __init__(self, file_path: str) -> None:
        self.parser = PyTesseractParser(pdf_path=file_path)
        super().__init__(file_path)

    def load(self) -> List[Document]:
        return list(self.lazy_load())

    def lazy_load(self) -> Iterator[Document]:
        yield from self.parser.parse(None)
        
def main():
    file_path = "./files/pdfs/CCI1029.pdf"
    loader    = PyTesseractLoader(file_path)
    documents = loader.load()

    for doc in documents:
        print(f"Página {doc.metadata['page']}:")
        print(doc.page_content)

if __name__ == "__main__":
    main()