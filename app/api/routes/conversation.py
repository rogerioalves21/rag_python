from fastapi import APIRouter
from typing import Any, Union
from app.models import ConversationPayload, ConversationResponse
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import logging
from app.api.services.comunicados_service import ComunicadosService
from langchain_text_splitters.spacy import SpacyTextSplitter
import re

MODEL_Q2      = 'mistral:7b-instruct-v0.3-q2_K'
EMBD          = 'mxbai-embed-large'

text_splitter = SpacyTextSplitter(pipeline="pt_core_news_sm")
embeddings    = OllamaEmbeddings(model=EMBD)

logger = logging.getLogger(__name__)
router = APIRouter()

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
    temperature=0.7,
    num_predict=2000
)

rag_service = None# ComunicadosService(embedding_function=embeddings, text_splitter=text_splitter, chain=llm_streaming, chain_qr=None, system_prompt=system_prompt, folder='./files/pdfs/', in_memory=True, chat_prompt=chat_prompt)

def send_message(question: str) -> str:
    return rag_service.invoke(query=question)

@router.post("/conversation")
def parent(payload: Union[ConversationPayload | None] = None) -> Any:
    __response = send_message(payload.properties.question.description.strip())
    return ConversationResponse(data=__response, success=True)