from fastapi import APIRouter
from typing import Any, Union
from app.models import ConversationPayload
import logging
from fastapi.responses import StreamingResponse
import ollama
from app.api.services.data_analysis_service import DataAnalysisService

logger = logging.getLogger(__name__)
router = APIRouter()

def __fake_data_streamer(__mensagem: str):
    __data_service = DataAnalysisService()
    __query, __propt = __data_service.chat(__mensagem)
    for part in ollama.chat(
        model='qwen2',
        messages=[
            {'role': 'system', 'content': __propt},
            {'role': 'user', 'content': __query}
        ],
        stream=True,
        options={"temperature": 0 }
    ): yield part['message']['content']

@router.post("/data-analysis")
async def chat(__payload: Union[ConversationPayload | None] = None) -> Any:
    return StreamingResponse(
        content=__fake_data_streamer(__payload.properties.question.description.strip()),
        media_type='text/event-stream'
    )
