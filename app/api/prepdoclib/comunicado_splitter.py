from typing import Any, List, Literal, Optional, Union
from langchain_text_splitters.base import Language, TextSplitter
import re
from app.api.prepdoclib.textparser import TextParser


def tratar_linhas_texto(document: str) -> str:
    __text = document.replace('.\n', '.\n\n').replace('!\n', '!\n\n').replace('?\n', '?\n\n').replace(':\n',
                                                                                                      ':\n\n').replace(
        ',\n', ', ').replace(';\n', ' ')
    __text = __text.replace('\\s\\n', '')
    __text = __text.replace('  ', ' ')
    return __text

def clean_query(query: str) -> str:
    return clean_text(query)

def clean_text(text: str) -> str:
    __text_parser = TextParser()
    __text = __text_parser.clean_empty_lines_mail_sites(text)
    __clean = re.split(r'\s+|#\s*', __text)
    __text = ' '.join(__clean)
    return __text

class ComunicadoTextSplitter(TextSplitter):
    """ Quebra em partes iguais textos de comunicados """

    def __init__(self, **kwargs: Any):
        super().__init__(add_start_index=False, **kwargs)

    def split_text(self, text: str) -> List[str]:
        """ Implementação do método abstrato da classe TextSplitter """
        __text = f"{text}" # tratar_linhas_texto(text)
        chunks = []
        while len(__text) > 0:
            if len(__text) > self._chunk_size:
                limit = __text.rfind(' ', 0, self._chunk_size)
                if limit == -1:
                    limit = self._chunk_size
                chunks.append(__text[:limit])
                # chunks.append(self.__clean_text(__text[:limit]))
                
                # aqui eu corto o texto. então seu eu cortar com valores a menos isso vira um overlap
                __text = __text[limit - self._chunk_overlap:].strip()
                # __text = self.__clean_text(__text[limit - self._chunk_overlap:]).strip()
            else:
                chunks.append(__text)
                # chunks.append(self.__clean_text(__text))
                break
        return self._merge_splits(chunks, separator='\x0c') # separator="\n\n\n\n")

    @staticmethod
    def __clean_text(text: str) -> str:
        __remover_sites = TextParser()
        __text = __remover_sites.clean_empty_lines_mail_sites(text)
        return clean_text(__text)
