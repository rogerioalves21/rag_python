import re
from typing import AnyStr


class TextParser:
    """Parser simples de texto."""

    def __init__(self):
        print("text-parser")

    def cleanup_data(self, data: str) -> str:
        """Limpa o conteúdo usando regex
        Args:
            data: (str): O texto para ser limpo.
        Returns:
            str: Texto limpo.
        """
        # combine duas ou mais novas linhas e substitua-as por uma nova linha
        output = re.sub(r"\n{2,}", "\n", data)
        # combine dois ou mais espaços que não sejam novas linhas e substitua-os por um espaço
        output = re.sub(r"[^\S\n]{2,}", " ", output)
        return output.strip()
    
    def parse(self, content: AnyStr) -> AnyStr:
        return self.cleanup_data(content)
