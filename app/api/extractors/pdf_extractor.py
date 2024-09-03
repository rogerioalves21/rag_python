from typing import Optional, Any, List, Union
import json
import os
from rich import print
from app.api.extractors.base_extractor import BaseExtractor
from langchain_core.documents import Document
from app.storage.local_storage import LocalStorage
from langchain_community.document_loaders import PyPDFium2Loader
from app.api.services.metadata_service import MetadataService
from concurrent.futures import ThreadPoolExecutor, wait, as_completed


class PdfExtractor(BaseExtractor):
    
    def __init__(
        self,
        file_path: str,
        file_cache_key: Optional[str] = None,
        metadata_service: Optional[MetadataService] = None
    ):
        self._file_path      = file_path
        self._file_cache_key = file_cache_key.replace('.pdf', '.json')
        self._storate = LocalStorage()
        self._metadata_service = metadata_service
        print(self._file_path, self._file_cache_key)

    def __task(self, __document: Document) -> Union[Document, None]:
        return self._metadata_service.extrair_metadata(__document)

    def __save_summary(self) -> Any:
        __documents = self.__to_documents()
        __json = self.__to_json()
        # agora que temos os resumos, vamos fazer um map reduce
        __resumo = self._metadata_service.combinar_resumos(__documents)
        __json['resumo'] = __resumo
        __text = str(__json)
        __text = __text.replace('\'', '\"')
        self._storate.save(self._file_cache_key, __text.encode('utf-8'))
        return __documents

    def __to_json(self, __file: Union[str | None] = None) -> List[Document]:
        if __file:
            __json = self._storate.load_json(__file)
        else:
            __json = self._storate.load_json(self._file_cache_key)
        return __json

    def __to_documents(self) -> List[Document]:
        __documents = list()
        __json = self.__to_json()
        for __page in __json["content"]:
            __document = Document(
                page_content=__page["page_content"],
                metadata={"source": __json["fileName"], "fonte": __json["fileName"], "page": __json["page"], "resumo": __json["resumo"] }
            )
            __documents.append(__document)
        return __documents

    def __to_documents_list(self) -> List[Document]:
        __documents = list()
        __jsons = self._storate.load_json_all()
        for __json in __jsons:
            __document = Document(
                page_content=__json["page_content"],
                metadata={"source": __json["fileName"], "fonte": __json["fileName"], "page": __json["page"], "resumo": __json["resumo"] }
            )
            __documents.append(__document)
        print(__documents)
        return __documents

    async def extract_all(self) -> List[Document]:
        return self.__to_documents_list()

    async def extract(self) -> List[Document]:
        if self._file_cache_key:
            try:
                __documents = self.__to_documents()
                return __documents
            except FileNotFoundError as excecao:
                print(f"\nARQUIVO {self._file_cache_key} NÃO ENCONTRADO!\n")
                print(excecao)
                pass

        # cria o arquivo json contendo as informações do documento.
        __documents = await self.__load()
        print('\nFez o load dos documentos de forma assincrona\n')

        __files = []

        # processo de metadatas assíncrono
        __qtd_workers = (os.cpu_count() or 1) + 1
        print(f"QUANTIDADE DE WORKERS: {__qtd_workers}")
        with ThreadPoolExecutor(max_workers=__qtd_workers) as exe:
            __futures = [exe.submit(self.__task, __document) for __document in __documents]
            wait(__futures)
            for future in as_completed(__futures):
                __doc = future.result()
                __page = __doc.metadata['page']
                print(F"\nDOCUMENTO NA PÁGINA {__page}\n")
                try:
                    __json_name = self._file_cache_key.replace('.json', F"_{__page}.json")
                    __content = { "fileName": __json_name, "page_content": __doc.page_content, "page": __page, "resumo": __doc.metadata["resumo"] }
                    __json_str = json.dumps(__content)
                    self._storate.save(__json_name, __json_str.encode('utf-8'))
                    __files.append(__json_name)
                except Exception as excecao:
                    print(excecao)
                    continue

        # carrega os documentos com o resumo total
        # self.__save_summary()
        print("\nExtração finalizada\n")
        return self.__to_documents_list()

    async def __load(self) -> List[Document]:
        return await self.__parse()
    
    async def __parse(self) -> List[Document]:
        return await PyPDFium2Loader(self._file_path, extract_images=True).aload()