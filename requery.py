from typing import Any, Union, List
from langchain_ollama import OllamaEmbeddings
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

# ANSI escape codes for colors
PINK = '\033[95m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
NEON_GREEN = '\033[92m'
RESET_COLOR = '\033[0m'

embeddings    = OllamaEmbeddings(model="nomic-embed-text:latest")
output_parser = StrOutputParser()
llm = ChatOllama(
    model="llama3.1:8b-instruct-q2_K",
    temperature=0.0,
    max_length=250,
    top_k=10,
    keep_alive='1h'
)

retriver      = llm | output_parser
text_splitter = CharacterTextSplitter(chunk_size=400, chunk_overlap=0)
db            = None

def obter_contexto_relevante(question: str, top_k: int = 2) -> List[Document]:
    relevant_context = db.similarity_search_with_score(question, top_k)
    return relevant_context

def ollama_chat(question: str, documentos_relevantes: List[Document], system_message: str, conversation_history: List) -> str:
    conversation_history.append({"role": "user", "content": question})
    contexto_relevante = []
    for doc in documentos_relevantes:
        contexto_relevante.append(doc[0].page_content)
    contexto_relevante = '\n'.join(contexto_relevante)
    
    user_input_with_context = question
    if contexto_relevante:
        user_input_with_context = question + "\n\Context:\n" + contexto_relevante
    conversation_history[-1]["content"] = user_input_with_context
    
    messages = [
        {"role": "system", "content": system_message},
        *conversation_history
    ]
    ai_msg = retriver.invoke(messages)
    return ai_msg

def get_file_contents(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

if __name__ == '__main__':
    document_chunks = text_splitter.split_text(get_file_contents("cci.txt"))
    db              = DocArrayInMemorySearch.from_texts(document_chunks, embeddings)
    
    print("Iniciando o loop de conversação...")
    conversation_history = []
    system_message = "You are a helpful assistant that is an expert at extracting information from a given text. Use only the context provided to craft a clear and detailed answer to the given question. Use language detection to ensure you respond in the same language as the user's question. If you don't know the answer, state that you don't know and do not provide unrelated information."
    while True:
        user_input = input(YELLOW + "Faça uma pergunta sobre os seus documentos ('q' to exit): " + RESET_COLOR)
        if user_input.lower() == 'q':
            break
        conversation_history.clear()
        documentos_relevantes = obter_contexto_relevante(user_input, 2)
        response              = ollama_chat(user_input, documentos_relevantes, system_message, conversation_history)
        print(NEON_GREEN + "Model response:\n\n" + response + RESET_COLOR)
