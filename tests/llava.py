import asyncio
from ollama import AsyncClient
import base64
import os
import io
from PIL import Image
import ollama

def get_image(image_path):
    with open(image_path, 'rb') as file:
        return file.read()

def encode_image(image_path):
    """Getting the base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def generate_text(instruction, file_path):
    result = ollama.generate(
        model='llava-phi3',
        prompt=instruction,
        images=[file_path],
        stream=False
    )['response']
    img=Image.open(file_path, mode='r')
    img = img.resize([int(i/1.2) for i in img.size])
    print(img) 
    for i in result.split('.'):
        print(i, end='', flush=True)

async def main():
    #instruction = "Descreva a imagem." 
    #file_path = 'C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/files/to_img/comprovante_0.png'
    #generate_text(instruction, file_path)
    
    #import sys; sys.exit(0) 'Você é um assistente OCR. Extraia todo o texto da imagem. O idioma é português.'

    prompt = """You are an assistant tasked with text extraction from images for retrieval."""
    
    b64 = get_image('C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/files/to_img/CCI1.088_2024_0.png')
    #with Image.open('C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/files/to_img/cci1202_0.png','rb') as f:
    #    b64 = f
    async for part in await AsyncClient().chat(
        model='llava-phi3',
        messages=[
            {
                'role': 'user',
                'content': prompt,
                'images': [b64]
            }
        ],
        options={'num_predict': 2000, "temperature": 0.7},
        keep_alive='1h',
        stream=True,
    ):print(part['message']['content'], end='', flush=True)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    