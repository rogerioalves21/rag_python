from fastapi import APIRouter
from typing import Any, Union, List
from app.models import ConversationPayload, User, ConversationResponse
from langchain_ollama import OllamaEmbeddings
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
import logging

gemma_model = 'gemma:2b'
llama_model = 'llama3.1:8b-instruct-q2_K'

logger = logging.getLogger(__name__)
router = APIRouter()
embeddings = OllamaEmbeddings(model="nomic-embed-text:latest", show_progress=True)
llm = ChatOllama(
    model=llama_model,
    temperature=0.0,
)

text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=0)
parser = StrOutputParser()

chain = llm | parser

def gen_embd(question: str, context: str) -> List[Document]:
    docs = text_splitter.split_text(context)
    db = DocArrayInMemorySearch.from_texts(docs, embeddings)
    relevant_docs = db.similarity_search_with_score(question, 3)
    return relevant_docs

def chat(question: str, relevant_docs) -> AIMessage:
    context = []
    for doc in relevant_docs:
        context.append(doc['content'])
    messages = [
        ("system", "Você é um assistente dedicado a responder perguntas de usuários sobre o conteúdo do contexto que foi passado na role user, se o contexto não foi informado ou está vazio, responda que o contexto não foi informado ainda e que é necessário realizar o upload de um arquivo de contexto para continuar a conversação."),
        ("user", f"contexto: {'\n'.join(context)}"),
        ("user", question)
    ]
    ai_msg = chain.invoke(messages)
    return ai_msg

@router.post("/conversation", response_model=ConversationResponse)
def conversation(payload: Union[ConversationPayload | None] = None) -> Any:
    relevant_docs = gen_embd(payload.properties.question.description.strip(), payload.properties.service.description.strip())
    output = []
    for doc in relevant_docs:
        (page_content) = doc[0]
        output.append({"content": page_content.page_content, "score": doc[1]})
    response = chat(payload.properties.question.description.strip(), output)
    return ConversationResponse(
        data=response, success=True
    )