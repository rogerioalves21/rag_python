from typing import List
import asyncio
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
import argparse
from rag_service import RAGService

# Model
MODEL         = 'tinyllama'
EMBD          = 'nomic-embed-text'

# ANSI escape codes for colors
PINK          = '\033[95m'
CYAN          = '\033[96m'
YELLOW        = '\033[93m'
NEON_GREEN    = '\033[92m'
RESET_COLOR   = '\033[0m'

rag_service   = None
text_splitter = CharacterTextSplitter(chunk_size=400, chunk_overlap=0)
embeddings    = OllamaEmbeddings(model=EMBD)
llm           = ChatOllama(
    model=MODEL,
    temperature=0.0,
    max_length=250,
    top_k=10,
    keep_alive='1h'
)
parser        = StrOutputParser()
chain         = llm | parser
db            = None

async def ollama_chat(pergunta_usuario: str, documentos_relevantes: List[Document], rag_service: RAGService, historico_chat: List):
    historico_chat.append({"role": "user", "content": pergunta_usuario})
    contexto_relevante = []
    for doc in documentos_relevantes:
        contexto_relevante.append(doc[0].page_content)
    contexto_relevante = '\n'.join(contexto_relevante)
    
    user_input_with_context = pergunta_usuario
    if contexto_relevante:
        user_input_with_context = pergunta_usuario + "\n\nCONTEXTO:\n" + contexto_relevante
    historico_chat[-1]["content"] = user_input_with_context
    
    # query = await rag_service.reescrever_query(question)
    # print(query)

    messages = [
        {"role": "system", "content": rag_service.get_system_prompt()},
        *historico_chat
    ]
    ai_msg = rag_service.invoke(messages)
    return ai_msg

async def stream_ollama_chat(pergunta_usuario: str, documentos_relevantes: List[Document], rag_service: RAGService, historico_chat: List) -> None:
    historico_chat.append({"role": "user", "content": pergunta_usuario})
    contexto_relevante = []
    for doc in documentos_relevantes:
        contexto_relevante.append(doc[0].page_content)
    contexto_relevante = '\n'.join(contexto_relevante)
    
    user_input_with_context = pergunta_usuario
    if contexto_relevante:
        user_input_with_context = pergunta_usuario + "\n\nContext:\n" + contexto_relevante
    historico_chat[-1]["content"] = user_input_with_context

    messages = [
        {"role": "system", "content": rag_service.get_system_prompt()},
        *historico_chat
    ]
    for text in rag_service.get_chain().stream(messages):
        print(NEON_GREEN + text + RESET_COLOR, end="", flush=True)

async def main():
    system_prompt = "You are a brazilian helpful assistant that is an expert at extracting information from a given text. Use only the context provided to craft a clear and detailed answer to the given question. Use language detection to ensure you respond in the same language as the user's question. If you don't know the answer, state that you don't know and do not provide unrelated information."
    rag_service = RAGService(embeddings, text_splitter, chain, system_prompt, './files/pdfs/')
    
    print(NEON_GREEN + "Parsing command-line arguments..." + RESET_COLOR)
    parser = argparse.ArgumentParser(description="Ollama Chat")
    parser.add_argument("--model", default=MODEL, help="Ollama model to use (default: llama3.1:8b-instruct-q2_K)")
    
    print(NEON_GREEN + "Inicializando o Ollama API client..." + RESET_COLOR)
        
    print("Iniciando um loop de conversação...")
    historico_chat = []
    while True:
        query = input(YELLOW + "Pergunte sobre os seus documentos (ou digite 'q' para sair): " + RESET_COLOR)
        if query.lower() == 'q':
            break
        historico_chat.clear()
        print(query)
        documentos_relevantes = await rag_service.obter_contexto_relevante(query, 2)
        if documentos_relevantes:
            await stream_ollama_chat(query, documentos_relevantes, rag_service, historico_chat)
        else:
            break

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())