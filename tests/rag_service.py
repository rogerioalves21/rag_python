from typing import List, Union, Dict, Any, AsyncIterator
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
from app.api.prepdoclib.image_utils import ImageProcessing
from langchain_core.messages import BaseMessage
import unicodedata
import re
from langchain_core.prompts import ChatPromptTemplate

def unicode_to_ascii(s: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

def normalize_string(s: str) -> str:
    s = unicode_to_ascii(s.lower().strip())
    s = re.sub(r"([.!?])", r" \1", s)
    s = re.sub(r"[^a-zA-Z!?]+", r" ", s)
    return s.strip()

class RAGService():
    """ Classe responsável por converter arquivos PDF em Imagens.
        Transforma as mesmas em textos, e inclui em base de dados (memória).
    """
    def __init__(
        self,
        embedding_function: OllamaEmbeddings,
        text_splitter: CharacterTextSplitter,
        chain: Union[ChatOllama | StrOutputParser | ChatPromptTemplate],
        chain_qr: Union[ChatOllama | StrOutputParser | ChatPromptTemplate] = None,
        system_prompt: str = None,
        folder: str = None,
        in_memonry : bool = False
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
        self.__in_memory          = in_memonry
        
        self.__obter_conteudo_arquivo()
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
        
    def invoke(self, messages: List[BaseMessage]) -> str:
        return self.__chain.invoke(messages)
    
    def get_retriever(self) -> SelfQueryRetriever:
        return self.__retriever
    
    def get_chain(self) -> Union[ChatOllama | StrOutputParser | ChatPromptTemplate]:
        return self.__chain
    
    def get_system_prompt(self) -> str:
        return self.__system_prompt
    
    def __obter_conteudo_arquivo(self) -> str:
        """ Obtêm os arquivos da pasta, divide e lotes de textos e inclui no banco em memória \"docarray\" """
        arquivos      = os.listdir(self.__folder)
        img_pdf_pages = []
        if arquivos:
            img_pdf_pages = self.__pdf_to_imagens(arquivos)
            self.__gerar_embed_data_base(img_pdf_pages)
            
    def __pdf_to_imagens(self, arquivos: List[str]) -> List[str]:
        """ Converte os pdfs em imagens e retorna a lista com as imagens geradas """
        img_pdf_pages   = []
        for arquivo in tqdm(arquivos):
            file_path   = self.__folder + arquivo
            nome_imagem = normalize_string(arquivo).replace(' ', '_')
            img_pdf_pages.extend(self.__img_prc.pdf_to_image(file_path, './files/to_img/' + nome_imagem.replace('_pdf', '.png')))
        return img_pdf_pages
    
    def __gerar_embed_data_base(self, imagens: List[str]) -> None:
        """ Lê os arquivos na lista, gera chunks para os mesmos e inclui na base de dados """
        for image_path in tqdm(imagens):
            conteudo        = self.__img_prc.get_text_from_image(image_path)
            document_chunks = self.__converter_texto_para_chunks(conteudo)
            
            # TODO - incluir palavras-chave no metadata
            # cria um metada simples apenas com o nome do documento
            metadatas = list()
            for i in range(len(document_chunks)):
                metadatas.append({ "documento": image_path, "chunk": i, "CCI": i  })
           
            if self.__data_base is None:
                if self.__in_memory:
                    self.__data_base = DocArrayInMemorySearch.from_texts(collection_name="comunicados-sicoob", texts=document_chunks, embedding=self.__embedding_function, metadatas=metadatas)
                else:
                    self.__chroma_db = Chroma.from_texts(collection_name="comunicados-sicoob", texts=document_chunks, embedding=self.__embedding_function, metadatas=metadatas)
            else:
                if self.__in_memory:
                    self.__data_base.add_texts(document_chunks, metadatas=metadatas)
                else:
                    self.__chroma_db.add_texts(document_chunks, metadatas=metadatas)
    
    def __converter_texto_para_chunks(self, texto_arquivo: str) -> List[str]:
        return self.__text_splitter.split_text(texto_arquivo)
    
    async def obter_contexto_relevante(self, question: str, top_k: int = 2) -> List[Document]:
        if self.__in_memory:
            relevant_context = await self.__data_base.asimilarity_search_with_score(question, top_k)
        else:
            relevant_context = self.__retriever.invoke(question, k=top_k)
        return relevant_context

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