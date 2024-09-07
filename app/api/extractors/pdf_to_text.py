# -*- coding: utf-8 -*-
import os
import subprocess
import shutil
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel, Field


class Documento(BaseModel):
    """Classe para textos e metadatas."""

    conteudo: str
    metadata: Optional[dict] = Field(default_factory=dict)


class AbstractExtrator(ABC):
    """Interface para extração de textos.
    """

    @abstractmethod
    def extrair_texto(self) -> Documento:
        raise NotImplementedError


class PdfToTextExtrator(AbstractExtrator):
    """ Extrai texto do PDF no layout mais próximo ao original """

    def extrair_texto(self, _arquivo: str) -> Documento:
        # if not os.path.isfile(_arquivo): raise RuntimeError(f"O arquivo informado não existe! -> {_arquivo}")
        
        # _is_windows = os.name == 'nt'
        # if _is_windows: raise RuntimeError("pdftotext não existe no windows!")

        if shutil.which('pdftotext'):
            _cmd = ["pdftotext", "-layout", "-nodiag", "-enc", "UTF-8", "-colspacing", "0.3"]
            _cmd += [_arquivo, "-"]
            _out, _err = subprocess.Popen(_cmd, stdout=subprocess.PIPE).communicate()
            _conteudo = _out.decode('utf-8')
            #with open('cci.txt', 'w', encoding='utf-8') as f:
            #    f.write(_conteudo)
            _splt = _arquivo.split('/')
            return Documento(conteudo=_conteudo, metadata={"source": _splt[len(_splt) - 1], "page": 0, "resumo": ""})
        else:
            raise EnvironmentError("pdftotext não instalado!")


#if __name__ == "__main__":
#    pdftotext = PdfToTextExtrator()
#    texto = pdftotext.extrair_texto('/home/rogerio_rodrigues/python-workspace/rag_python/files/pdfs/CCI500_2023.pdf')
#    print(texto)