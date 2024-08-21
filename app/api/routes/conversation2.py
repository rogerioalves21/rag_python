import asyncio
from typing import AsyncIterable
from fastapi import APIRouter
from typing import Any, Union, List, Awaitable
from app.models import ConversationPayload, User, ConversationResponse
from langchain_ollama import OllamaEmbeddings
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
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
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=3)
embeddings    = OllamaEmbeddings(model=EMBD)
llm           = ChatOllama(
    model=MODEL_Q2,
    keep_alive='1h',
    temperature=0.4,
    num_predict=2000,
)
llm_query     = ChatOllama(
    model=MODEL_Q2,
    keep_alive='1h',
    temperature=0.4,
    top_k=10
)
parser        = StrOutputParser()
chain         = llm | parser
chain_q2      = llm_query | parser 
db            = None

logger = logging.getLogger(__name__)
router = APIRouter()

system_prompt = "Você é um assistente dedicado a responder perguntas de usuários utilizando apenas o conteúdo do CONTEXTO fornecido. Se você não souber a resposta, escreva que a pergunta deve ser reformulada ou que o contexto é insuficiente. Não faça comentários. Escreva seu raciocínio passo a passo para ter certeza de que gerou a resposta correta!"
rag_service   = None # ComunicadosService(embeddings, text_splitter, chain, chain_q2, system_prompt, './files/pdfs/', True)

def extrair_numero_cci(context: str) -> str:
    _splitado = context.split('\n')
    _regexer  = re.compile(fr'(?<=(CCI\s[—|-]\s)).*(?=.$)')
    return ''.join(list(filter(_regexer.findall, _splitado)))

def limpar_texto(t: str) -> str:
    t = t.replace(' \n', '\n').replace('— \n', '— ').replace('—\n', '— ').replace('- \n', '- ').replace('-\n', '- ').replace(') \n', ') ').replace(')\n', ') ').replace('o \n', 'o ').replace('o\n', 'o ').replace('s \n', 's ').replace('s\n', 's ').replace('e \n', 's ').replace('e\n', 'e ').replace('a \n', 'a ').replace('a\n', 'a ').replace('r \n', 'r ').replace('r\n', 'r ').replace('á \n', 'á ').replace('á\n', 'á ').replace('HRESTRITA', '')
    _cleaner = CleanSymbolsProcessor()
    return _cleaner.process_line(t)# .replace('\n', ' '))

def tratar_contexto(relevant_docs: List) -> str:
    __contexto_relevante = ''
    __keys = relevant_docs.keys()
    for chave in __keys:
        __texto               = ''.join((relevant_docs[chave])).replace('HRESTRITAH', '').replace("#RESTRITA#", '').replace('\r\n', '\n\n').replace('#', '').replace('.\n', '.\n\n').replace('.\r\n', '.\n\n').replace(',\n', '.\n\n').replace(',\r\n', '.\n\n')
        __contexto_relevante += f"## Comunicado: {extrair_numero_cci(__texto)}\n\n"     
        __contexto_relevante += limpar_texto(__texto.strip())
        __contexto_relevante += "\n\n\n"
    return __contexto_relevante

async def send_message(question: str, relevant_docs: str) -> AsyncIterable[str]:
    __callback = AsyncIteratorCallbackHandler()
    __llm_streaming           = ChatOllama(
        model=MODEL_Q2,
        keep_alive='1h',
        temperature=0.4,
        num_predict=2000,
        callbacks=[__callback]
    )
    __chat_template = ChatPromptTemplate.from_messages(
        [
            ("system", rag_service.get_system_prompt()),
            ("user", "{question}"),
            ("user", "## CONTEXTO ##\n{contexto_relevante}")
        ]
    )
    __messages = __chat_template.format_messages(question=question, contexto_relevante=relevant_docs)
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
        __llm_streaming.agenerate(messages=[__messages]),
        __callback.done),
    )

    try:
        async for token in __callback.aiter():
            yield token
    except Exception as e:
        print(f"Caught exception: {e}")
        raise e
    finally:
        __callback.done.set()
    await __task

@router.post("/conversation-tinty")
def conversation(payload: Union[ConversationPayload | None] = None) -> Any:
    __response = send_message(payload.properties.question.description.strip())
    return StreamingResponse(__response, media_type="text/event-stream")