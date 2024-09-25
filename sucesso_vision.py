import base64
# from rich import print
import ollama

PROMPT_NUM_PROCESSO = """
Aplique OCR no texto da imagem. Encontre e escreva as informações abaixo:

O número do processo.
A data da distribuição ou última distribuição.
O valor da causa do processo.
Nome da parte autora da ação ou processo.
Nome do advogado da parte autora da ação ou processo.
Órgão julgador do processo.

Escreva sua resposta no formato
{
    "numero_processo": {numero_processo},
    "data_distribuicao": {data_distribuicao},
    "valor_causa": {valor_causa},
    "nome_parte_autora": {nome_parte_autora},
    "nome_advogado": {nome_advogado},
    "orgao_julgador": {orgao_julgador}
}

Escreva "null" para os valores não encontrados.

Utilize o exemplo de número do processo abaixo como referência para sua busca.

**Exemplo de número de processo**

XXXXXXX-XX.XXXX.X.XX.XXXX (Contêm 20 dígitos)

Pense passo a passo antes de escrever sua resposta.
"""

PROMPT_PARTES = """
Encontre e escreva as informações abaixo:

Nome e CPF/CNPJ de pessoas ou bancos citados no processo.

Escreva sua resposta no formato
{
    "pessoas_bancos": [ "nome_pessoa_banco": {nome_pessoa_banco}, "cpf_cnpj_pessoa_banco": {cpf_cnpj_pessoa_banco} ]
}

Pense passo a passo antes de escrever sua resposta.
"""

PROMPT_DATA_DISTRITUICAO = """
Escreva a data da distribuição ou última distribuição descrita na imagem.
"""

PROMPT_CLASSE_TIPO_PROCESSO = """
Escreva o Tipo de Processo, ou Classe, ou Classe judicial descrito(a) na imagem.
"""

PROMPT_AUTOR = """
Quais são as partes (autor(a), advogado(s), réu(s)) citadas no processo?

Escreva sua resposta no formato abaixo:
```
Partes: [<nome_parte>] // lista com os nomes das partes citadas
```
"""

PROMPT_CPF_CNPJ = """
Escreva os nomes e CPF/CNPJ das partes do processo descritos(as) nas imagens.
"""

def get_image(image_path) -> bytes:
    with open(image_path, 'rb') as file:
        return file.read()

def to_base64(image_path):
    """Getting the base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def main():
    img_path_00 = 'C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/files/old_to_img/0702763-79.2024.8.07.0014_0010_0_GRAY.jpeg'
    
    response = ollama.chat(
        model='minicpm-v:8b-2.6-q5_K_M',
        messages=[
            {
                'role': 'user',
                'content': f"{PROMPT_NUM_PROCESSO}",
                'images': [to_base64(img_path_00)]
            },
        ],
        options={"temperature": 0.7, "num_ctx": 5096},
        keep_alive=0,
        stream=False
    )
    print(response['message']['content'])

if __name__ == "__main__":
    main()
    