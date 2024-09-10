from ollama import generate

data_frame = """
<dataframe>
dfs[0]:4x3
produto,preco,quantidade_vendas
Frutas,8.0,5
Salgado,10.0,10
Bolo,25.0,50
</dataframe>
"""

prompt = F'''{data_frame}\n\nA variável `dfs: list[pd.DataFrame]` já está declarada. Sabendo disso responda a pergunta.\n\nQual a maior quantidade_vendas?
    """ '''

suffix = """
    return { \"type\": \"int\", \"value\": result }
"""

for response in generate(
  model='codellama:7b-code',
  prompt=prompt,
  suffix=suffix,
  options={
    'num_predict': 128,
    'temperature': 0,
    'top_k': 20,
    'top_p': 0.9,
    'stop': ['<EOT>'],
    # 'repeat_penalty': 0.6
  },
  stream=True
):print(response['response'], end='', flush=True)

print('')