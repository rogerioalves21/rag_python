from typing import List, Union, Dict, Any, AsyncIterator
from tqdm import tqdm
import os
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import (
    BaseMessageChunk
)
from image_utils import ImageProcessing
import unicodedata
import re

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
        system_prompt: str,
        folder: str
    ):
        self.__data_base          = None
        self.__embedding_function = embedding_function
        self.__chain              = chain
        self.__system_prompt      = system_prompt
        self.__text_splitter      = text_splitter
        self.__folder             = folder
        self.__img_prc            = ImageProcessing()
        
        self.__obter_conteudo_arquivo()
    
    def invoke(self, messages: List) -> str:
        return self.__chain.invoke(messages)
    
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
                metadatas.append({ "documento": image_path, "chunk": i })
           
            if self.__data_base is None:
                self.__data_base = DocArrayInMemorySearch.from_texts(document_chunks, self.__embedding_function, metadatas=metadatas)
            else:
                self.__data_base.add_texts(document_chunks, metadatas=metadatas)
    
    def __converter_texto_para_chunks(self, texto_arquivo: str) -> List[str]:
        return self.__text_splitter.split_text(texto_arquivo)
    
    async def obter_contexto_relevante(self, question: str, top_k: int = 2) -> List[Document]:
        relevant_context = self.__data_base.similarity_search_with_score(question, top_k)
        return relevant_context

    async def reescrever_query(self, question: str) -> str:
        system_rewrite = """Você é um assistente útil que gera várias consultas de pesquisa com base em uma única consulta de entrada.

Execute a expansão da consulta. Se houver várias maneiras comuns de formular uma pergunta do usuário
ou sinônimos comuns para palavras-chave na pergunta, certifique-se de retornar várias versões
da consulta com as diferentes frases.

Se houver siglas ou palavras com as quais você não está familiarizado, não tente reformulá-las.

Retorne 3 versões diferentes da pergunta."""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_rewrite),
                ("human", "{question}"),
            ]
        )
        model = prompt | self.__chain
        response = model.invoke({"question": question})
        response