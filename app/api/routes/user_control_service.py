from fastapi import APIRouter
from typing import Any, Union
from app.config import InformacoesUsuario
from app.models import UserControlServicePayload, User, UserControlServiceResponse
from app.storage.local_storage import LocalStorage
from rich import print

router = APIRouter()

# @router.post("/user_control_service", dependencies=[InformacoesUsuario], response_model=UserControlServiceResponse)
# def user_control_service(usuario_logado: Union[User | None] = InformacoesUsuario, payload: Union[UserControlServicePayload | None] = None) -> Any:
@router.post("/user_control_service", response_model=UserControlServiceResponse)
def user_control_service(payload: Union[UserControlServicePayload | None] = None) -> Any:
    print(payload)
    __storage = LocalStorage()
    __storage.save(filename=payload.file_key.replace('.pdf', ''), data=payload.service.encode('utf-8'))
    return UserControlServiceResponse(
        message=f"O documento {payload.file_key} foi salvo com sucesso na feature {payload.service}"
    )