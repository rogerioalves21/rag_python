import weaviate
from weaviate.config import AdditionalConfig, Timeout
import weaviate.classes as wvc
from weaviate.classes.query import MetadataQuery
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
VECTOR_NAME = "sicoob_juridico_vector"

summary_juridico_prompt = "Você é um assistente especialista em processos judiciais. Sua tarefa é fazer um resumo claro e conciso de processos, foque em aspectos como número do processo, valor da causa, valores de dívidas, requerentes, requeridos, datas, as partes, comarca, juiz, fase do proesso, produto ou serviços do Sicoob, CPF ou CNPJ das partes, o que deseja ou pede a parte autora e o objetivo do processo. Não acrescente nenhum conhecimento prévio, nota ou sugestão. Escreva sua resposta em formato JSON.\n\n\n{page_content}"

faz_carga = False

env_path = Path('/home/rogerio_rodrigues/python-workspace/rag_python/.env') # C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/.env')
db_path = '/home/rogerio_rodrigues/python-workspace/rag_python/db_weaviate/' # 'C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/db_weaviate/'
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
    
    client = weaviate.WeaviateClient(
        embedded_options=EmbeddedOptions(
            additional_env_vars={
                "ENABLE_MODULES": "backup-filesystem,text2vec-ollama,generative-ollama",
                "BACKUP_FILESYSTEM_PATH": "/tmp/backups",
                "PERSISTENCE_DATA_PATH": db_path,
                "MODULES_CLIENT_TIMEOUT": "120m"
            }
        ),
        additional_config=AdditionalConfig(
            timeout=Timeout(init=72000, query=72000, insert=72000)  # Values in seconds
        )
    )
    # client = weaviate.connect_to_local(host='127.0.0.1', port=8079, grpc_port=50060)
    try:
        # embd_ollama = get_ollama_embeddings_basic()
        client.connect()
        
        if faz_carga:
            doc_jur_collection = client.collections.create(
                name="Doc_Jur",
                vectorizer_config=[Configure.NamedVectors.text2vec_ollama(
                    name=VECTOR_NAME,
                    source_properties=["page_content", "page", "resumo", "source"],
                    api_endpoint="http://localhost:11434",
                    model=CONFIG_EMBDBERT,
                )],
                generative_config=Configure.Generative.ollama(
                    api_endpoint="http://localhost:11434",
                    model=MODEL_GEMMA
                ),
                
            )
        doc_jur_collection = client.collections.get(name="Doc_Jur")
        
        if faz_carga:
            with doc_jur_collection.batch.dynamic() as batch:
                for __doc in __documents:
                    __weaviate_obj = {
                        "source": __doc.metadata["source"],
                        "page": __doc.metadata["page"],
                        "page_content": __doc.page_content,
                        "resumo": __doc.metadata["resumo"]
                    }

                    # _embds = await embd_ollama.aembed_documents([__doc.page_content])
                    # print(_embds)
                    
                    batch.add_object(
                        properties=__weaviate_obj,
                        # vector=_embds[0]
                    )
        
        response = doc_jur_collection.generate.near_text(
            query="Qual o valor da causa descrita no processo?",
            limit=3,
            # return_properties=["page_content"],
            target_vector=VECTOR_NAME,
            return_metadata=MetadataQuery(score=True, distance=True, is_consistent=True, explain_score=True),
            single_prompt=summary_juridico_prompt,
            grouped_task=summary_juridico_prompt,
            # return_metadata=MetadataQuery(score=True)
        )
        
        print(response)

        # for o in response.objects:
        #    print(o.properties)
    except Exception as excecao:
        print(excecao)
        # print(client.batch.failed_objects)
        # print(doc_jur_collection.batch.failed_objects)
    finally:
        print('fim')
        # print(client.batch.failed_objects)
        # print(doc_jur_collection.batch.failed_objects)
        client.close()  # Close client gracefully

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
