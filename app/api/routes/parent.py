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
from app.utils import ComunicadoTextSplitter

MODEL_Q2      = 'gemma2:2b-instruct-q4_K_M'
EMBD          = 'mxbai-embed-large'

callback      = AsyncIteratorCallbackHandler()
text_splitter = ComunicadoTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
embeddings    = OllamaEmbeddings(model=EMBD)

logger = logging.getLogger(__name__)
router = APIRouter()

system_prompt = "Use os documentos fornecidos delimitados por aspas triplas para responder às perguntas. Se a resposta não puder ser encontrada nos documentos, escreva “Não consegui encontrar uma resposta”. Por fim, escreva de forma clara e concisa em Português."
chat_prompt   = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{question}"),
            ("user", "O conxteto é:\n{context}")
        ]
)
llm_streaming = ChatOllama(
    model=MODEL_Q2,
    keep_alive='1h',
    temperature=0.1,
    num_predict=2000,
    callbacks=[callback]
)
rag_service = None# ComunicadosService(embedding_function=embeddings, text_splitter=text_splitter, chain=llm_streaming, chain_qr=None, system_prompt=system_prompt, folder='./files/pdfs/', in_memory=True, callbacks=[callback], chat_prompt=chat_prompt)

async def send_message(question: str) -> AsyncIterable[str]:
    async def wrap_done(fn: Awaitable, event: asyncio.Event):
        """Wrap an awaitable with a event to signal when it's done or an exception is raised."""
        try:
            await fn
        except Exception as e:
            print(f"Caught exception: {e}")
            raise e
        finally:
            event.set()

    __task = asyncio.create_task(wrap_done(rag_service.agenerate_memory(query=question), callback.done))

    try:
        async for token in callback.aiter():
            yield token
    except Exception as e:
        print(f"Caught exception: {e}")
        raise e
    finally:
        callback.done.set()
    await __task

@router.post("/conversation-parent")
def parent(payload: Union[ConversationPayload | None] = None) -> Any:
    __response = send_message(payload.properties.question.description.strip())
    return StreamingResponse(__response, media_type="text/event-stream")