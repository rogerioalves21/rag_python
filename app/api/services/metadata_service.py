from typing import Annotated, List
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_ollama import ChatOllama
from app.api.prepdoclib.comunicado_splitter import clean_text
from app.api.prepdoclib.textparser import TextParser
from langchain.chains.summarize import load_summarize_chain

class MetadataService:
    def __init__(self):
        self.__model          = 'qwen2:1.5b-instruct-q4_K_M'
        self.__summary_prompt = "Você é um assistente dedicado a criar resumos de documentos. Sua tarefa é fazer um resumo claro e conciso, sem acrescentar nenhum conhecimento prévio, nota ou sugestão."
        self.__summary_juridico_prompt = "Você é um assistente especialista em processos judiciais. Sua tarefa é fazer um resumo claro e conciso de processos, foque em aspectos como número do processo, valor da causa, valor da dívida, requerentes, requeridos, as partes e objetivo do processo. Não acrescente nenhum conhecimento prévio, nota ou sugestão."
        self.__keys_prompt    = "Você é um assistente dedicado a identificar e extrair palavras-chave de um documento. Extraia entre 3 e 5 palavras-chave, pois elas serão utilizadas pela área administrativa para buscar esse mesmo documento futuramente."
        self.__multi_query    = "Você é um assistente dedicado a identificar e criar perguntas com base no texto de um documento. Crie apenas 2 perguntas sobre o conteúdo do documento fornecido."

        self.__text_parser = TextParser()
        self.__output      = StrOutputParser()
        self.__llm         = ChatOllama(
            model=self.__model,
            keep_alive='1h',
            temperature=0.2,
            num_predict=2000
        )
        self.__llm.verbose = True
        self.__chain       = self.__llm | self.__output

    def combinar_resumos(self, __documents: List[Document]) -> str:
        """ Faz o map-reduce dos resumos """
        __combine_prompt = """Você é um assistente especialista em processos judiciais.
Você receberá uma série de resumos de um processo judicial. Os resumos serão colocados entre aspas triplas (```).
Seu objetivo é fazer um resumo detalhado,foque em aspectos como número do processo, valor da causa, valor da dívida, requerentes, requeridos, as partes e objetivo do processo.

```{text}```
RESUMO DETALHADO:
        """
        __combine_prompt_template = PromptTemplate(template=__combine_prompt, input_variables=["text"])

        __summary_list = []
        for doc in __documents:
            # Go get a summary of the chunk
            __chunk_summary = doc.metadata['resumo']
            # Append that summary to your list
            __summary_list.append(__chunk_summary)
        __summaries = "\n".join(__summary_list)
        # Convert it back to a document
        __summaries_doc = [Document(page_content=__summaries)]

        __reduce_chain = load_summarize_chain(
            llm=self.__llm,
            chain_type="stuff",
            prompt=__combine_prompt_template,
            verbose=True
        )
        __output = __reduce_chain.run(__summaries_doc)
        print(f"resumo:\n{__output}")
        return __output
    
    def extrair_metadata(self, __documento: Annotated[Document, "lista de documentos carregados"]):
        """ Faz a extração/geração dos metadados do documento """
        __resumo = self.__extrair_resumo(__documento)
        __documento.metadata['resumo'] = __resumo
        # __palavras_chave = self.__extrair_palavras_chave(__resumo)
        # self.__documento.metadata['palavras-chave'] = __palavras_chave
        #__perguntas      = self.__extrair_perguntas(__resumo)
        #self.__documento.metadata['perguntas']      = __perguntas
        return __documento
        
    def __extrair_palavras_chave(self, __resumo: str):
        """ chama o llm para extração das palavras chave do documento """
        __chat_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.__keys_prompt),
                ("user", "### Documento ###\n\n{texto}")
            ]
        )
        __messages = __chat_prompt.format_messages(texto=__resumo)
        return self.__chain.invoke(__messages)
    
    def __extrair_perguntas(self, __resumo: str):
        """ chama o llm para extração das perguntassobre o documento """
        __chat_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.__multi_query),
                ("user", "### Documento ###\n\n{texto}")
            ]
        )
        __messages = __chat_prompt.format_messages(texto=__resumo)
        return self.__chain.invoke(__messages)
    
    def __extrair_resumo(self, __documento: Annotated[Document, "lista de documentos carregados"]):
        """ chama o llm para resumo do documento """
        __chat_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.__summary_juridico_prompt),
                ("user", "O texto é:\n{texto}")
            ]
        )
        __cleaned_text = clean_text(__documento.page_content[:1500])
        __texto = self.__text_parser.parse(__cleaned_text)
        __messages = __chat_prompt.format_messages(texto=__texto)
        return self.__chain.invoke(__messages)
