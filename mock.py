from typing import List
import asyncio
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.prompts import ChatPromptTemplate
import os
import argparse
import json
from rag_service import RAGService

# Model
MODEL         = 'llama3.1:8b-instruct-q2_K'
EMBD          = 'nomic-embed-text:latest'

# ANSI escape codes for colors
PINK          = '\033[95m'
CYAN          = '\033[96m'
YELLOW        = '\033[93m'
NEON_GREEN    = '\033[92m'
RESET_COLOR   = '\033[0m'

rag_service   = None
text_splitter = CharacterTextSplitter(chunk_size=800, chunk_overlap=0)
embeddings    = OllamaEmbeddings(model=EMBD)
llm           = ChatOllama(
    model=MODEL,
    max_tokens=256,
    keep_alive='1h',
    temperature=0.0,
)
parser        = StrOutputParser()
chain         = llm | parser
db            = None

async def main():
    system_prompt         = "Você é um assistente dedicado a responder perguntas de usuários sobre o conteúdo do CONTEXTO fornecido."
    query                 = "Me fale sobre a parceria firmada entre o Banco Sicoob e a empresa Western Union."
    rag_service           = RAGService(embeddings, text_splitter, chain, system_prompt, './files/pdfs/')
    documentos_relevantes = await rag_service.obter_contexto_relevante(query, 2)
    print(documentos_relevantes)
    
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())