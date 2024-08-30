from typing import List, Union, Any, Tuple
from tqdm import tqdm
import os
import time
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from langchain_ollama import ChatOllama
import langchain
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_community.document_transformers import LongContextReorder
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_core.prompts import ChatPromptTemplate
from app.api.prepdoclib.image_utils import PyTesseractLoader
import re
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_community.document_loaders import PyPDFium2Loader
from langchain.retrievers import ParentDocumentRetriever, MergerRetriever
from langchain.storage import InMemoryStore
from rich import print
from app.api.prepdoclib.comunicado_splitter import clean_query
from langchain_community.vectorstores import DuckDB
from app.api.services.metadata_service import MetadataService

langchain.debug = False

all_letters = " abcdefghijlmonpqrstuvxyzABCDEFGHIJLMNOPQRSTUVXYZ.,;'-0123456789"
def unicode_to_ascii(s: str) -> str:
    texto = ''
    for c in s:
        if c in all_letters:
            texto += c 
    return ''.join(texto)

def normalize_string(s: str) -> str:
    s = unicode_to_ascii(s.lower().strip())
    return s.strip()

class ComunicadosService():
    """ Classe responsável por converter arquivos PDF em Imagens.
        Transforma as mesmas em textos, e inclui em base de dados (memória).
    """
    def __init__(
        self,
        text_splitter: CharacterTextSplitter,
        chain: Union[ChatOllama | StrOutputParser | ChatPromptTemplate],
        system_prompt: Union[str, None] = None,
        folder: Union[str, None] = None,
        in_memory: Union[bool, None] = False,
        callbacks: Union[List| None] = None,
        chat_prompt: Union[ChatPromptTemplate, None] = None,
        memory_history: Union[ConversationBufferMemory, None] = None,
        memory_data_base: Union[DocArrayInMemorySearch, None] = None,
        store: Union[InMemoryStore, None] = None,
        duckdb_vector_storage: Union[DuckDB, None] = None,
        duckdb_vector_storage_basic: Union[DuckDB, None] = None
    ):
        self.__chain          = chain
        self.__system_prompt  = system_prompt
        self.__text_splitter  = text_splitter
        self.__folder         = folder
        self.__in_memory      = in_memory
        self.__store          = store # contêm todos os documentos
        self.__callbacks      = callbacks
        self.__chat_prompt    = chat_prompt
        self.__memory         = memory_history # TODO - criar isso para multi-usuário
        self.__data_base      = memory_data_base
        self.__vector_storage = duckdb_vector_storage

        if self.__in_memory:
            self.__full_doc_retriever = ParentDocumentRetriever(
                vectorstore=self.__data_base,
                docstore=self.__store,
                child_splitter=self.__text_splitter,
            )
        else:
            self.__full_doc_retriever = ParentDocumentRetriever(
                vectorstore=self.__vector_storage,
                docstore=self.__store,
                child_splitter=self.__text_splitter,
            )
        self.__chain.verbose = True
        
        # trata o prompt after formatting
        __condense_question_template = """
            Return text in the original language of the follow up question.
            If the follow up question does not need context, return the exact same text back.
            Never rephrase the follow up question given the chat history unless the follow up question needs context.
            
            Chat History: {chat_history}
            Follow Up question: {question}
            Standalone question:
        """
        condense_question_prompt = PromptTemplate.from_template(__condense_question_template)

        __vect_retriever = self.__vector_storage.as_retriever(search_type="similarity", search_kwargs={"k": 10, "include_metadata": True})
        __data_retriever = self.__data_base.as_retriever(search_type="similarity", search_kwargs={"k": 10, "include_metadata": True})

        self.__lotr = MergerRetriever(retrievers=[__data_retriever, __vect_retriever])
        
        self.__qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.__chain,
            retriever=self.__lotr,
            memory=self.__memory,
            condense_question_prompt=condense_question_prompt,
            return_source_documents=True,
            verbose=True
        )
        self.__qa_chain.rephrase_question=False

    def load_data(self) -> None:
        """ popula a store e vectstore """
        self.__obter_conteudo_arquivos()
        print(list(self.__store.yield_keys()))
    
    def set_callbacks(self, value: List) -> None:
        self.__callbacks = value
    
    async def agenerate_memory(self, query: str) -> Any:
        """ Chamada streaming para o llm. Busca os documentos com mais contexto no ParentDocumentRetriever """
        __sub_docs = self.get_sub_documents(clean_query(query), 10)
        __sub_docs.sort(key=lambda x: x.metadata['source'])
        print(__sub_docs)
        __relevantes = []
        for __doc in __sub_docs:
            __relevantes.append(f'\n#### {__doc.metadata['source']} ####\n\n')
            __relevantes.append(__doc.page_content)
            __relevantes.append('\n\n')
        __messages = self.__chat_prompt.format_messages(question=query, context=''.join(__relevantes))
        self.__qa_chain.combine_docs_chain.llm_chain.prompt.messages = __messages
        return await self.__qa_chain.ainvoke(input={"question": query}, config={"callbacks": self.__callbacks, "include_run_info": True})
    
    async def agenerate(self, query: str) -> Any:
        """ Chamada streaming para o llm. Busca os documentos com mais contexto no ParentDocumentRetriever """
        __docs = self.get_parent_documents(clean_query(query))
        __docs.sort(key=lambda x: x.metadata['source'])
        __relevantes = []
        for __doc in __docs:
            __relevantes.append('\n"""')
            __relevantes.append(__doc.page_content)
            __relevantes.append('"""\n')
        __messages = self.__chat_prompt.format_messages(question=query, context=''.join(__relevantes))
        return await self.__chain.agenerate(messages=[__messages])

    def invoke_with_sources(self, query: str) -> Union[Tuple[str, List[Document]], None]:
        """ Chamada para o llm. SubDocuments e Fontes utilizadas """
        __sub_docs   = self.get_sub_documents(clean_query(query), 20)
        # __sub_docs.sort(key=lambda x: x.metadata['source'])
        __reordering = LongContextReorder()
        __reordered_docs = __reordering.transform_documents(__sub_docs)
        print(__reordered_docs)
        # TODO - filtrar por resumo e palavras - chave
        # TODO - OPÇÃO, gerar os embeds do resultado e fazer outro filtro por similaridade.
        __relevantes = []
        for __doc in __reordered_docs:
            __relevantes.append(f'\n#### {__doc.metadata['source']} ####\n\n')
            __relevantes.append(__doc.page_content)
            __relevantes.append('\n\n')
        __messages   = self.__chat_prompt.format_messages(question=query, context=''.join(__relevantes))
        self.__qa_chain.combine_docs_chain.llm_chain.prompt.messages = __messages
        retorno      = self.__qa_chain.invoke({"question": query})
        return retorno['answer'], __sub_docs
    
    def invoke(self, query: str) -> Union[str, None]:
        """ Chamada para o llm. Busca os documentos com mais contexto no ParentDocumentRetriever """
        __sub_docs = self.get_sub_documents(clean_query(query), 20)
        __relevantes = []
        for __doc in __sub_docs:
            __relevantes.append('\n"""')
            __relevantes.append(__doc.page_content)
            __relevantes.append('"""\n')
        __messages = self.__chat_prompt.format_messages(question=query, context=''.join(__relevantes))
        self.__qa_chain.combine_docs_chain.llm_chain.prompt.messages = __messages
        retorno    = self.__qa_chain.invoke({"question": query})
        return retorno['answer']
  
    def get_chain(self) -> Union[ChatOllama | StrOutputParser | ChatPromptTemplate]:
        return self.__chain
    
    def get_system_prompt(self) -> str:
        return self.__system_prompt
    
    def __obter_conteudo_arquivos(self) -> str:
        """ Obtêm os arquivos da pasta, divide e lotes de textos e inclui no banco em memória \"docarray\" """
        arquivos = os.listdir(self.__folder)
        if arquivos:
            self.__carregar_pdf(arquivos)
    
    def __obter_conteudo_arquivo(self) -> str:
        """ Obtêm os arquivos da pasta, divide e lotes de textos e inclui no banco em memória \"docarray\" """
        _lista_arquivos = os.listdir(self.__folder)
        if _lista_arquivos:
             self.__save_documents_from_pdfs(_lista_arquivos)
    
    def __carregar_pdf(self, arquivos: List[str]):
         for arquivo in tqdm(arquivos):
            __doc_path_pdf = self.__folder + arquivo
            __loader       = PyPDFium2Loader(__doc_path_pdf, extract_images=True)
            __documents    = __loader.load()
            # for __doc in __documents:
            #    MetadataService(__doc).extrair_metadata()
            print(__documents)
            self.__full_doc_retriever.add_documents(__documents)

    def __task(self, __arquivo: str) -> Union[List[Document], None]:
        __file_path     = self.__folder + __arquivo
        __pytess_loader = PyTesseractLoader(__file_path)
        return __pytess_loader.load()

    def __save_documents_from_pdfs(self, __arquivos: List[str]) -> None:
        t0 = time.time()
        count = 0
        print('workers started.')
        with ThreadPoolExecutor(max_workers=4) as exe:
            __futures = [exe.submit(self.__task, __arquivo) for __arquivo in __arquivos]
            wait(__futures)
            for future in as_completed(__futures):
                __documents = future.result()
                for __doc in __documents:
                    MetadataService(__doc).extrair_metadata()
                print(__documents)
                self.__full_doc_retriever.add_documents(__documents)
                count += 1
        print(f'all done, {count} documents in {int(int(time.time() - t0)/60)} minutos')
   
    def extrair_numero_cci(self, context: str) -> Union[str, None]:
        __splitado  = context.split('\n')
        __regexer   = re.compile(fr'(?<=(CCI\s[—|-]\s)).*(?=.$)')
        __resultado = list(filter(__regexer.findall, __splitado))
        if __resultado is not None:
            return __resultado[0]
        return None
    
    def get_parent_documents(self, query: str) -> List[Document]:
        """ Recupera os textos completos da página do pdf e não o chunk dos subdocs """
        return self.__full_doc_retriever.invoke(query, kwargs={"verbose": True, "top_k": 4, "k": 4})
    
    def get_sub_documents(self, question: str, top_k: int = 10) -> List[Document]:
        if self.__in_memory:
            relevant_context = self.__data_base.similarity_search(query=question, k=top_k)
        else:
            relevant_context = self.__lotr.get_relevant_documents(query=question)
        return relevant_context

    def get_full_document_by_source(self, source: str) -> Union[Document, None]:
        """ Busca o documento pelo nome do arquivo """
        __document: Union[str, None] = None
        for __doc in self.__documents:
            if source == __doc.metadata['source'] and __doc.metadata['page'] == 0: # no caso de cci é onde a boa informação está
                if __document is None:
                    __document  = __doc.page_content
                else:
                    __document += __doc.page_content
        return __document