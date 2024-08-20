from typing import List
import asyncio
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.prompts import ChatPromptTemplate
from rag_service import RAGService

# Model
MODEL         = 'llama3.1:8b-instruct-q2_K'
MODEL_Q2      = 'qwen2:0.5b-instruct-fp16'
EMBD          = 'nomic-embed-text:latest'

# ANSI escape codes for colors
PINK          = '\033[95m'
CYAN          = '\033[96m'
YELLOW        = '\033[93m'
NEON_GREEN    = '\033[92m'
RESET_COLOR   = '\033[0m'

rag_service   = None
text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
embeddings    = OllamaEmbeddings(model=EMBD)
llm           = ChatOllama(
    model=MODEL_Q2,
    keep_alive='1h',
    temperature=0.3,
    top_k=50
)
llm_query       = ChatOllama(
    model       = MODEL_Q2,
    keep_alive  = '1h',
    temperature = 0.4,
    top_k       = 10
)
parser        = StrOutputParser()
chain         = llm | parser
chain_q2      = llm_query | parser 
db            = None

async def ollama_chat(question: str, documentos_relevantes: List[Document], rag_service: RAGService, historico_chat: List):
    historico_chat.append({"role": "user", "content": question})
    contexto_relevante = []
    for doc in documentos_relevantes:
        contexto_relevante.append(doc.page_content)
        # contexto_relevante.append(doc[0].page_content)
    contexto_relevante = '\n'.join(contexto_relevante)
    
    # user_input_with_context = question
    # if contexto_relevante:
    #    user_input_with_context = question + "\n\nCONTEXTO:\n" + contexto_relevante
    # historico_chat[-1]["content"] = user_input_with_context

    chat_template = ChatPromptTemplate.from_messages(
        [
            ("system", rag_service.get_system_prompt()),
            ("user", "{question}"),
            ("user", "## CONTEXTO ##\n{contexto_relevante}")
        ]
    )
    messages = chat_template.format_messages(contexto_relevante=contexto_relevante, question=question)
    # messages = [
    #     {"role": "system", "content": rag_service.get_system_prompt()},
    #     *historico_chat
    # ]
    ai_msg = rag_service.invoke(messages)
    return ai_msg

async def stream_ollama_chat(question: str, documentos_relevantes: List[Document], rag_service: RAGService, historico_chat: List) -> None:
    historico_chat.append({"role": "user", "content": question})
    contexto_relevante = []
    for doc in documentos_relevantes:
        contexto_relevante.append(doc[0].page_content)
    contexto_relevante = '\n'.join(contexto_relevante)
    
    # print(PINK + f"\n\n{contexto_relevante}\n\n"  + RESET_COLOR)
    
    # refaz o questionamento do usuário
    # questao_reescrita = rag_service.reescrever_query(question, contexto_relevante)
    # print(PINK + f"\nquestão reescrita:\n {questao_reescrita}\n" + RESET_COLOR)
    
    # if questao_reescrita and len(questao_reescrita) > 0:
    #    question = question + ", " + questao_reescrita
        
    # print(f"\n{question}\n")
        
    # user_input_with_context = question
    # if contexto_relevante:
    #    user_input_with_context = question + "\n\nCONTEXTO:\n" + contexto_relevante
    # historico_chat[-1]["content"] = user_input_with_context

    chat_template = ChatPromptTemplate.from_messages(
        [
            ("system", rag_service.get_system_prompt()),
            ("user", "{question}"),
            ("user", "## CONTEXTO ##\n{contexto_relevante}")
        ]
    )
    messages = chat_template.format_messages(contexto_relevante=contexto_relevante, question=question)

    # messages = [
    #    {"role": "system", "content": rag_service.get_system_prompt()},
    #    *historico_chat
    #]
    print("\n")
    for text in rag_service.get_chain().stream(messages):
        print(NEON_GREEN + text + RESET_COLOR, end="", flush=True)
    print("\n")

async def main():
    system_prompt = "Você é um assistente dedicado a responder perguntas de usuários sobre o conteúdo do CONTEXTO fornecido. Escreva sua resposta de forma sucinta!"
    rag_service   = RAGService(embeddings, text_splitter, chain, chain_q2, system_prompt, './files/pdfs/', True)
    
    # import sys; sys.exit(0)
    
    print(NEON_GREEN + "Inicializando o Ollama API client..." + RESET_COLOR)
        
    print("Iniciando um loop de conversação...")
    historico_chat = []
    while True:
        query = input(YELLOW + "Pergunte sobre os seus documentos (ou digite 'q' para sair): " + RESET_COLOR)
        if query.lower() == 'q':
            break
        historico_chat.clear()
        documentos_relevantes = await rag_service.obter_contexto_relevante(query, 1)
        if documentos_relevantes:
            await stream_ollama_chat(query, documentos_relevantes, rag_service, historico_chat)
        else:
            break

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())