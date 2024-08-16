from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredExcelLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import DocArrayInMemorySearch
from typing import Any, Union, List
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
import excel2img
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")
db = None

pdf_file_path = (
    "./files/comprovante.pdf"
)

word_file_path = (
    "./files/AtivoProblematico.docx"
)

excel_file_path = (
    "./files/Pilar3.xlsx"
)

def load_pdf(file_path: str, text_splitter: CharacterTextSplitter, extract_images=True) -> List[Document]:
    loader = PyPDFLoader(file_path, extract_images=extract_images)
    return loader.load_and_split(text_splitter)

def load_docx(file_path: str, text_splitter: CharacterTextSplitter) -> List[Document]:
    loader = UnstructuredWordDocumentLoader(file_path, mode="elements")
    return loader.load_and_split(text_splitter)

def load_xlsx2():
    excel2img.export_img("./files/AnaliseCCF.xlsx","AnaliseCCFTratamentos.png","Tratamentos")

def load_xlsx(file_path: str, text_splitter: CharacterTextSplitter) -> List[Document]:
    loader = UnstructuredExcelLoader(file_path, mode="elements")
    return loader.load_and_split(text_splitter)

def extrair_xlsx() -> None:
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = load_xlsx(excel_file_path, text_splitter)
    print(docs[0])
    with open('Pilar3.html', 'w', encoding='UTF-8') as file:
        for doc in docs:
            if 'text_as_html' in doc.metadata.keys():
                file.write(doc.metadata['text_as_html'])
            else:
                file.write('\n'.join(doc.page_content))
            
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

if __name__ == '__main__':
    load_xlsx2()
    # TODO - converter os documentos em markdown. as llms leem facilmente este formato.
    # extrair_pdfs()
    # db = DocArrayInMemorySearch.from_documents(docs, embeddings)