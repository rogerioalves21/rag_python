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
from langchain_community.vectorstores import MongoDBAtlasVectorSearch, DocArrayInMemorySearch
from langchain.storage import InMemoryStore
import functools
from langchain_community.vectorstores import DuckDB
from pymongo import MongoClient

logger = logging.getLogger(__name__)

# VARIÁVEIS PARA VALIDAÇÃO DO TOKEN RHSSO
api_userinfo = 'https://api-sisbr-ti.homologacao.com.br/user-info/v2/userinfo'
client_id    = 'lid'

CONFIG_EMBDBERT = 'paraphrase-multilingual'
CONFIG_EMBD  = 'mxbai-embed-large'
MODEL_MISTRAL = 'mistral:7b-instruct-v0.3-q2_K'
MODEL_LLAMA  = 'qwen2:1.5b-instruct-q4_K_M'
MODEL_GEMMA  = 'gemma2:2b-instruct-q4_K_M'

config_system_prompt = "Você é um assistente dedicado a responder perguntas utilizando SOMENTE o contexto fornecido. Se não for possível encontrar a resposta no contexto, responda \"O contexto fornecido é insuficiente!\". Não utilize conhecimento prévio."

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
    __splitter = ComunicadoTextSplitter(chunk_size=400, chunk_overlap=20, length_function=len)
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
def get_mongodb_vector_store() -> Union[MongoDBAtlasVectorSearch, None]:
    """ Cria o vectorstore com duckdb """
    print("Criando o MongoDB")
    __mongo_client = MongoClient("mongodb://localhost:27017/?appname=SicoobLid&directConnection=true&ssl=false")
    __collection = __mongo_client["lid"]["sicoob-collection"]
    print(__mongo_client.list_database_names())
    print(__collection)
    __vector_store = MongoDBAtlasVectorSearch(collection=__collection, embedding=get_ollama_embeddings())
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
    __llm = ChatOllama(model=MODEL_GEMMA, keep_alive='1h', temperature=0.4, num_predict=2000)
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
        duckdb_vector_storage: Annotated[MongoDBAtlasVectorSearch, Depends(get_mongodb_vector_store)],
        duckdb_vector_storage_basic: Annotated[DuckDB, Depends(get_duckdb_vector_store_basic)],
        embeddings: Annotated[OllamaEmbeddings, Depends(get_ollama_embeddings)],
    ) -> Union[ComunicadosService, None]:
    __rag_service = ComunicadosService(
        text_splitter=text_splitter,
        llm=llm_streaming,
        system_prompt=config_system_prompt,
        folder='./files/pdfs/',
        in_memory=False,
        callbacks=None,
        chat_prompt=chat_prompt,
        memory_history=memory_history,
        memory_data_base=memory_data_base,
        store=memory_store,
        duckdb_vector_storage=duckdb_vector_storage,
        duckdb_vector_storage_basic=duckdb_vector_storage_basic,
        embeddings=embeddings
    )
    print(__rag_service)
    return __rag_service

def create_user(token: Union[str, None]) -> User:
    return User(
        cpfCnpj="00875981160",
        cooperativa="0300",
        descricao="Rogério Alves Rodrigues",
        email="rogerioalves21@gmail.com",
        login="rogerio.rodrigues",
        instituicaoOrigem="2")
    """return User(
        cpfCnpj=payload['cpfCnpj'],
        cooperativa=str(payload['cooperativa']),
        descricao=str(payload['descricao']),
        email=str(payload['email']),
        login=str(payload['login']),
        instituicaoOrigem=str(payload['instituicaoOrigem'])
    )"""

def get_dados_usuario(token: Union[str, None]) -> User:
    return create_user(token)
    """try:
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
        )"""

def do_login(X_JWT_Assertion: Annotated[Union[str, None], Header()] = None) -> User:
    logger.info('do_login')
    # if X_JWT_Assertion is None:
    #    raise HTTPException(
    #        status_code=status.HTTP_401_UNAUTHORIZED,
    #        detail="Usuário não autenticado",
    #    )
    return get_dados_usuario(None) # X_JWT_Assertion)

InformacoesUsuario: User | None = Depends(do_login)
RagService: ComunicadosService | None = Depends(get_rag_service)