from langchain_community.document_loaders import PyPDFLoader, UnstructuredExcelLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import CharacterTextSplitter
from typing import List
from langchain_core.documents import Document
from langchain_community.llms.ollama import Ollama
from pandasai import SmartDataframe
import pandas as pd
# import excel2img
from rich import print
import pandasai as pai
import langchain
import gc

db = None

pdf_file_path = (
    "./files/comprovante.pdf"
)

word_file_path = (
    "./files/AtivoProblematico.docx"
)

excel_file_path = (
    "../files/outros/analise_excel.xlsx"
)

def load_pdf(file_path: str, text_splitter: CharacterTextSplitter, extract_images=True) -> List[Document]:
    loader = PyPDFLoader(file_path, extract_images=extract_images)
    
    return loader.load_and_split(text_splitter)

def load_docx(file_path: str, text_splitter: CharacterTextSplitter) -> List[Document]:
    loader = UnstructuredWordDocumentLoader(file_path, mode="elements")
    return loader.load_and_split(text_splitter)

def load_xlsx2():
    print('1')
    # excel2img.export_img("./files/AnaliseCCF.xlsx","AnaliseCCFTratamentos.png","Tratamentos")

def load_xlsx(file_path: str, text_splitter: CharacterTextSplitter) -> List[Document]:
    loader = UnstructuredExcelLoader(file_path, mode="elements")
    return loader.load_and_split(text_splitter)

def extrair_xlsx() -> None:
    text_splitter = CharacterTextSplitter(chunk_size=5000, chunk_overlap=100)
    docs = load_xlsx(excel_file_path, text_splitter)
    # print(docs)
    # grava somente as tabelas
    for doc in docs:
        with open(F"{doc.metadata['page_name'].replace(' ', '_')}_{doc.metadata['page_number']}.html", 'w', encoding='UTF-8') as file:
            if 'text_as_html' in doc.metadata.keys():
                file.write(doc.metadata['text_as_html'])
            # else:
                # file.write('\n'.join(doc.page_content))
        
    
def extrair_docs() -> None:
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = load_docx(word_file_path, text_splitter)
    print(docs[0])
    with open('AtivoProblematico.html', 'w', encoding='UTF-8') as file:
        for doc in docs:
            if 'text_as_html' in doc.metadata.keys():
                file.write(doc.metadata['text_as_html'])
            else:
                file.write(doc.page_content)

def extrair_pdfs() -> None:
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = load_pdf(pdf_file_path, text_splitter, True)
    with open('comprovante_com_ocr.txt', 'w', encoding='UTF-8') as file:
        for doc in docs:
            file.write(doc.page_content)
    docs = load_pdf(pdf_file_path, text_splitter, False)
    with open('comprovante_sem_ocr.txt', 'w', encoding='UTF-8') as file:
        for doc in docs:
            file.write(doc.page_content)

def chat_pandas_ai():
    # Get-Process ollama* | Sort-Object -Property CPU -Descending | Select-Object -First 10
    llm = Ollama(model="gemma2:2b-instruct-q4_K_M", temperature= 0, top_k=20, top_p=4, keep_alive=0, num_predict=1234477)
    data_list = pd.read_html('Caso_PF_2.html', header=0, encoding="utf-8") # essa porra vem com números nas colunas
    data_frame = SmartDataframe(df=data_list[0], config={"llm": llm, "custom_whitelisted_dependencies": ["any_module"], "encoding": "utf-8", "verbose": True, "enforce_privacy": True, "is_conversational_answer": False, "enable_cache": False}, name="Casos Pessoa Física")
    output = data_frame.chat(query="What is the minimum, maximum and range CCF?")
    print(f"Resposta PANDAS AI com OLLAMA:\n{output}")
    # import sys; sys.exit(0)


# This is a utility method to convert message to prompt that are understood by
# the Llama 2 model
def build_llama2_prompt(messages):
    start_prompt = "<s>[INST] "
    end_prompt = " [/INST]"
    conversation = []
    for index, message in enumerate(messages):
        if message["role"] == "system" and index == 0:
            conversation.append(f"<<SYS>>\n{message['content']}\n<</SYS>>\n\n")
        elif message["role"] == "user":
            conversation.append(message["content"].strip())
        else:
            conversation.append(f" [/INST] {message['content'].strip()}</s><s>[INST] ")

    return start_prompt + "".join(conversation) + end_prompt
 
def chat_pandas_ai_excel():
<<<<<<< HEAD
    llm = Ollama(model="gemma2:2b-instruct-q4_K_M", temperature=0, top_k=20, top_p=4, keep_alive='1h', num_predict=1234477)
    data_frame = SmartDataframe(df="../files/outros/analise_excel.xlsx", config={"llm": llm, "custom_whitelisted_dependencies": ["any_module"], "encoding": "utf-8", "verbose": True, "enforce_privacy": True, "is_conversational_answer": False, "enable_cache": False}, name="Casos Pessoa Física")
    output = data_frame.chat(query="Witch is the minimum and maximum \"quantidade_vendas\" in the dataset?")
=======
    llm = Ollama(
        model="codellama:7b-code", 
        temperature= 0, 
        top_k=40,
        # top_p=0.1,
        keep_alive='1h', 
        num_predict=4096, 
        # repeat_penalty=1.03
    )
    data_frame = SmartDataframe(
        df="../files/outros/analise_excel.xlsx",
        config={
            "llm": llm, 
            "custom_whitelisted_dependencies": ["any_module"], 
            "encoding": "utf-8", 
            "verbose": True, 
            "enforce_privacy": False, 
            "is_conversational_answer": False, 
            "enable_cache": False,
            # "custom_prompts": {"generate_python_code": MyCustomPrompt(dfs=[dfs]), "correct_error": MyCustomErrorPrompt()}
            }, 
        name="Tabela de produtos e vendas")
    output = data_frame.chat(query="How many rows does the data have?", output_type='string')
>>>>>>> 727d7d3 (evolução)
    print(f"Resposta PANDAS AI com OLLAMA:\n{output}")

if __name__ == '__main__':
    gc.collect()
    pai.clear_cache()
    langchain.verbose = True
    # extrair_xlsx()
    chat_pandas_ai_excel()
    