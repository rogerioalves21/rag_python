from typing import Optional, Any, List

from app.api.extractors.base_extractor import BaseExtractor
from langchain_core.documents import Document
from app.storage.local_storage import storage
from langchain_community.document_loaders import PyPDFium2Loader


class PdfExtractor(BaseExtractor):
    
    def __init__(self, file_path: str, file_cache_key: Optional[str] = None):
        """Initialize with file path."""
        self._file_path      = file_path
        self._file_cache_key = file_cache_key

    def extract(self) -> List[Document]:
        plaintext_file_key    = ''
        plaintext_file_exists = False
        if self._file_cache_key:
            try:
                text = storage.load(self._file_cache_key).decode('utf-8')
                plaintext_file_exists = True
                return [Document(page_content=text)]
            except FileNotFoundError as excecao:
                print(excecao)
                pass
        documents = list(self.load())
        text_list = []
        for document in documents:
            text_list.append(document.page_content)
        text = "\n\n".join(text_list)
        if not plaintext_file_exists and plaintext_file_key:
            storage.save(plaintext_file_key, text.encode('utf-8'))
        return documents

    def load(self) -> List[Document]:
        return self.parse()

    def parse(self) -> List[Document]:
        return PyPDFium2Loader(self._file_path, extract_images=True).load()