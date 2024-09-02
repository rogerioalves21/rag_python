import weaviate
import weaviate.classes as wvc
import os
import requests
import json
from rich import print
from typing import Union
from langchain_ollama import ChatOllama, OllamaEmbeddings
from dotenv import load_dotenv
from pathlib import Path
from weaviate.classes.config import Configure
from weaviate.embedded import EmbeddedOptions
from app.api.extractors.pdf_extractor import PdfExtractor
from app.api.services.metadata_service import MetadataService
import asyncio
import sys

CONFIG_EMBDBERT = 'paraphrase-multilingual'
CONFIG_EMBD  = 'mxbai-embed-large'
MODEL_MISTRAL = 'mistral:7b-instruct-v0.3-q2_K'
MODEL_LLAMA  = 'qwen2:1.5b-instruct-q4_K_M'
MODEL_GEMMA  = 'gemma2:2b-instruct-q4_K_M'

env_path = Path('C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/.env')
db_path = 'C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/db_weaviate/'
load_dotenv(dotenv_path=env_path)

# Best practice: store your credentials in environment variables
weav_url = os.getenv("WEAVIATE_URL")
weav_api_key = os.getenv("WEAVIATE_ADMIN_KEY")

def get_ollama_embeddings_basic() -> Union[OllamaEmbeddings, None]:
    """ LLM para embeddings """
    print(f"Criando o OllamaEmbeddings Basic")
    __embed = OllamaEmbeddings(model=CONFIG_EMBDBERT)
    print(__embed)
    return __embed

async def main():
    __loader    = PdfExtractor('', '', MetadataService())
    __documents = await __loader.extract_all()
    
    with await weaviate. (host="localhost", port=8080, grpc_port=50051) as client:
        client.is_ready()
        print("upa")
        try:
            embd_ollama = get_ollama_embeddings_basic()
            # client.connect()
            """

            doc_jur_collection = client.collections.create(
                name="Doc_Jur",
                vectorizer_config=[Configure.NamedVectors.text2vec_ollama(
                    name="sicoob_juridico_vector",
                    source_properties=["content", "resumo"],
                    api_endpoint="http://127.0.0.1:11434",
                    model=CONFIG_EMBDBERT,
                )],
                generative_config=Configure.Generative.ollama(
                    api_endpoint="http://127.0.0.1:11434/",
                    model="gemma2:2b-instruct-q4_K_M"
                )
            )
            doc_jur_collection = client.collections.get(
                name="Doc_Jur",
                
            )
            with doc_jur_collection.batch.dynamic() as batch:
                for __doc in __documents:
                    __weaviate_obj = {
                        "file": __doc.metadata["source"],
                        "page": __doc.metadata["page"],
                        "content": __doc.page_content,
                        "resumo": __doc.metadata["resumo"]
                    }

                    _embds = await embd_ollama.aembed_documents([__doc.page_content])
                    # print(_embds)
                    
                    batch.add_object(
                        properties=__weaviate_obj,
                        vector=_embds[0]
                    )
                    """
            
        except Exception as excecao:
            print(excecao)
            # print(client.batch.failed_objects)
            # print(doc_jur_collection.batch.failed_objects)
        finally:
            print('fim')
            # print(client.batch.failed_objects)
            # print(doc_jur_collection.batch.failed_objects)
            # client.close()  # Close client gracefully

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
