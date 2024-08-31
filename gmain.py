import gradio as gr
import requests
import json

class ChatApp:
    def __init__(self):
        self.context_text = ""

    def send_message(self, question):
        payload = {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": question
                },
                "service": {
                    "type": "string",
                    "description": "--"
                },
                "model": {
                    "type": "string",
                    "description": "llama3"
                }
            }
        }
        response = requests.post('http://localhost:8000/api/v1/conversation-with-sources', headers={'Content-Type': 'application/json'}, json=payload)
        if response.status_code == 200:
            response_json = response.json()
            if 'message' in response_json:
                resposta = response_json['message']
                return resposta
            else:
                return "Erro: Não foi possível obter a resposta."
        else:
            return "Erro: Não foi possível conectar ao servidor."

if __name__ == "__main__":
    app = ChatApp()
    with gr.Blocks() as demo:
        chatbot = gr.Chatbot(height=500)
        msg     = gr.Textbox()
        clear   = gr.ClearButton([msg, chatbot])

        def respond(message, chat_history):
            response = app.send_message(message)
            chat_history.append((message, response))
            return "", chat_history

        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        demo.launch(height=800)