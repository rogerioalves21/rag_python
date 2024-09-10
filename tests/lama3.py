import ollama
from langchain_community.llms.ollama import Ollama
import pandas as pd
from openpyxl import load_workbook
from rich import print

system_message = "Você é um analista de dados e especialista em pandas que escreve em português. Seu objetivo é ajudar as pessoas a gerar código robusto e de alta qualidade."
system_message_excel = "Você é um dedicado analista de dados, especialista em tabelas, excel, relatórios e planilhas. Seu objetivo é ajudar as pessoas fazendo análises detalhadas, insights robustos e sugestões de análises específicas para informações relevantes sobre os dados do dataframe."

def build_llama_prompt(data_frame: str) -> str:
  return F"""
<dataframe>
{data_frame}
</dataframe>
"""
df = pd.read_excel(
  "./files/outros/intercredis_remessa_expressa.xlsx",
  header=None,
  index_col=False,
  keep_default_na=False,
  sheet_name=[0, 1, 2, 3, 4, 5, 6, 7],
  date_format="DD/MM/YYYY HH:MM:SS",
  parse_dates=True,
  #na_values=['-'],
  verbose=False,
  na_filter=False,
  # decimal="{:0.2f}".format
)

print(df[6].round(4).to_csv(compression='infer', index=False, encoding="UTF-8", sep=";"))

import sys; sys.exit(0)

# # data_frame=df[3].to_markdown(index=False))

query = F"""
{build_llama_prompt(data_frame=df[6].to_csv(index=False, encoding="UTF-8", sep=";"))}

Verifique a estrutura do dataframe, altere o que for necessário para torna-la mais legível, remova textos como \"Unnamed\", \"null\" e informações que pareçam ser marcações de dados vazios ou nulos.
Escreva SOMENTE o dataframe reestruturado no formato MARKDOWN e verifique se o mesmo está legível.
Por fim retorne APENAS a análise e insighs detalhados sobre o dataframe. Responda em português.

"""
query = F"""
{build_llama_prompt(data_frame=df[6].to_csv(index=False, encoding="UTF-8"))}

Com base no conjunto de dados fornecido, analise e apresente de 3 a 5 observações, destaques ou tendências mais interessantes.
Isto pode incluir a identificação de segmentos (por exemplo, datas, valores, empresas, taxas, reclamações, etc.) com maior probabilidade de responder de uma determinada forma,
padrões significativos ou insights inesperados dos dados.

Sua análise deve ser detalhada e criteriosa, concentrando-se nos aspectos mais atraentes do conjunto de dados.
Forneça um resumo claro e conciso que destaque as principais conclusões, garantindo que as tendências ou observações sejam apresentadas de forma envolvente e informativa.

Certifique-se de que sua resposta incentive a criatividade e a originalidade na identificação e apresentação dos insights mais atraentes do conjunto de dados, mantendo a precisão e a relevância.

Responda em português.

"""
print(query)


for part in ollama.chat(
    model='qwen2',
    messages=[
      {'role': 'system', 'content': system_message_excel},
      {'role': 'user', 'content': query}
    ],
    stream=True,
    options={"num_predict": 1024, "temperature": 0.3, 'top_p': 0.1 }
):print(part['message']['content'], end='', flush=True)

# end with a newline
print()
import sys; sys.exit(0)

import sys; sys.exit(0)


data_frame = """
<dataframe>
dfs[0]:4x3
produto,preco,quantidade_vendas
Frutas,8.0,5
Salgado,10.0,10
Bolo,25.0,50
</dataframe>
"""

query = F"""
{data_frame}\n\n\nFaça uma análise do dataframe. Explique a sua resposta em português.
"""
print(query)

for part in ollama.generate(
    model='llama3:8b-instruct-q2_K',
    messages=[
      {'role': 'system', 'content': system_message_excel},
      {'role': 'user', 'content': query}
    ],
    stream=True,
    options={"num_predict": 512, "temperature": 0, 'top_p': 0.1, 'stop': ['<EOT>'], }
):print(part['message']['content'], end='', flush=True)

# end with a newline
print()