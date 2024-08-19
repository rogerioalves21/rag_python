from fastapi import APIRouter
from typing import Any, Union, List
from app.models import ConversationPayload, User, ConversationResponse
from langchain_ollama import OllamaEmbeddings
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document
import logging
from app.api.services.comunicados_service import ComunicadosService
import re

MODEL         = 'tinyllama'
MODEL_Q2      = 'qwen2:0.5b-instruct-fp16'
EMBD          = 'nomic-embed-text'

rag_service   = None
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=3)
embeddings    = OllamaEmbeddings(model=EMBD)
llm           = ChatOllama(
    model=MODEL_Q2,
    keep_alive='1h',
    temperature=0,
    verbose=True,
    top_k=10,
    num_predict=250,
)
llm_query     = ChatOllama(
    model=MODEL_Q2,
    keep_alive='1h',
    temperature=0.4,
    top_k=10
)
parser        = StrOutputParser()
chain         = llm | parser
chain_q2      = llm_query | parser 
db            = None

logger = logging.getLogger(__name__)
router = APIRouter()

system_prompt = "Você é um assistente especialista em responder perguntas utilizando apenas o conteúdo do CONTEXTO fornecido, não utilize seu conhecimento prévio. Se você não souber a resposta, escreva que a pergunta deve ser reformulada ou que o contexto é insuficiente. Não faça comentários nem notas."
rag_service   = ComunicadosService(embeddings, text_splitter, chain, chain_q2, system_prompt, './files/pdfs/', True)

history_placeholder = MessagesPlaceholder("chat_history", optional=True)
history_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

lista_historico = []

def extrair_numero_cci(context: str) -> str:
    print(context)
    splitado = context.split('\n')
    regexer  = re.compile(fr'(?<=(CCI\s-\s)).*(?=.$)')
    return ''.join(list(filter(regexer.findall, splitado)))

def chat(question: str, relevant_docs: List) -> AIMessage:
    contexto_relevante = ''
    keys = relevant_docs.keys()
    for chave in keys:
        ''.join((relevant_docs[chave]))
        texto               = ''.join((relevant_docs[chave])).replace("#RESTRITA#", '').replace('\r\n', '\n\n').replace('#', '').replace('.\n', '.\n\n').replace('.\r\n', '.\n\n').replace(',\n', '.\n\n').replace(',\r\n', '.\n\n')
        contexto_relevante += f"## Comunicado: {extrair_numero_cci(texto)}\n\n"     
        contexto_relevante += texto.strip()
        contexto_relevante += "\n\n"
    with open('ccis_contexto.txt', 'w+', encoding='utf-8') as file:
        file.write(contexto_relevante)
    chat_template     = ChatPromptTemplate.from_messages(
        [
            ("system", rag_service.get_system_prompt()),
            # MessagesPlaceholder("chat_history", optional=True),
            ("user", "{question}"),
            ("user", "## CONTEXTO ##\n{contexto_relevante}")
        ]
    )
    messages = chat_template.format_messages(contexto_relevante=contexto_relevante, question=question)
    ai_msg   = rag_service.invoke(messages)
    return ai_msg, contexto_relevante

@router.post("/conversation", response_model=ConversationResponse)
async def conversation(payload: Union[ConversationPayload | None] = None) -> Any:
    relevant_docs = rag_service.obter_contexto_relevante(payload.properties.question.description.strip(), 10)
    sources = dict()
    for doc in relevant_docs:
        sources[doc.metadata['source']] = list()
    for doc in relevant_docs:
        if len(sources[doc.metadata['source']]) < 1:
            sources[doc.metadata['source']].append(doc.page_content)
    response, contexto_relevante = chat(payload.properties.question.description.strip(), sources)
    
    lista_historico.apeend(history_placeholder.format_messages(
        history=[
            ("system", history_prompt),
            ("human", f"## CONTEXTO ##\n{contexto_relevante}"),
            ("human", payload.properties.question.description.strip()),
        ]
    ))
    return ConversationResponse(
        data=response, success=True
    )
