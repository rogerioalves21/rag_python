from fastapi import APIRouter, Response
from typing import Any, Union
from app.models import ConversationPayload, ConversationResponse
import logging
from app.api.services.comunicados_service import ComunicadosService
from app.config import RagService

logger = logging.getLogger(__name__)
router = APIRouter()

def send_message(question: str, __rag_service: ComunicadosService) -> str:
    return __rag_service.invoke(query=question)

# @router.post("/conversation", dependencies=[InformacoesUsuario], response_model=ConversationResponse)
@router.post("/conversation", dependencies=[RagService], response_model=ConversationResponse)
def parent(__payload: Union[ConversationPayload | None] = None, __rag_service: ComunicadosService | None = RagService) -> Any:
    __response = send_message(__payload.properties.question.description.strip(), __rag_service)
    return Response(content=__response, status_code=200, media_type="text/plain")
    # return ConversationResponse(data=__response, success=True)