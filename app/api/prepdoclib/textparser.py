import re
from typing import AnyStr


class TextParser:
    """Parser simples de texto."""
    
    def __clean_empty_lines(self, full_text: str) -> str:
        """ Remove mais de 3 quebras de linhas """
        __full_text = re.sub(r'\n{3,}', '\n\n', full_text)
        __full_text = re.sub(r'(\n\s){3,}', '\n\n', __full_text)
        __full_text = __full_text.replace('\xa0', ' ') # Replace non-breaking spaces
        return __full_text
    
    def clean_empty_lines_mail_sites(self, text: str) -> str:
        # default clean
        # remove invalid symbol
        text = re.sub(r'<\|', '<', text)
        text = re.sub(r'\|>', '>', text)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\xEF\xBF\xBE]', '', text)
        # Unicode  U+FFFE
        text = re.sub('\uFFFE', '', text)

        # Remove extra spaces
        # pattern = r'\n{3,}'
        # text = re.sub(pattern, '\n\n', text)
        # pattern = r'[\t\f\r\x20\u00a0\u1680\u180e\u2000-\u200a\u202f\u205f\u3000]{2,}'
        # text = re.sub(pattern, ' ', text)
            
        # Remove email
        pattern = r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
        text = re.sub(pattern, '', text)

        # Remove URL
        pattern = r'https?://[^\s]+'
        text = re.sub(pattern, '', text)
        return text

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
