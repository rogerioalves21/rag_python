from typing import Tuple
import pandas as pd

class DataAnalysisService():
    """ Classe responsável por converter arquivos PDF em Imagens.
        Transforma as mesmas em textos, e inclui em base de dados (memória).
    """
    def __init__(self):
        print('Data Analysis Service')

    def __build_llama_prompt(self, data_frame: str) -> str:
        return F"""
            Conjunto de dados:
            
            <dataframe>
            {data_frame}
            </dataframe>
        """
    
    def chat(self, query: str) -> Tuple[str, str]:
        """ Chamada streaming para o llm. Busca os documentos com mais contexto no ParentDocumentRetriever """

        __system_message_excel = "Você é um dedicado analista de dados, especialista em tabelas, excel, relatórios e planilhas. Seu objetivo é ajudar as pessoas fazendo análises detalhadas, insights robustos e sugestões de análises específicas para informações relevantes sobre os dados do dataframe."
        __df = pd.read_excel(
            "C:/Users/rogerio.rodrigues/documents/workspace_python/rag_python/files/outros/CalculoReembolso.xlsb.xlsx",
            sheet_name=[0],
            date_format="DD/MM/YYYY HH:MM:SS",
            na_values='-',
            verbose=True
        )

        if not query or len(query) == 0:
            return F"""
                {self.__build_llama_prompt(data_frame=__df[0].to_csv(compression='infer', index=False, encoding="UTF-8", sep=";"))}

                Com base no conjunto de dados fornecido, analise e apresente de 1 a 4 observações, destaques, insights ou tendências mais interessantes.

                Sua análise deve ser detalhada e criteriosa, concentrando-se nos aspectos mais atraentes do conjunto de dados.
                Forneça um resumo claro e conciso que destaque as principais conclusões, garantindo que as tendências ou observações sejam apresentadas de forma envolvente e informativa.
                
                Pense passo a passo.
                Use no máximo 100 palavras e responda em português.

                """, __system_message_excel
        else:
            return F"""
                {self.__build_llama_prompt(data_frame=__df[0].to_csv(compression='infer', index=False, encoding="UTF-8", sep=";"))}

                Com base no conjunto de dados fornecido. {query}

                Sua análise deve ser detalhada e criteriosa.
                Use no máximo 100 palavras e responda em português.

                """, __system_message_excel

   