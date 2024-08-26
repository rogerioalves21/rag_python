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
from app.config import RagService

logger = logging.getLogger(__name__)
router = APIRouter()

async def send_message(__question: str, __rag_service: ComunicadosService) -> AsyncIterable[str]:
    __callback = AsyncIteratorCallbackHandler()
    __rag_service.set_callbacks([__callback])
    async def wrap_done(fn: Awaitable, event: asyncio.Event):
        """Wrap an awaitable with a event to signal when it's done or an exception is raised."""
        try:
            await fn
        except Exception as e:
            print(f"Caught exception: {e}")
            raise e
        finally:
            event.set()

    __task = asyncio.create_task(wrap_done(__rag_service.agenerate_memory(query=__question), __callback.done),)

    try:
        async for token in __callback.aiter():
            yield token
    except Exception as e:
        print(f"Caught exception: {e}")
        raise e
    finally:
        __callback.done.set()
    await __task

@router.post("/conversation-parent", dependencies=[RagService])
async def parent(__payload: Union[ConversationPayload | None] = None, __rag_service: ComunicadosService | None = RagService) -> Any:
    __response = send_message(__payload.properties.question.description.strip(), __rag_service)
    return StreamingResponse(__response, media_type="text/event-stream")