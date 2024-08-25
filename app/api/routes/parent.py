import asyncio
from typing import AsyncIterable
from fastapi import APIRouter
from typing import Any, Union, Awaitable
from app.models import ConversationPayload
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import logging
from app.api.services.comunicados_service import ComunicadosService
from fastapi.responses import StreamingResponse
from langchain.callbacks import AsyncIteratorCallbackHandler
from rich import print
from app.api.prepdoclib.comunicado_splitter import ComunicadoTextSplitter

MODEL_Q2      = 'gemma2:2b-instruct-q4_K_M'
EMBD          = 'mxbai-embed-large'

text_splitter = ComunicadoTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
embeddings    = OllamaEmbeddings(model=EMBD)

logger = logging.getLogger(__name__)
router = APIRouter()

system_prompt = "Você é um assistente dedicado a responder perguntas utilizando o contexto fornecido. O contexto contêm comunicados (CCI) delimitados por aspas triplas. Se você não souber a resposta, responda que não sabe. Escreva sua resposta SEMPRE em Português."
chat_prompt   = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{question}"),
            ("user", "#### CONTEXTO ####\n\n{context}")
        ]
)
llm_streaming = ChatOllama(
    model=MODEL_Q2,
    keep_alive='1h',
    temperature=0.3,
    num_predict=2000
)
rag_service = ComunicadosService(embedding_function=embeddings, text_splitter=text_splitter, chain=llm_streaming, chain_qr=None, system_prompt=system_prompt, folder='./files/pdfs/', in_memory=True, callbacks=None, chat_prompt=chat_prompt)

async def send_message(question: str) -> AsyncIterable[str]:
    __callback = AsyncIteratorCallbackHandler()
    rag_service.set_callbacks([__callback])
    async def wrap_done(fn: Awaitable, event: asyncio.Event):
        """Wrap an awaitable with a event to signal when it's done or an exception is raised."""
        try:
            await fn
        except Exception as e:
            print(f"Caught exception: {e}")
            raise e
        finally:
            event.set()

    __task = asyncio.create_task(wrap_done(rag_service.agenerate_memory(query=question), __callback.done),)

    try:
        async for token in __callback.aiter():
            yield token
    except Exception as e:
        print(f"Caught exception: {e}")
        raise e
    finally:
        __callback.done.set()
    await __task

@router.post("/conversation-parent")
def parent(payload: Union[ConversationPayload | None] = None) -> Any:
    __response = send_message(payload.properties.question.description.strip())
    return StreamingResponse(__response, media_type="text/event-stream")