from fastapi import APIRouter
from typing import Any, Union
from app.config import InformacoesUsuario
from app.models import CheckDocumentsPayload, User, CheckDocumentsResponse

router = APIRouter()

@router.post("/check_documents", dependencies=[InformacoesUsuario], response_model=CheckDocumentsResponse)
def check_documents(usuario_logado: Union[User | None] = InformacoesUsuario, payload: Union[CheckDocumentsPayload | None] = None) -> Any:
    return CheckDocumentsResponse(
        count=0,
        documents=None
    )