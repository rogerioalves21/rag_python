from typing import List, Union, Any, Tuple
from tqdm import tqdm
import os
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
from image_utils import ImageProcessing
from langchain_core.messages import BaseMessage
import unicodedata
import re
import string
from langchain_core.outputs import (
    LLMResult,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFium2Loader
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from clean_symbols import CleanSymbolsProcessor
from langchain.chains.retrieval_qa.base import RetrievalQA

all_letters = " abcdefghijlmonpqrstuvxyzABCDEFGHIJLMNOPQRSTUVXYZ.,;'-0123456789"
def unicode_to_ascii(s: str) -> str:
    texto = ''
    for c in s:
        if c in all_letters:
            texto += c 
    return ''.join(texto)

def normalize_string(s: str) -> str:
    s = unicode_to_ascii(s.lower().strip())
    # s = re.sub(r"([.!?])", r" \1", s)
    # s = re.sub(r"[^a-zA-Z!?]+", r" ", s)
    return s.strip()

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
        chat_prompt: Union[ChatPromptTemplate, None] = None
    ):
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
        
        self.__chroma_db = Chroma(
            collection_name="comunicados-sicoob",
            embedding_function=self.__embedding_function,
        )
        
        self.__full_doc_retriever = ParentDocumentRetriever(
            vectorstore=self.__chroma_db,
            docstore=self.__store,
            child_splitter=self.__text_splitter,
        )
        
        self.__chain.verbose = True
              
        self.__retrieval_qa = RetrievalQA.from_chain_type(
            llm=self.__chain,
            # prompt=self.__chat_prompt,
            retriever=self.__full_doc_retriever,
            # callbacks=self.__callbacks,
            # return_source_documents=True
        )
        
        self.__retrieval_qa.verbose = True
        
        # popula a store e vectstore
        self.__obter_conteudo_arquivo()
        self.__documents.sort(key=lambda x: x.metadata["page"])
        self.__full_doc_retriever.add_documents(self.__documents, ids=None)
        
        if self.__in_memory:
            self.__retriever = None
        else:
            metadata_field_info = [
                AttributeInfo(
                    name="documento",
                    description="O nome do documento que foi extraída a informação. Pode ser um arquivo PDF ou PNG",
                    type="string",
                ),
                AttributeInfo(
                    name="chunk_index",
                    description="Qual índice do chunk que a informação está",
                    type="integer",
                ),
                AttributeInfo(
                    name="CCI",
                    description="O Número do comunicado",
                    type="integer",
                )
            ]
            self.__retriever = SelfQueryRetriever.from_llm(
                llm=self.__chain,
                vectorstore=self.__chroma_db,
                text_splitter=self.__text_splitter,
                document_contents="Comunicados sobre problemas, novos produtos ou alteração de produto do Sicoob - SISBR",
                metadata_field_info=metadata_field_info,
                verbose=True,
                enable_limit=True
            )
            
    async def agenerate(self, query: str) -> Any:
        """ Chamada streaming para o llm. Busca os documentos com mais contexto no ParentDocumentRetriever """
        __docs = self.get_contexto_relevante(query)
        __docs.sort(key=lambda x: x.metadata['source'] and x.metadata["page"])
        print(__docs)
        __relevantes = []
        for __doc in __docs:
            # __source = __doc.metadata['source']
            __relevantes.append('\n\n')
            __relevantes.append(__doc.page_content) #self.get_full_document_by_source(__source))
        # print(__relevantes)
        __messages = self.__chat_prompt.format_messages(question=query, context=__relevantes)
        return await self.__chain.agenerate(messages=[__messages])
    
    def invoke(self, query: str) -> str:
        """ Chamada para o llm. Busca os documentos com mais contexto no ParentDocumentRetriever """
        __docs = self.get_contexto_relevante(query)
        __docs.sort(key=lambda x: x.metadata['source'] and x.metadata["page"])
        print(__docs)
        __relevantes = []
        for __doc in __docs:
            # __source = __doc.metadata['source']
            __relevantes.append('\n\n')
            __relevantes.append(__doc.page_content) #self.get_full_document_by_source(__source))
        # print(__relevantes)
        __messages = self.__chat_prompt.format_messages(question=query, context=__relevantes)
        return self.__chain.invoke(__messages).content
    
    def get_retriever(self) -> SelfQueryRetriever:
        return self.__retriever
    
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
        arquivos      = os.listdir(self.__folder)
        img_pdf_pages = []
        if arquivos:
            img_pdf_pages = self.__pdf_to_imagens(arquivos)
            self.__gerar_embed_data_base(img_pdf_pages)
    
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
                    self.__chroma_db = Chroma.from_documents(collection_name="comunicados-sicoob", documents=document_chunks, embedding=self.__embedding_function)
            else:
                if self.__in_memory:
                    self.__data_base.add_documents(document_chunks)
                else:
                    self.__chroma_db.add_documents(document_chunks)
    
    def __pdf_to_imagens(self, arquivos: List[str]) -> List[Tuple[str, str, int]]:
        """ Converte os pdfs em imagens e retorna a lista com as imagens geradas """
        __img_pdf_pages   = []
        for arquivo in tqdm(arquivos):
            __file_path   = self.__folder + arquivo
            __nome_imagem = normalize_string(arquivo).replace(' ', '_')
            __nome_imagem = __nome_imagem.replace('.pdf', '.png')
            __imagens     = self.__img_prc.pdf_to_image(__file_path, './files/to_img/' + __nome_imagem)
            for __imagem, __pagina in __imagens:
                __img_pdf_pages.append((arquivo.replace(' ', '_'), __imagem, __pagina))
        return __img_pdf_pages
    
    def __gerar_embed_data_base(self, imagens: List[str]) -> None:
        """ Lê os arquivos na lista, gera chunks para os mesmos e inclui na base de dados """
        for __arquivo_original, __image_path, __pagina in tqdm(imagens):
            if (__pagina > 0):
                continue
            __conteudo        = self.__img_prc.get_text_from_image(__image_path)
            __document_chunks = __conteudo
            
            self.__documents.append(
                Document(
                    page_content=self.__limpar_texto(__document_chunks),
                    metadata={"source": __arquivo_original, "page": __pagina}
                )
            )
    
    def extrair_numero_cci(self, context: str) -> Union[str, None]:
        __splitado  = context.split('\n')
        __regexer   = re.compile(fr'(?<=(CCI\s[—|-]\s)).*(?=.$)')
        __resultado = list(filter(__regexer.findall, __splitado))
        if __resultado is not None:
            return __resultado[0]
        return None
    
    def __converter_texto_para_chunks(self, texto_arquivo: str) -> List[str]:
        return self.__text_splitter.split_text(texto_arquivo)
    
    def get_contexto_relevante(self, query: str) -> List[Document]:
        """ Recupera os textos completos da página do pdf e não o chunk dos subdocs """
        return self.__full_doc_retriever.invoke(query, kwargs={"verbose": True})
    
    def obter_contexto_relevante(self, question: str, top_k: int = 2) -> List[Document]:
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

    def reescrever_query(self, question: str, contexto_relevante: str) -> str:
        output = None
        messages = [
            ("system", f"Você é um ótimo assistente chamdo chamado Qwen-2, especialista em reformular perguntas e sua tarefa é reformular as perguntas de usuários fornecidas na rola user. Se você, o assistente não souber o que responder então não escreva nada."),# usando as informações contidas no contexto fornecido na outra role user. Se você, o assistente não souber responder então repita a pergunta orginal apenas, sem acrescentar nada."),
            ("user", f"Pergunta: {question}"),
            ("assistant", f""),
            # ("user", f"Contexto: {contexto_relevante}"),
        ]
        output = self.__chain_qr.invoke(messages)
        return output

    def __limpar_texto(self, t: str) -> str:
        __t      = t.replace(' \n', '\n').replace('— \n', '— ').replace('—\n', '— ').replace('- \n', '- ').replace('-\n', '- ').replace(') \n', ') ').replace(')\n', ') ').replace('o \n', 'o ').replace('o\n', 'o ').replace('s \n', 's ').replace('s\n', 's ').replace('e \n', 's ').replace('e\n', 'e ').replace('a \n', 'a ').replace('a\n', 'a ').replace('r \n', 'r ').replace('r\n', 'r ').replace('á \n', 'á ').replace('á\n', 'á ').replace('HRESTRITAH', '')
        _cleaner = CleanSymbolsProcessor()
        return _cleaner.process_line(__t).replace('  ', ' ').strip().replace('\n', ' ').replace('  ', ' ').strip()