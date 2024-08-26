from typing import List, Union, Any
from tqdm import tqdm
import os
import time
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
try:
    from langchain_chroma import Chroma
except:
    print("não existe o chroma instalado")
from langchain_core.prompts import ChatPromptTemplate
from image_utils import ImageProcessing, PyTesseractLoader
import re
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_community.document_loaders import PyPDFium2Loader
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from rich import print
from app.api.prepdoclib.textparser import TextParser
from app.api.prepdoclib.comunicado_splitter import clean_query

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

data_base = None

class ComunicadosService():
    """ Classe responsável por converter arquivos PDF em Imagens.
        Transforma as mesmas em textos, e inclui em base de dados (memória).
    """
    def __init__(
        self,
        embedding_function: OllamaEmbeddings,
        text_splitter: CharacterTextSplitter,
        chain: Union[ChatOllama | StrOutputParser | ChatPromptTemplate],
        chain_qr: Union[ChatOllama | StrOutputParser | ChatPromptTemplate, None] = None,
        system_prompt: Union[str, None] = None,
        folder: Union[str, None] = None,
        in_memory : Union[bool, None] = False,
        callbacks: Union[List| None] = None,
        chat_prompt: Union[ChatPromptTemplate, None] = None,
        memory_history: Union[ConversationBufferMemory, None] = None
    ):
        self.__text_parser        = TextParser()
        self.__data_base          = None
        self.__chroma_db          = None
        self.__embedding_function = embedding_function
        self.__chain              = chain
        self.__chain_qr           = chain_qr
        self.__system_prompt      = system_prompt
        self.__text_splitter      = text_splitter
        self.__folder             = folder
        self.__img_prc            = ImageProcessing()
        self.__in_memory          = in_memory
        self.__documents          = []
        self.__store              = InMemoryStore() # contêm todos os documentos
        self.__callbacks          = callbacks
        self.__chat_prompt        = chat_prompt
        self.__memory             = memory_history # TODO - criar isso para multi-usuário

        __chroma_folder = '/home/rogerio_rodrigues/python-workspace/rag_python/collection/'
        # self.__store = LocalFileStore(root_path='C:/Users/rogerio.rodrigues/Documents/workspace_python/doc_store/')
        if not self.__in_memory:
            self.__chroma_db = Chroma(
                collection_name="comunicados-sicoob",
                embedding_function=self.__embedding_function,
                persist_directory=__chroma_folder,
            )
            print(self.__chroma_db)

        self.__data_base = DocArrayInMemorySearch.from_params(
            embedding=self.__embedding_function,
            metric="euclidian_dist",
        )

        if self.__in_memory:
            self.__full_doc_retriever = ParentDocumentRetriever(
                vectorstore=self.__data_base,
                docstore=self.__store,
                child_splitter=self.__text_splitter,
                search_kwargs={"k": 10}
            )
        else:
            self.__full_doc_retriever = ParentDocumentRetriever(
                vectorstore=self.__chroma_db,
                docstore=self.__store,
                child_splitter=self.__text_splitter,
                search_kwargs={"k": 10}
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
        
        self.__qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.__chain,
            retriever=self.__full_doc_retriever,
            memory=self.__memory,
            condense_question_prompt=condense_question_prompt,
            return_source_documents=True,
            verbose=True
        )

        self.__qa_chain.rephrase_question=False

    def load_data(self) -> None:
        """ popula a store e vectstore """
        data_base = DocArrayInMemorySearch.from_params(
            embedding=self.__embedding_function,
            metric="euclidian_dist",
        )
        self.__data_base = data_base
        self.__obter_conteudo_arquivo()
        print(list(self.__store.yield_keys()))
    
    def set_callbacks(self, value: List) -> None:
        self.__callbacks = value
    
    async def agenerate_memory(self, query: str) -> Any:
        """ Chamada streaming para o llm. Busca os documentos com mais contexto no ParentDocumentRetriever """
        __sub_docs = self.get_sub_documents(clean_query(query), 10)
        print(__sub_docs)
        # __sub_docs.reverse()
        __relevantes = []
        for __doc in __sub_docs:
            __relevantes.append('\n"""')
            __relevantes.append(__doc.page_content)
            __relevantes.append('"""\n')
        __messages = self.__chat_prompt.format_messages(question=query, context=''.join(__relevantes))
        self.__qa_chain.combine_docs_chain.llm_chain.prompt.messages = __messages
        return await self.__qa_chain.ainvoke({"question": query}, {"callbacks": self.__callbacks})
    
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
    
    def invoke(self, query: str) -> Union[str, None]:
        """ Chamada para o llm. Busca os documentos com mais contexto no ParentDocumentRetriever """
        __sub_docs = self.get_sub_documents(clean_query(query), 20)
        __sub_docs.reverse()
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
        arquivos      = os.listdir(self.__folder)
        if arquivos:
            self.__carregar_pdf(arquivos)
    
    def __obter_conteudo_arquivo(self) -> str:
        """ Obtêm os arquivos da pasta, divide e lotes de textos e inclui no banco em memória \"docarray\" """
        _lista_arquivos = os.listdir(self.__folder)
        if _lista_arquivos:
             self.__save_documents_from_pdfs(_lista_arquivos)
    
    def __carregar_pdf(self, arquivos: List[str]):
         for arquivo in tqdm(arquivos):
            doc_path_pdf     = self.__folder + arquivo
            loader           = PyPDFium2Loader(doc_path_pdf)
            documents        = loader.load()
            self.__documents.extend(documents)
            document_chunks  = self.__text_splitter.split_documents(documents=documents)
            if self.__data_base is None:
                if self.__in_memory:
                    self.__data_base = DocArrayInMemorySearch.from_documents(collection_name="comunicados-sicoob", documents=document_chunks, embedding=self.__embedding_function)
                else:
                    self.__chroma_db = None# Chroma.from_documents(collection_name="comunicados-sicoob", documents=document_chunks, embedding=self.__embedding_function)
            else:
                if self.__in_memory:
                    self.__data_base.add_documents(document_chunks)
                else:
                    raise Exception('sem base de dados configurada')
                    ## self.__chroma_db.add_documents(document_chunks)

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
    
    def __converter_texto_para_chunks(self, texto_arquivo: str) -> List[str]:
        return self.__text_splitter.split_text(texto_arquivo)
    
    def get_parent_documents(self, query: str) -> List[Document]:
        """ Recupera os textos completos da página do pdf e não o chunk dos subdocs """
        return self.__full_doc_retriever.invoke(query, kwargs={"verbose": True, "top_k": 4, "k": 4})
    
    def get_sub_documents(self, question: str, top_k: int = 10) -> List[Document]:
        if self.__in_memory:
            relevant_context = self.__data_base.similarity_search(query=question, k=top_k)
        else:
            relevant_context = self.__chroma_db.similarity_search(query=question, k=top_k)
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