from typing import List, Union
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
from huggingface_hub import InferenceClient
from langchain_core.prompts import ChatPromptTemplate

# Model
MODEL         = 'tinyllama'
MODEL_Q2      = 'qwen2:1.5b-instruct-fp16'
EMBD          = 'nomic-embed-text'

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
    keep_alive='1h',
    temperature=0.1,
    top_k=10
)
llm_query     = ChatOllama(
    model=MODEL_Q2,
    keep_alive='1h',
    temperature=0,
    top_k=10
)
parser        = StrOutputParser()
chain         = llm | parser
chain_q2      = llm_query

contexto_menor = """
#### Introdução
O Banco Sicoob tem como visão “Ser reconhecido como a principal instituição financeira
propulsora do desenvolvimento econômico e social dos associados das cooperativas do
Sicoob”. A oferta dos produtos e serviços de câmbio e comércio exterior foi idealizada
com vistas a agregar competitividade e visibilidade ao portfólio da instituição ante ao
mercado.

Como parte da solução, o Banco Sicoob disponibilizará a troca de moeda estrangeira para
fins de turismo. As transferências de recursos até US$ 3.000,00 (três mil dólares dos
Estados Unidos) integram parte dessa solução e serão disponibilizadas através de
parceria firmada com a empresa Western Union.

A Circular nº 3.691/2013 do Banco Central do Brasil regulamenta, entre outros assuntos,
as operações de remessa expressa de recursos, limitadas à US$ 3.000,00 ou o
equivalente em outras moedas, eximindo-as de burocracias inerentes às outras
modalidades de operações de câmbio.
"""
"""
#### Propósito
Descrever as regras negociais detalhadamente para possibilitar a operacionalização das
transferências de recursos até US$ 3.000,00.


#### Áreas envolvidas
Para a implantação das funcionalidades descritas nesta especificação definiu-se a
necessidade de participação das áreas:
- GEDEP/SUEST - responsável pela elaboração da especificação negocial e pela
coordenação do projeto câmbio e comércio exterior.
- GEBAN/SUOPE - responsável pela priorização dos desenvolvimentos em pauta e pela
condução das operações.
- Sicoob Confederação - responsável pelo desenvolvimento da infraestrutura,
funcionalidades e integrações, homologação e disponibilização nos canais de
autoatendimento e SISBR.


#### Regras de negócio
As operações de Remessa Expressa de Recursos, alvo desta especificação, podem ser
realizadas exclusivamente por pessoas físicas que possuam endereço no Brasil e
Cadastro de Pessoas Físicas (CPF). O Banco Sicoob optou por disponibilizá-las através de
parceria com a Western Union, líder global no segmento.


Os desenvolvimentos serão realizados no SISBR e incluirão:
- Desenvolver módulo específico para gestão das operações de câmbio, contemplando os
menus câmbio e comércio exterior, remessa expressa de recursos, moeda em espécie e
cartão pré-pago;
- Desenvolver menu para contratação das operações de remessa até US$ 3.000,00 no
canal de autoatendimento Mobile Banking;
- Realizar integração com a Western Union para consumo e transmissão de informações
necessárias para efetivação das operações;
- Realizar integração com o sistema de Conta Corrente para sensibilização das contas
correntes dos cooperados, refletindo na conta convênio da respectiva cooperativa
singular.
"""

def gerar_novas_queries_local(query: str, contexto: str) -> Union[List[str], None]:
    output = None
    messages=[
        {"role": "system", "content": "Você é um assistente dedicado a gerar novas perguntas a partir de uma pergunta base. Crie 1 nova pergunta sem perder o foco da pergunta original que foi passada na roler user."},
        {"role": "user", "content": f"{query}"},
    ]
    # messages = [
    #    ("system", "Você é um assistente dedicado a gerar novas perguntas a partir de uma pergunta base. Crie 1 nova pergunta sem perder o foco da pergunta original que foi passada na roler user."),
    #    ("user", pergunta)
    #]

    output = chain_q2.invoke(messages)
    return output

if __name__ == "__main__":
    pergunta = "Qual é o contexto?"
    # print("LOCAL:\n", gerar_novas_queries_local(pergunta, contexto))
    # import sys; sys.exit(0)
    
    chat_template = ChatPromptTemplate.from_messages(
        [
            ("system", "Você é um assistente brasileiro dedicado a responder perguntas de usuários sobre o conteúdo do CONTEXTO fornecido. Escreva sua resposta em português e de forma curta e sucinta!"),
            ("user", "{pergunta}"),
            ("user", "## CONTEXTO ##\n{contexto}"),
            #("ai", ""),
        ]
    )
    
    messages = chat_template.format_messages(contexto=contexto_menor, pergunta=pergunta)
    print(messages)

    print('\n')
    for text in chain.stream(messages):
        print(NEON_GREEN + text + RESET_COLOR, end="", flush=True)
    print('\n')