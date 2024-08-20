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
import re

MODEL         = 'qwen'
MODEL_Q2      = 'qwen2:1.5b-instruct-q8_0'
EMBD          = 'nomic-embed-text'

rag_service   = None
text_splitter = RecursiveCharacterTextSplitter(chunk_size=400)
embeddings    = OllamaEmbeddings(model=EMBD)
callback = AsyncIteratorCallbackHandler()


logger = logging.getLogger(__name__)
router = APIRouter()

system_prompt = "Você é um assistente do Banco Sicoob dedicado a responder perguntas de funcionários utilizando apenas o conteúdo do CONTEXTO fornecido. Escreva sua resposta em formato Markdown e se ovcê não souber a resposta, escreva que a pergunta deve ser reformulada ou que o contexto é insuficiente."
chat_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{question}"),
            ("user", "## CONTEXTO ##\n\n{contexto_relevante}")
        ]
)
llm_streaming = ChatOllama(
    model=MODEL_Q2,
    keep_alive='1h',
    temperature=0,
    top_k=20,
    num_predict=2000,
    verbose=True,
    callbacks=[callback]
)
chain         = llm_streaming
db            = None
rag_service   = ComunicadosService(embeddings, text_splitter, chain, None, system_prompt, './files/pdfs/', False, callbacks=[callback])

def extrair_numero_cci(context: str) -> Union[str, None]:
    __splitado  = context.split('\n')
    __regexer   = re.compile(fr'(?<=(CCI\s[—|-]\s)).*(?=.$)')
    __resultado = list(filter(__regexer.findall, __splitado))
    if __resultado is not None:
        return __resultado[0]
    return None

def limpar_texto(t: str) -> str:
    __t = t.replace(' \n', '\n').replace('— \n', '— ').replace('—\n', '— ').replace('- \n', '- ').replace('-\n', '- ').replace(') \n', ') ').replace(')\n', ') ').replace('o \n', 'o ').replace('o\n', 'o ').replace('s \n', 's ').replace('s\n', 's ').replace('e \n', 's ').replace('e\n', 'e ').replace('a \n', 'a ').replace('a\n', 'a ').replace('r \n', 'r ').replace('r\n', 'r ').replace('á \n', 'á ').replace('á\n', 'á ').replace('HRESTRITA', '')
    _cleaner = CleanSymbolsProcessor()
    return _cleaner.process_line(__t)# .replace('\n', ' '))

def tratar_contexto(relevant_docs: List) -> str:
    __contexto_relevante = ''
    __keys = relevant_docs.keys()
    print(f"CHAVES: {__keys}")
    for chave in __keys:
        __full_doc            = rag_service.get_document_by_source(chave)
        __texto               = __full_doc
        __numero_cci          = extrair_numero_cci(__full_doc)
        __texto               = ''.join(__texto).replace('HRESTRITAH', '').replace("#RESTRITA#", '').replace('\r\n', '\n\n').replace('#', '').replace('.\n', '.\n\n').replace('.\r\n', '.\n\n').replace(',\n', '.\n\n').replace(',\r\n', '.\n\n')
        __contexto_relevante += f"#### Comunicado: {__numero_cci}\n\n"        
        __contexto_relevante += limpar_texto(__texto.strip())
        __contexto_relevante += "\n\n\n"
    return __contexto_relevante

async def send_message(question: str, relevant_docs: str) -> AsyncIterable[str]:
    # __messages = chat_template.format_messages(question=question, contexto_relevante=relevant_docs)
    async def wrap_done(fn: Awaitable, event: asyncio.Event):
        """Wrap an awaitable with a event to signal when it's done or an exception is raised."""
        try:
            await fn
        except Exception as e:
            print(f"Caught exception: {e}")
            raise e
        finally:
            event.set()

    __task = asyncio.create_task(wrap_done(
        rag_service.agenerate(query=question),
        #__llm_streaming.agenerate(messages=[__messages]),
        callback.done),
    )

    try:
        async for token in callback.aiter():
            yield token
    except Exception as e:
        print(f"Caught exception: {e}")
        raise e
    finally:
        callback.done.set()
    await __task

@router.post("/conversation-parent")
def parent(payload: Union[ConversationPayload | None] = None) -> Any:
    __relevant_docs = rag_service.get_contexto_relevante(payload.properties.question.description.strip())
    __sources       = dict()
    for doc in __relevant_docs:
        __sources[doc.metadata['source']] = list(dict())
    for doc in __relevant_docs:
        __sources[doc.metadata['source']].append(doc.page_content)
    __contexto_relevante = tratar_contexto(__sources)
    __response           = send_message(payload.properties.question.description.strip(), __contexto_relevante)
    return StreamingResponse(__response, media_type="text/event-stream")