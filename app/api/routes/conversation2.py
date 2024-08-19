import asyncio
from typing import AsyncIterable
from fastapi import APIRouter
from typing import Any, Union, List, Awaitable
from app.models import ConversationPayload, User, ConversationResponse
from langchain_ollama import OllamaEmbeddings
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
import logging
from app.api.services.comunicados_service import ComunicadosService
from fastapi.responses import StreamingResponse
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.schema import HumanMessage
import re

MODEL_Q2      = 'qwen2:0.5b-instruct-fp16'
EMBD          = 'nomic-embed-text'

callback = AsyncIteratorCallbackHandler()

rag_service   = None
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=3)
embeddings    = OllamaEmbeddings(model=EMBD)
llm           = ChatOllama(
    model=MODEL_Q2,
    keep_alive='1h',
    temperature=0.3,
    # top_k=50,
    verbose=True,
    num_predict=2000,
    callbacks=[callback]
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

system_prompt = "Você é um assistente dedicado a responder perguntas de usuários utilizando apenas o conteúdo do CONTEXTO fornecido. Se você não souber a resposta, escreva que a pergunta deve ser reformulada ou que o contexto é insuficiente. Não faça comentários. Escreva seu raciocínio passo a passo para ter certeza de que gerou a resposta correta!"
rag_service   = ComunicadosService(embeddings, text_splitter, chain, chain_q2, system_prompt, './files/pdfs/', True)

async def send_message(question: str, relevant_docs: List) -> AsyncIterable[str]:
    callback = AsyncIteratorCallbackHandler()
    llm_streaming           = ChatOllama(
        model=MODEL_Q2,
        keep_alive='1h',
        temperature=0.7,
        # top_k=50,
        num_predict=2000,
        verbose=True,
        callbacks=[callback]
    )
    contexto_relevante = ''
    keys = relevant_docs.keys()
    for chave in keys:
        # contexto_relevante += f'#### Fonte: {chave}\n\n'
        texto         = ''.join((relevant_docs[chave])).replace("#RESTRITA#", '').replace('\r\n', '\n\n').replace('#', '').replace('.\n', '.\n\n').replace('.\r\n', '.\n\n').replace(',\n', '\n\n').replace(',\r\n', '\n\n')
        contexto_relevante += texto.strip()
        contexto_relevante += "\n\n"
    with open('ccis_contexto.txt', 'w+', encoding='utf-8') as file:
        file.write(contexto_relevante)
    chat_template     = ChatPromptTemplate.from_messages(
        [
            ("system", rag_service.get_system_prompt()),
            ("user", "{question}"),
            ("user",  "### CONTEXTO: {contexto_relevante}"),
        ]
    )
    messages = chat_template.format_messages(question=question, contexto_relevante=contexto_relevante)
    
    async def wrap_done(fn: Awaitable, event: asyncio.Event):
        """Wrap an awaitable with a event to signal when it's done or an exception is raised."""
        try:
            await fn
        except Exception as e:
            # TODO: handle exception
            print(f"Caught exception: {e}")
        finally:
            # Signal the aiter to stop.
            event.set()

    # Begin a task that runs in the background.
    task = asyncio.create_task(wrap_done(
        llm_streaming.agenerate(messages=[messages]),
        callback.done),
    )

    try:
        async for token in callback.aiter():
            yield token
    except Exception as e:
        print(f"Caught exception: {e}")
    finally:
        callback.done.set()

    await task

@router.post("/conversation-tiny")
def conversation(payload: Union[ConversationPayload | None] = None) -> Any:
    relevant_docs = rag_service.obter_contexto_relevante(payload.properties.question.description.strip(), 10)
    sources = dict()
    for doc in relevant_docs:
        sources[doc.metadata['source']] = list()
    for doc in relevant_docs:
        sources[doc.metadata['source']].append(doc.page_content)
    print(sources)
    response = send_message(payload.properties.question.description.strip(), sources)
    return StreamingResponse(response, media_type="text/event-stream")