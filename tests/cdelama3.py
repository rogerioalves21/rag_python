from ollama import generate

data_frame = """
<dataframe>
dfs[0]:4x3
produto,preco,quantidade_vendas
Frutas,8.0,5
Salgado,10.0,10
Bolo,25.0,50
</dataframe>


Reescreva este código:
```python
# TODO: importe as dependencias necessárias
import pandas as pd

# Escreva o seu código aqui

# Declare a variável result: 
type (deve ser \"string\"), o valor deve ser string. Exemplo: { \"type\": \"string\", \"value\": f\"O maior salário é {maior_salario}.\" }

```


### Pergunta ###
Qual a maior quantidade_vendas?

A variável `dfs: list[pd.DataFrame]` já está declarada.

Declare no final a variável \"result\" do tipo dicionário e valor.

Escreva o código python atualizado:
"""

prompt = F'''{data_frame}\n\nA variável `dfs: list[pd.DataFrame]` já está declarada. Sabendo disso responda a pergunta.\n\nQual a maior quantidade_vendas?
    """ '''

suffix = """
    return result
"""

for response in generate(
  model='codellama:7b-code',
  prompt=data_frame,
  # suffix=suffix,
  options={
    'num_predict': 128,
    'temperature': 0,
    'top_p': 0.9,
    'top_k': 20,
    'stop': ['<EOT>'],
  },
  stream=True
):print(response['response'], end='', flush=True)

print('')