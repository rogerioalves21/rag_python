import requests
from typing import Union, Tuple
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
import weaviate
from weaviate import WeaviateClient
try:
    from langchain_weaviate.vectorstores import WeaviateVectorStore
except:
    print("sem weaviate")
    WeaviateVectorStore = None
from langchain.storage import InMemoryStore
import functools
from langchain_community.vectorstores import DuckDB
from pymongo import MongoClient

logger = logging.getLogger(__name__)

# VARIÁVEIS PARA VALIDAÇÃO DO TOKEN RHSSO
api_userinfo = 'https://api-sisbr-ti.homologacao.com.br/user-info/v2/userinfo'
client_id    = 'lid'

CONFIG_EMBDBERT = 'gemma2:2b-instruct-q4_K_M' # 'paraphrase-multilingual'
CONFIG_EMBD  = 'gemma2:2b-instruct-q4_K_M' # 'mxbai-embed-large'
MODEL_MISTRAL = 'mistral:7b-instruct-v0.3-q2_K'
MODEL_LLAMA  = 'qwen2:1.5b-instruct-q4_K_M'
MODEL_GEMMA  = 'gemma2:2b-instruct-q4_K_M'

config_system_prompt = "Você é um assistente prestativo do Banco Sicoob, dedicado a responder perguntas utilizando SOMENTE o contexto e resumo fornecidos. Se não for possível encontrar a resposta no contexto, responda \"O contexto fornecido é insuficiente!\". Não utilize conhecimento prévio. Antes de escrever sua resposta final, lembre que a resposta deve ser no idioma português."

@functools.cache
def get_memory_history() -> ConversationBufferMemory:
    """ \nCarrega a memória de conversação\n """
    __memory = ConversationBufferMemory(
        chat_memory=ChatMessageHistory(),
        memory_key='chat_history',
        output_key='answer',
        return_messages=True
    )
    return __memory

def get_text_splitter() -> Union[ComunicadoTextSplitter, None]:
    __splitter = ComunicadoTextSplitter(chunk_size=1000, chunk_overlap=100)
    return __splitter

def get_chat_prompt() -> Union[ChatPromptTemplate, None]:
    __chat_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", config_system_prompt),
            ("user", "#### CONTEXTO ####\n\n{context}### RESUMO ###\n\n{summaries}"),
            ("user", "{question}"),
        ]
    )
    return __chat_prompt

@functools.cache
def get_ollama_embeddings_basic() -> Union[OllamaEmbeddings, None]:
    """ \nLLM para embeddings\n """
    __embed = OllamaEmbeddings(model=CONFIG_EMBD)
    return __embed

@functools.cache
def get_ollama_embeddings() -> Union[OllamaEmbeddings, None]:
    """ \nLLM para embeddings\n """
    __embed = OllamaEmbeddings(model=CONFIG_EMBDBERT)
    return __embed

@functools.cache
def get_duckdb_vector_store_basic() -> Union[DuckDB, None]:
    """ \nCria o vectorstore com DUCKDB\n """
    __vector_store = DuckDB(embedding=get_ollama_embeddings_basic())
    return __vector_store

def get_weaviate_vector_store() -> Union[Tuple[WeaviateVectorStore, WeaviateClient], None]:
    """ \nCria o vectorstore com WEAVIATE\n """
    """__weaviate_client = weaviate.connect_to_local(host='127.0.0.1', port=8079, grpc_port=50060)
    __vector_store = WeaviateVectorStore(client=__weaviate_client, index_name="Doc_Jur", text_key="page_content", embedding=get_ollama_embeddings())
    print(__vector_store)
    return __vector_store, __weaviate_client"""
    return None

# @functools.cache
def get_mongodb_vector_store() -> Union[MongoDBAtlasVectorSearch, None]:
    """ \nCria o vectorstore com duckdb\n """
    try:
        __mongo_client = MongoClient("mongodb+srv://rogerioalves21:cCtExPYYxjDONME9@lidcluster.h0lg3.mongodb.net/?retryWrites=true&w=majority&appName=LidCluster")# "mongodb://localhost:27017/?appname=SicoobLid&directConnection=true&ssl=false")
        __collection = __mongo_client["lid"]["sicoob-collection"]
        __vector_store = MongoDBAtlasVectorSearch(collection=__collection, embedding=get_ollama_embeddings(), index_name="vector_index")
        return __vector_store
    except:
        print("Sem mongo DB")
    return None

@functools.cache
def get_memory_store() -> Union[InMemoryStore, None]:
    """ Cria a store em memória """
    __store = InMemoryStore()
    return __store

@functools.cache
def get_memory_db() -> Union[DocArrayInMemorySearch, None]:
    """ Cria o banco de dados em memória """
    __data_base = DocArrayInMemorySearch.from_params(
        embedding=get_ollama_embeddings(),
        metric="euclidian_dist",
    )
    return __data_base

def get_chat_ollama_client() -> Union[ChatOllama, None]:
    """ Instância do cliente para os LLMs do ollama """
    __llm = ChatOllama(model=MODEL_GEMMA, keep_alive='1h', temperature=0.3, num_predict=2000)
    return __llm

def get_rag_service(
        text_splitter: Annotated[ComunicadoTextSplitter, Depends(get_text_splitter)],
        llm_streaming: Annotated[ChatOllama, Depends(get_chat_ollama_client)],
        chat_prompt: Annotated[ChatPromptTemplate, Depends(get_chat_prompt)],
        memory_history: Annotated[ChatPromptTemplate, Depends(get_memory_history)],
        memory_data_base: Annotated[DocArrayInMemorySearch, Depends(get_memory_db)],
        memory_store: Annotated[InMemoryStore, Depends(get_memory_store)],
        mongodb_vector_storage: Annotated[MongoDBAtlasVectorSearch, Depends(get_mongodb_vector_store)],
        duckdb_vector_storage_basic: Annotated[DuckDB, Depends(get_duckdb_vector_store_basic)],
        embeddings: Annotated[OllamaEmbeddings, Depends(get_ollama_embeddings)],
        weaviate_storage: Annotated[Tuple[WeaviateVectorStore, WeaviateClient], Depends(get_weaviate_vector_store)]
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
        mongodb_vector_storage=mongodb_vector_storage,
        duckdb_vector_storage_basic=duckdb_vector_storage_basic,
        embeddings=embeddings,
        weaviate_storage=weaviate_storage
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