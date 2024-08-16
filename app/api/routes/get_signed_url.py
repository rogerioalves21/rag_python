from fastapi import APIRouter, Depends
from typing import Any, Union
from app.config import InformacoesUsuario
from app.models import SignedUrls, User

router = APIRouter()

@router.get("/get-signed-url", dependencies=[InformacoesUsuario], response_model=SignedUrls)
def get_signed_url(usuario_logado: User | None = InformacoesUsuario, pdf: str | None = None) -> Any:
    print(usuario_logado)
    print(pdf)
    """
    Retorna as urls pré-assinadas
    """
    return SignedUrls(presigned_urls=[f'http://localhost:8000/upload/{pdf}'])