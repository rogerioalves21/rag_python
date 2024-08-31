import requests
from typing import Union
from fastapi import Depends, Header, HTTPException, status
from typing_extensions import Annotated
from app.models import User
import logging
from langchain_core.prompts import ChatPromptTemplate
from app.api.services.comunicados_service import ComunicadosService
from langchain_ollama import ChatOllama, OllamaEmbeddings
from app.api.prepdoclib.comunicado_splitter import ComunicadoTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain.storage import InMemoryStore
import functools
from langchain_community.vectorstores import DuckDB
import duckdb

logger = logging.getLogger(__name__)

# VARIÁVEIS PARA VALIDAÇÃO DO TOKEN RHSSO
api_userinfo = 'https://api-sisbr-ti.homologacao.com.br/user-info/v2/userinfo'
client_id    = 'lid'

CONFIG_EMBDBERT = 'paraphrase-multilingual'
CONFIG_EMBD  = 'mxbai-embed-large'
MODEL_LLAMA  = 'qwen2:1.5b-instruct-q4_K_M'
MODEL_GEMMA  = 'gemma2:2b-instruct-q4_K_M'

config_system_prompt = "Você é um assistente brasileiro dedicado a responder perguntas utilizando o contexto fornecido. Se você não souber a resposta, responda que o contexto é insuficiente para responder a pergunta. Escreva sua resposta no idioma Português."

@functools.cache
def get_memory_history() -> ConversationBufferMemory:
    """ Carrega a memória de conversação """
    print(f"Criando o ConversationBufferMemory")
    __memory = ConversationBufferMemory(
        chat_memory=ChatMessageHistory(),
        memory_key='chat_history',
        output_key='answer',
        return_messages=True
    )
    print(__memory)
    return __memory

def get_text_splitter() -> Union[ComunicadoTextSplitter, None]:
    print(f"Criando o ComunicadoTextSplitter")
    __splitter = ComunicadoTextSplitter(chunk_size=1500, chunk_overlap=500, length_function=len)
    print(__splitter)
    return __splitter

def get_chat_prompt() -> Union[ChatPromptTemplate, None]:
    print(f"Criando o ChatPromptTemplate")
    __chat_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", config_system_prompt),
            ("user", "{question}"),
            ("user", "#### CONTEXTO ####\n\n{context}")
        ]
    )
    print(__chat_prompt)
    return __chat_prompt

@functools.cache
def get_ollama_embeddings_basic() -> Union[OllamaEmbeddings, None]:
    """ LLM para embeddings """
    print(f"Criando o OllamaEmbeddings Basic")
    __embed = OllamaEmbeddings(model=CONFIG_EMBD)
    print(__embed)
    return __embed

@functools.cache
def get_ollama_embeddings() -> Union[OllamaEmbeddings, None]:
    """ LLM para embeddings """
    print(f"Criando o OllamaEmbeddings")
    __embed = OllamaEmbeddings(model=CONFIG_EMBDBERT)
    print(__embed)
    return __embed

@functools.cache
def get_duckdb_vector_store_basic() -> Union[DuckDB, None]:
    """ Cria o vectorstore com duckdb """
    print("Criando o DuckDB Basic")
    __vector_store = DuckDB(embedding=get_ollama_embeddings_basic())
    print(__vector_store)
    return __vector_store

@functools.cache
def get_duckdb_vector_store() -> Union[DuckDB, None]:
    """ Cria o vectorstore com duckdb """
    print("Criando o DuckDB")
    __vector_store = DuckDB(embedding=get_ollama_embeddings())
    print(__vector_store)
    return __vector_store

@functools.cache
def get_memory_store() -> Union[InMemoryStore, None]:
    """ Cria a store em memória """
    __store = InMemoryStore()
    print(__store)
    return __store

@functools.cache
def get_memory_db() -> Union[DocArrayInMemorySearch, None]:
    """ Cria o banco de dados em memória """
    __data_base = DocArrayInMemorySearch.from_params(
        embedding=get_ollama_embeddings(),
        metric="euclidian_dist",
    )
    print(__data_base)
    return __data_base

def get_chat_ollama_client() -> Union[ChatOllama, None]:
    """ Instância do cliente para os LLMs do ollama """
    print(f"Criando o get_chat_ollama_client")
    __llm = ChatOllama(model=MODEL_LLAMA, keep_alive='1h', temperature=0.0, num_predict=2000)
    print("Criando o ChatOllama")
    print(__llm)
    return __llm

def get_rag_service(
        text_splitter: Annotated[ComunicadoTextSplitter, Depends(get_text_splitter)],
        llm_streaming: Annotated[ChatOllama, Depends(get_chat_ollama_client)],
        chat_prompt: Annotated[ChatPromptTemplate, Depends(get_chat_prompt)],
        memory_history: Annotated[ChatPromptTemplate, Depends(get_memory_history)],
        memory_data_base: Annotated[DocArrayInMemorySearch, Depends(get_memory_db)],
        memory_store: Annotated[InMemoryStore, Depends(get_memory_store)],
        duckdb_vector_storage: Annotated[DuckDB, Depends(get_duckdb_vector_store)],
        duckdb_vector_storage_basic: Annotated[DuckDB, Depends(get_duckdb_vector_store_basic)]
    ) -> Union[ComunicadosService, None]:
    __rag_service = ComunicadosService(
        text_splitter=text_splitter,
        chain=llm_streaming,
        system_prompt=config_system_prompt,
        folder='./files/pdfs/',
        in_memory=False,
        callbacks=None,
        chat_prompt=chat_prompt,
        memory_history=memory_history,
        memory_data_base=memory_data_base,
        store=memory_store,
        duckdb_vector_storage=duckdb_vector_storage,
        duckdb_vector_storage_basic=duckdb_vector_storage_basic
    )
    print(__rag_service)
    return __rag_service

def create_user(payload: str) -> User:
    return User(
        cpfCnpj=payload['cpfCnpj'],
        cooperativa=str(payload['cooperativa']),
        descricao=str(payload['descricao']),
        email=str(payload['email']),
        login=str(payload['login']),
        instituicaoOrigem=str(payload['instituicaoOrigem'])
    )

def get_dados_usuario(token: str) -> User:
    try:
        logger.info(f'JWT\n{token}')
        headers = {
            'Authorization': f'Bearer {token}',
            'accept': '*/*',
            'client_id': client_id,
            'Content-Type': 'application/json'
        }
        response = requests.get(api_userinfo, headers=headers, verify=False)
        if response.status_code == 200:
            payload = response.json()
            logger.info(payload)
            return create_user(payload)
        raise Exception(response.json())
    except Exception as excecao:
        logger.error('\nERRO AO AUTENTICAR O USUÁRIO\n')
        logger.error('ERRO\n', str(excecao))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Erro inesperado ao tentar obter os dados do usuário logado -> user-info-api',
        )

def do_login(X_JWT_Assertion: Annotated[Union[str, None], Header()] = None) -> User:
    logger.info('do_login')
    if X_JWT_Assertion is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
        )
    return get_dados_usuario(X_JWT_Assertion)

InformacoesUsuario: User | None = Depends(do_login)
RagService: ComunicadosService | None = Depends(get_rag_service)