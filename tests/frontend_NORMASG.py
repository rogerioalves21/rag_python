import gradio as gr
import requests
import json
import asyncio
import websockets
import re
import threading

class ChatApp:
    def __init__(self):
        self.context_text = ""
        self.model_var = "llama3"
        self.caching_var = True
        self.max_doc_size_var = 10000

    def send_message(self, message):
        if message:
            self.display_message("Você: " + message, "user")
            threading.Thread(target=self.query_api, args=(message,)).start()
            return "", "", ""

    def display_message(self, message, sender):
        return message + "\n", "user" if sender == "user" else "mistral"

    def query_api(self, user_message):
        query_url = 'http://localhost:8000/api/generate'
        query_payload = {
            "query": user_message,
            "context": self.context_text
        }
        query_headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(query_url, headers=query_headers, json=query_payload)
        if response.status_code == 200:
            query_result = response.json()
            chunks = query_result.get('chunks', [])
            context = query_result.get('context', '')

            formatted_result = json.dumps(query_result, indent=4, ensure_ascii=False)
            self.highlight_json(formatted_result)

            chunk_texts = []
            for chunk in chunks:
                chunk_text = f"Documento: {chunk['doc_name']}, Chunk ID: {chunk['chunk_id']}, Score: {chunk['score']}\n{chunk['text']}\n\n"
                chunk_texts.append(chunk_text)

            chunk_context = '\n'.join(chunk_texts)
            threading.Thread(target=self.get_response, args=(user_message, chunk_context)).start()
            return "", "", ""

    def highlight_json(self, json_text):
        # implement JSON highlighting logic here
        pass

    def get_response(self, user_message, chunk_context):
        asyncio.run(self.get_response_async(user_message, chunk_context))

    async def get_response_async(self, user_message, chunk_context):
        url = 'ws://localhost:8000/ws/generate_stream'
        try:
            async with websockets.connect(url) as websocket:
                prompt = (
                    "Você é um assistente cognitivo que serve para responder perguntas sobre o contexto fornecido. "
                    "Suas respostas devem sempre ser no idioma português. Não responda questões que não envolvam o conteúdo do contexto informado.\n\n"
                    "Pergunta: " + user_message
                )
                payload = json.dumps({
                    "query": prompt,
                    "context": chunk_context,
                    "conversation": [],
                    "model": self.model_var
                })
                await websocket.send(payload)

                response = await websocket.recv()
                response_json = json.loads(response)
                if 'message' in response_json:
                    response_chunk = response_json['message']
                    return "Sicoob: " + response_chunk, "", ""

                if response_json.get('finish_reason') == 'stop':
                    return "", "", ""

        except Exception as e:
            return f"Erro: {str(e)}", "", ""

if __name__ == "__main__":
    app = ChatApp()
    iface = gr.Interface(
        fn=app.send_message,
        inputs="text",
        outputs=["text", "text", "text"],
        title="MVP Normas",
        description="Chat App"
    )
    iface.launch()