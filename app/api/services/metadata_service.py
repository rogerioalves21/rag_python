from typing import Annotated
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

class MetadataService:
    """ classe responsável por gerar metadatas de um documento carregado """
    def __init__(self, documento: Annotated[Document, "lista de documentos carregados"]):
        self.__documento      = documento
        self.__model          = 'qwen2:1.5b-instruct-q4_K_M'
        self.__summary_prompt = "Você é um assistente dedicado a criar resumos de documentos. Sua tarefa é fazer um resumo curto e conciso, sem acrescentar nenhum conhecimento prévio, nota ou sugestão."
        self.__keys_prompt    = "Você é um assistente dedicado a identificar e extrair palavras-chave de um documento. Extraia entre 3 e 5 palavras-chave, pois elas serão utilizadas pela área administrativa para buscar esse mesmo documento futuramente."
        self.__multi_query    = "Você é um assistente dedicado a identificar e criar perguntas com base no texto de um documento. Crie apenas 2 perguntas sobre o conteúdo do documento fornecido."
        
        self.__output      = StrOutputParser()
        self.__llm         = ChatOllama(
            model=self.__model,
            keep_alive='1h',
            temperature=0,
            num_predict=2000
        )
        self.__llm.verbose = True
        self.__chain       = self.__llm | self.__output
        
    def extrair_metadata(self):
        """ Faz a extração/geração dos metadados do documento """
        __resumo         = self.__extrair_resumo()
        self.__documento.metadata['resumo']         = __resumo
        __palavras_chave = self.__extrair_palavras_chave(__resumo)
        self.__documento.metadata['palavras-chave'] = __palavras_chave
        __perguntas      = self.__extrair_perguntas(__resumo)
        self.__documento.metadata['perguntas']      = __perguntas
        return self.__documento
        
    def __extrair_palavras_chave(self, __resumo: str):
        """ chama o llm para extração das palavras chave do documento """
        __chat_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.__keys_prompt),
                ("user", "### Documento ###\n\n{texto}")
            ]
        )
        __messages = __chat_prompt.format_messages(texto=__resumo)
        return self.__chain.invoke(__messages)
    
    def __extrair_perguntas(self, __resumo: str):
        """ chama o llm para extração das perguntassobre o documento """
        __chat_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.__multi_query),
                ("user", "### Documento ###\n\n{texto}")
            ]
        )
        __messages = __chat_prompt.format_messages(texto=__resumo)
        return self.__chain.invoke(__messages)
    
    def __extrair_resumo(self):
        """ chama o llm para resumo do documento """
        __chat_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.__summary_prompt),
                ("user", "O texto é:\n{texto}")
            ]
        )
        __messages = __chat_prompt.format_messages(texto=self.__documento.page_content)
        return self.__chain.invoke(__messages)
