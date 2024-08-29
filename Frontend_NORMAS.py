# _*_ coding: utf-8 _*_
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import requests
import json
import threading
import asyncio
import websockets
import re

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MVP Normas")
        self.root.geometry("1200x700")

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chat_frame = tk.Frame(self.main_frame)
        self.chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.context_frame = tk.Frame(self.main_frame)
        self.context_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.chunk_frame = tk.Frame(self.main_frame)
        self.chunk_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.config_frame = tk.Frame(root)
        self.config_frame.pack(fill=tk.X, padx=10, pady=10)

        self.chat_area = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, state='disabled')
        self.chat_area.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.entry_frame = tk.Frame(self.chat_frame)
        self.entry_frame.pack(fill=tk.X, padx=5, pady=5)

        self.entry = tk.Entry(self.entry_frame)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(self.entry_frame, text="Enviar", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

        self.context_area = scrolledtext.ScrolledText(self.context_frame, wrap=tk.WORD, height=10, state='disabled')
        self.context_area.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.chunk_area = scrolledtext.ScrolledText(self.chunk_frame, wrap=tk.WORD, height=10, state='disabled')
        self.chunk_area.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        # CONTEXTO
        self.context_text = """ """

        #tags de formatação
        self.chat_area.tag_config("user", foreground="blue", font=("Helvetica", 12, "bold"))
        self.chat_area.tag_config("mistral", foreground="green", font=("Helvetica", 12, "italic"))
        self.context_area.tag_config("context", foreground="purple", font=("Helvetica", 10))
        self.chunk_area.tag_config("chunk", foreground="brown", font=("Helvetica", 10))

        #tags para JSON
        self.context_area.tag_configure("string", foreground="green")
        self.context_area.tag_configure("number", foreground="orange")
        self.context_area.tag_configure("boolean", foreground="purple")
        self.context_area.tag_configure("null", foreground="red")
        self.context_area.tag_configure("key", foreground="blue")
        
        #configurações
        self.model_label = tk.Label(self.config_frame, text="Escolha o modelo:")
        self.model_label.pack(side=tk.LEFT, padx=5)
        self.model_var = tk.StringVar(value="llama3")
        self.model_menu = ttk.Combobox(self.config_frame, textvariable=self.model_var)
        self.model_menu['values'] = ("llama3", "phi3", "mistral")
        self.model_menu.pack(side=tk.LEFT, padx=5)

        self.caching_var = tk.BooleanVar(value=True)
        self.caching_check = tk.Checkbutton(self.config_frame, text="Habilitar Cache", variable=self.caching_var)
        self.caching_check.pack(side=tk.LEFT, padx=5)

        self.max_doc_size_label = tk.Label(self.config_frame, text="Tamanho máximo do documento:")
        self.max_doc_size_label.pack(side=tk.LEFT, padx=5)
        self.max_doc_size_var = tk.IntVar(value=10000)
        self.max_doc_size_entry = tk.Entry(self.config_frame, textvariable=self.max_doc_size_var)
        self.max_doc_size_entry.pack(side=tk.LEFT, padx=5)

    def send_message(self, event=None):
        message = self.entry.get()
        if message:
            self.display_message("Você: " + message, "user")
            self.entry.delete(0, tk.END)
            threading.Thread(target=self.query_api, args=(message,)).start()

    def display_message(self, message, sender):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + "\n", sender)
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

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

            self.context_area.config(state='normal')
            formatted_result = json.dumps(query_result, indent=4, ensure_ascii=False)
            self.highlight_json(formatted_result)
            self.context_area.config(state='disabled')

            self.chunk_area.config(state='normal')
            chunk_texts = []
            for chunk in chunks:
                chunk_text = f"Documento: {chunk['doc_name']}, Chunk ID: {chunk['chunk_id']}, Score: {chunk['score']}\n{chunk['text']}\n\n"
                chunk_texts.append(chunk_text)
                self.chunk_area.insert(tk.END, chunk_text, "chunk")
            self.chunk_area.config(state='disabled')

            chunk_context = '\n'.join(chunk_texts)
            threading.Thread(target=self.get_response, args=(user_message, chunk_context)).start()
        else:
            self.display_message("Erro ao buscar chunks.", "system")

    def highlight_json(self, json_text):
        self.context_area.config(state='normal')
        self.context_area.delete(1.0, tk.END)
        for token in re.split(r'(".*?"|\s+|\{|\}|\[|\]|:|,)', json_text):
            if not token:
                continue
            elif token.startswith('"'):
                if re.match(r'^"\s*:\s*$', token): 
                    self.context_area.insert(tk.END, token, 'key')
                else: 
                    self.context_area.insert(tk.END, token, 'string')
            elif token in ('true', 'false'):
                self.context_area.insert(tk.END, token, 'boolean')
            elif token == 'null':
                self.context_area.insert(tk.END, token, 'null')
            elif re.match(r'^\s*[\{\}\[\]:,]\s*$', token):  
                self.context_area.insert(tk.END, token)
            elif re.match(r'^-?\d+(\.\d+)?([eE][+-]?\d+)?$', token):  
                self.context_area.insert(tk.END, token, 'number')
            else:  
                self.context_area.insert(tk.END, token)
        self.context_area.config(state='disabled')

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
                    "model": self.model_var.get()
                })
                await websocket.send(payload)

                self.chat_area.config(state='normal')
                self.chat_area.insert(tk.END, "Sicoob: ", "mistral")
                self.chat_area.config(state='disabled')

                async for message in websocket:
                    response_json = json.loads(message)
                    if 'message' in response_json:
                        response_chunk = response_json['message']
                        self.chat_area.config(state='normal')
                        self.chat_area.insert(tk.END, response_chunk, "llama")
                        self.chat_area.config(state='disabled')
                        self.chat_area.yview(tk.END)

                    if response_json.get('finish_reason') == 'stop':
                        break

                self.chat_area.config(state='normal')
                self.chat_area.insert(tk.END, "\n", "llama")
                self.chat_area.config(state='disabled')
        except Exception as e:
            self.display_message(f"Erro: {str(e)}", "system")


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
