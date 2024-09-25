import base64
# from rich import print
import ollama
import codecs
import requests
import json

PROMPT_NUM_PROCESSO = """
Utilizando APEANAS o contexto. Encontre e escreva as informações abaixo:

O número do processo.
A data da distribuição ou última distribuição.
O valor da causa do processo.
Nome da parte autora da ação ou processo.
Nome do advogado da parte autora da ação ou processo.
Órgão julgador do processo.
Juiz, ou qual o nome do Juiz de Direito citado no processo.

Escreva sua resposta no formato
{
    "numero_processo": {numero_processo},
    "data_distribuicao": {data_distribuicao},
    "valor_causa": {valor_causa},
    "nome_parte_autora": {nome_parte_autora},
    "nome_advogado_parte_autora": {nome_advogado_parte_autora},
    "orgao_julgador": {orgao_julgador},
    "nome_juiz_processo": {nome_juiz_processo}
}

Escreva "null" para os valores não encontrados.

Pense passo a passo antes de escrever sua resposta.
"""

headers = {
    "Content-Type": "application/json"
}
jan_ai_url = "http://localhost:1337"

def sumarizar_processos(pagina: str):
    try:
        summary_juridico_prompt = "Você é um assistente especialista em processos judiciais. Sua tarefa é fazer um resumo claro e conciso de processos, foque em aspectos como número do processo, valor da causa, valor da dívida, requerentes, requeridos, as partes e objetivo do processo. Não acrescente nenhum conhecimento prévio, nota ou sugestão. Escreva suas respostas no formato markdown."
        payload = {
            "messages": [
                {
                    "content": summary_juridico_prompt,
                    "role": "system"
                },
                {
                    "content": pagina,
                    "role": "user"
                }
            ],
            "model": "phi3-3.8b",
            "stream": False,
            "max_tokens": 4096,
            "frequency_penalty": 1.18,
            "temperature": 0.3,
            "top_p": 0.1
        }

        _data = json.dumps(payload)
        response = requests.post(f"{jan_ai_url}/v1/chat/completions", headers=headers, data=_data, timeout=712)
        response.raise_for_status()
    except requests.RequestException as excecao:
        print(f"Erro ao processar a mensagem: {excecao}")
        raise Exception(excecao.strerror)
    return response.json()

if __name__ == "__main__":
    respostas = []
    with open('50059699220248210038.txt', 'r', encoding='utf-8') as f:
        conteudo = f.read()
        __linhas = conteudo.split('\x0c')
        cont = 0
        for __linha in __linhas:
            if cont == 2:
                break
            if len(__linha) > 0:
                respostas.append(sumarizar_processos(__linha)['choices'][0]['message']['content'])
                cont += 1
    with codecs.open('resumos.txt', 'w', encoding='utf-8') as files:
        files.write('\n'.join(respostas))
    print('FIM!')
    