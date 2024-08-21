from typing import Any, List, Literal, Optional, Union
from langchain_text_splitters.base import Language, TextSplitter
import re

cors_origins = [
    "*"
]

def tratar_linhas_texto(document: str) -> str:
    __text = document.replace('.\n','.\n\n').replace('!\n','!\n\n').replace('?\n','?\n\n').replace(':\n',':\n\n').replace(',\n',', ').replace(';\n',' ')
    __text = __text.replace('\\s\\n', '')
    __text = __text.replace('  ', ' ')
    return __text

def clean_query(query: str) -> str:
    return clean_text(query)

def clean_text(text: str) -> str:
    clean = re.split(r'\s+|[#]\s*', text)
    texto_0 = ' '.join(clean) 
    return texto_0#re.sub(r'[\x00-\x1F\x7F-\x9F\x0c]', ' ', texto_0) 
        
class ComunicadoTextSplitter(TextSplitter):
    """ Quebra em partes iguais textos de comunicados """
    def __init__(self, **kwargs: Any):
        super().__init__(add_start_index=False, **kwargs)

    def split_text(self, text: str) -> List[str]:
        """ Implementação do método abstrato da classe TextSplitter """
        __text = tratar_linhas_texto(text)
        chunks = []
        print(f"CHUNK_SIZE: {self._chunk_size}")
        while len(__text) > 0:
            if len(__text) > self._chunk_size:
                limit = __text.rfind(' ', 0, self._chunk_size)
                if limit == -1:  
                    limit = self._chunk_size
                chunks.append(self.__clean_text(__text[:limit]))
                __text = self.__clean_text(__text[limit:]).strip()
                
            else:
                chunks.append(self.__clean_text(__text))
                break
        return self._merge_splits(chunks, separator="\n\n")
    
    def __clean_text(self, text: str) -> str:
        return clean_text(text)