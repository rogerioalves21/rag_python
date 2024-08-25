import requests
from typing import Union
from fastapi import Depends, Header, HTTPException, status
from typing_extensions import Annotated
from app.models import User
import os
import logging
from app.api.services.comunicados_service import ComunicadosService

logger = logging.getLogger(__name__)

# VARIÁVEIS PARA VALIDAÇÃO DO TOKEN RHSSO
api_userinfo = 'https://api-sisbr-ti.homologacao.com.br/user-info/v2/userinfo'
client_id = 'lid'

def get_rag_service() -> Union[ComunicadosService, None]:
    return None

def create_user(payload: str) -> User:
    return User(
        cpfCnpj=payload['cpfCnpj'],
        cooperativa=str(payload['cooperativa']),
        descricao=str(payload['descricao']),
        email=str(payload['email']),
        login=str(payload['login']),
        instituicaoOrigem=str(payload['instituicaoOrigem'])
    )

def get_dados_usuario(token: str) -> User:
    try:
        logger.info(f'JWT\n{token}')
        headers = {
            'Authorization': f'Bearer {token}',
            'accept': '*/*',
            'client_id': client_id,
            'Content-Type': 'application/json'
        }
        response = requests.get(api_userinfo, headers=headers, verify=False)
        if response.status_code == 200:
            payload = response.json()
            logger.info(payload)
            return create_user(payload)
        raise Exception(response.json())
    except Exception as excecao:
        logger.error('\nERRO AO AUTENTICAR O USUÁRIO\n')
        logger.error('ERRO\n', str(excecao))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Erro inesperado ao tentar obter os dados do usuário logado -> user-info-api',
        )

def do_login(X_JWT_Assertion: Annotated[Union[str, None], Header()] = None) -> User:
    logger.info('do_login')
    if X_JWT_Assertion is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
        )
    return get_dados_usuario(X_JWT_Assertion)

InformacoesUsuario: User | None = Depends(do_login)