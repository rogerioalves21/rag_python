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

faz_carga = False

env_path = Path('/home/rogerio_rodrigues/python-workspace/rag_python/.env') # C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/.env')
db_path = '/home/rogerio_rodrigues/python-workspace/rag_python/db_weaviate/' # 'C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/db_weaviate/'
load_dotenv(dotenv_path=env_path)

# Best practice: store your credentials in environment variables
weav_url = os.getenv("WEAVIATE_URL")
weav_api_key = os.getenv("WEAVIATE_ADMIN_KEY")

if __name__ == "__main__":
    client = weaviate.WeaviateClient(
        embedded_options=EmbeddedOptions(
            additional_env_vars={
                "ENABLE_MODULES": "backup-filesystem,text2vec-ollama,generative-ollama",
                "BACKUP_FILESYSTEM_PATH": "/tmp/backups",
                "PERSISTENCE_DATA_PATH": db_path,
                "LIMIT_RESOURCES": 'true'
            }
        )
    )
    try:
        client.connect()
        while True:
            query = input("digite 'q' para sair: ")
            if query.lower() == 'q':
                break
    finally:
        client.close()
