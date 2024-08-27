from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.utils import cors_origins
from app.api.main import api_router
import os
from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

set_llm_cache(SQLiteCache())

# seta as variáveis local
os.environ.setdefault('API_USERINFO', 'https://api-sisbr-ti.homologacao.com.br/user-info/v2/userinfo')
os.environ.setdefault('CLIENT_ID', 'lid')

# instancia a aplicação
app = FastAPI(
    debug=True,
    title='lid-sisbr-backoffice'
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# habilita o CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# define as rotas
app.include_router(api_router, prefix="/api/v1")