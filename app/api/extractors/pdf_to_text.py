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

    def extrair_texto(self, diretorio: str) -> Documento:
        if not os.path.isdir(diretorio): raise RuntimeError(f"O diretório informado não existe! -> {diretorio}")
        
        is_windows = os.name == 'nt'
        if is_windows: raise RuntimeError("pdftotext não existe no windows!")

        if shutil.which('pdftotext'):
            cmd = ["pdftotext", "-layout", "-nodiag", "-enc", "UTF-8", "-colspacing", "0.3"]
            cmd += [diretorio, "-"]
            out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
            return Documento(conteudo=out.decode('utf-8'))
        else:
            raise EnvironmentError("pdftotext não instalado!")


if __name__ == "__main__":
    # print(os.name)
    pdftotext = PdfToTextExtrator()
    texto = pdftotext.extrair_texto('C:/users//rogerio.rodrigues/workspace-python/rag_python/files/old_pdfs/CCI500_2023.pdf')
    print(texto)