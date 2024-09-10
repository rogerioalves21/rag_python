import ollama

system_message = "You are a Data Analyst and pandas expert. Your goal is to help people generate high quality and robust code."

data_frame = """
<dataframe>
dfs[0]:4x3
produto,preco,quantidade_vendas
Frutas,8.0,5
Salgado,10.0,10
Bolo,25.0,50
</dataframe>
"""

query = """
<dataframe>
dfs[0]:4x3
produto,preco,quantidade_vendas
Frutas,8.0,5
Salgado,10.0,10
Bolo,25.0,50
</dataframe>
```


Update this initial code:
```python
# TODO: import the required dependencies
import pandas as pd

# Write code here

# Declare result var: 
type (must be \"string\"), value must be string. Example: { \"type\": \"string\", \"value\": f\"The highest salary is {highest_salary}.\" }

```


### QUERY
 How many rows does the data have?

Variable `dfs: list[pd.DataFrame]` is already declared.

At the end, declare \"result\" variable as a dictionary of type and value.

Generate python code and return full updated code:
"""
print(query)

for part in ollama.chat(
    model='codellama:7b-code',
    messages=[
      {'role': 'system', 'content': system_message},
      {'role': 'user', 'content': query}
    ],
    stream=True,
    options={"num_predict": 512, "temperature": 0, 'top_p': 0.1, 'stop': ['<EOT>'], }
):print(part['message']['content'], end='', flush=True)

# end with a newline
print()