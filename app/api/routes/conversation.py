import asyncio
from typing import AsyncIterable
from fastapi import APIRouter
from typing import Any, Union, List, Awaitable
from app.models import ConversationPayload, User, ConversationResponse
from langchain_ollama import OllamaEmbeddings
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.documents import Document
import logging
from app.api.services.comunicados_service import ComunicadosService
from fastapi.responses import StreamingResponse
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.schema import HumanMessage
from clean_symbols import CleanSymbolsProcessor
from langchain_text_splitters.spacy import SpacyTextSplitter
import re

MODEL_Q2      = 'qwen2:1.5b-instruct-q8_0'
EMBD          = 'nomic-embed-text'

text_splitter = SpacyTextSplitter(pipeline="pt_core_news_sm")
embeddings    = OllamaEmbeddings(model=EMBD)
callback      = AsyncIteratorCallbackHandler()

logger = logging.getLogger(__name__)
router = APIRouter()

output_parser = StrOutputParser()

system_prompt = "Você é um assistente dedicado a responder perguntas utilizando apenas o contexto fornecido. Escreva sua resposta em formato Markdown e se ovcê não souber a resposta, escreva que a pergunta deve ser reformulada ou que o contexto é insuficiente."
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

chain = llm_streaming | output_parser

rag_service = ComunicadosService(embedding_function=embeddings, text_splitter=text_splitter, chain=llm_streaming, chain_qr=None, system_prompt=system_prompt, folder='./files/pdfs/', in_memory=False, chat_prompt=chat_prompt)

def send_message(question: str) -> str:
    return rag_service.invoke(query=question)

@router.post("/conversation")
def parent(payload: Union[ConversationPayload | None] = None) -> Any:
    __response = send_message(payload.properties.question.description.strip())
    return ConversationResponse(
        data=__response, success=True
    )