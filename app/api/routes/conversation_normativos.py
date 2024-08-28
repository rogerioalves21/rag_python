from fastapi import APIRouter
from typing import Any, Union
from app.models import ConversationPayload, NormativosResponse, SourceModel
import logging
from app.api.services.comunicados_service import ComunicadosService
from app.config import RagService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/conversation-with-sources", dependencies=[RagService], response_model=NormativosResponse)
def conversation_with_sources(__payload: Union[ConversationPayload | None] = None, __rag_service: ComunicadosService | None = RagService) -> Any:
    __response, __documents = __rag_service.invoke_with_sources(__payload.properties.question.description.strip())

    sources = list()
    for __doc in __documents:
        __name = str(__doc.metadata['source'])
        __name_splited = __name.split('/')
        __name = __name_splited[len(__name_splited) - 1]

        # verifica se já existe na lista a fonte
        exists = False
        for __i in sources:
            if __i.name == __name and __i.page == __doc.metadata['page']:
                exists = True
                break
        if not exists:
            sources.append(SourceModel(name=__name, link=f"https://abcdef.com.br/pdf/{__name}", page=__doc.metadata['page']))
    return NormativosResponse(message=__response, success=True, sources=sources)