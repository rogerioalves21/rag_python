import base64
# from rich import print
import ollama

PROMPT_NUM_PROCESSO = """
Encontre e escreva as informações abaixo:
O número do processo.
A data da distribuição ou última distribuição.
O valor da causa.
Nome da parte autora.
CPF ou CPF/MF da parte autora.
Nome do advogado da parte autora.
Órgão julgador.
Comarca.
Pessoas ou Bancos.

Escreva sua resposta no formato
{
    "numero_processo": {numero_processo},
    "data_distribuicao": {data_distribuicao},
    "valor_causa": {valor_causa},
    "nome_parte_autora": {nome_parte_autora},
    "cpf_parte_autora": {cpf_parte_autora},
    "nome_advogado_parte_autora": {nome_advogado_parte_autora},
    "orgao_julgador": {orgao_julgador},
    "comarca": {comarca},
    { "pessoa_banco": [ { "nome_pessoa_banco": {nome_pessoa_banco}, "cpf_cnpj_pessoa_banco": {cpf_cnpj_pessoa_banco} } ]}
}

Escreva "null" para os valores não encontrados.

Utilize o exemplo de número do processo abaixo como referência para sua busca.

**Exemplo de número de processo**

9999999-99.9999.9.99.9999 (Contêm 20 dígitos)

**Exemplo de "CPF ou CPF/MF da parte autora"**

999.999.999-99 ou 999.999.99999 ou 99999999999

Use APENAS o conteúdo da imagem. Pense passo a passo antes de escrever sua resposta.
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
    img_path_00 = 'C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/files/old_to_img/0702763-79.2024.8.07.0014_0010_0.jpeg'
    img_path_01 = 'C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/files/old_to_img/0702763-79.2024.8.07.0014_0010_1.jpeg'
    img_path_02 = 'C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/files/old_to_img/0702763-79.2024.8.07.0014_0010_2.jpeg'
    img_path_03 = 'C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/files/old_to_img/0702763-79.2024.8.07.0014_0010_3.jpeg'
    img_bytes_00 = get_image(img_path_00)
    img_bytes_01 = get_image(img_path_01)
    img_bytes_02 = get_image(img_path_02)
    response = ollama.chat(
        model='minicpm-v:8b-2.6-q5_K_M',
        messages=[
            {
                'role': 'user',
                'content': f"{PROMPT_NUM_PROCESSO}",
                'images': [to_base64(img_path_00), to_base64(img_path_02)]
            },
        ],
        options={"temperature": 0.4, "num_ctx": 4096},
        keep_alive=0,
        stream=False
    )
    print(response['message']['content'])

if __name__ == "__main__":
    main()
    