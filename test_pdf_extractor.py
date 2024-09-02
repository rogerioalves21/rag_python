from app.api.extractors.pdf_extractor import PdfExtractor
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from rich import print
from app.config import get_chat_ollama_client
import warnings
warnings.filterwarnings("ignore")
import os

if __name__ == "__main__":
    # extract = PdfExtractor('./files/pdfs/0702763-79.2024.8.07.0014_0005.pdf')
    # documents = extract.extract()
    filename = '0702763-79.2024.8.07.0014_0003.pdf'
    diretorio = 'C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/local_storage/'
    if not diretorio or diretorio.endswith("/"):
        filename = diretorio + filename
    else:
        filename = diretorio + "/" + filename

    folder = os.path.dirname(filename)
    print(folder)
    print(filename)