from fastapi import APIRouter, Response
from typing import Any, Union
from app.models import ConversationPayload, ConversationResponse
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import logging
from app.api.services.comunicados_service import ComunicadosService
from app.api.prepdoclib.comunicado_splitter import ComunicadoTextSplitter
from app.config import InformacoesUsuario

MODEL_Q2      = 'gemma2:2b-instruct-q4_K_M'
EMBD          = 'mxbai-embed-large'

text_splitter = ComunicadoTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
embeddings    = OllamaEmbeddings(model=EMBD)

logger        = logging.getLogger(__name__)
router        = APIRouter()

system_prompt = "Use os documentos fornecidos delimitados por aspas triplas para responder às perguntas. Se a resposta não puder ser encontrada nos documentos, escreva “Não consegui encontrar uma resposta”. Procure responder de forma clara e detalhada."
chat_prompt   = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{question}"),
            ("user", "O conxteto é:\n{context}")
        ]
)
llm_streaming = ChatOllama(
    model=MODEL_Q2,
    keep_alive='1h',
    temperature=0.3,
    num_predict=2000
)

rag_service = None# ComunicadosService(embedding_function=embeddings, text_splitter=text_splitter, chain=llm_streaming, chain_qr=None, system_prompt=system_prompt, folder='./files/pdfs/', in_memory=True, chat_prompt=chat_prompt)

def send_message(question: str) -> str:
    return rag_service.invoke(query=question)

# @router.post("/conversation", dependencies=[InformacoesUsuario], response_model=ConversationResponse)
@router.post("/conversation", response_model=ConversationResponse)
def parent(payload: Union[ConversationPayload | None] = None) -> Any:
    __response = send_message(payload.properties.question.description.strip())
    # return Response(content=__response, status_code=200, media_type="text/plain")
    return ConversationResponse(data=__response, success=True)