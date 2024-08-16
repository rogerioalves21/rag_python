from fastapi import APIRouter
from typing import Any, Union
from app.config import InformacoesUsuario
from app.models import UserControlServicePayload, User, UserControlServiceResponse

router = APIRouter()

@router.post("/user_control_service", dependencies=[InformacoesUsuario], response_model=UserControlServiceResponse)
def user_control_service(usuario_logado: Union[User | None] = InformacoesUsuario, payload: Union[UserControlServicePayload | None] = None) -> Any:
    return UserControlServiceResponse(
        message=f"O documento {payload.file_key} foi salvo com sucesso para {usuario_logado.descricao} na feature {payload.service}"
    )