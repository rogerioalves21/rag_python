import fitz
import pytesseract
from PIL import Image
from pytesseract import Output
import cv2
import ollama

pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

def get_rgb_from_img(img_path):
    image_bgr = cv2.imread(img_path)
    img_rgb   = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    return img_rgb

def get_text_from_image(img_path):
    img_rgb = get_rgb_from_img(img_path)
    config_pytesseract = '--tessdata-dir assets/tessdata'
    text = pytesseract.image_to_string(image=img_rgb, lang='por', config=config_pytesseract)
    return text

if __name__ == "__main__":
    res = ollama.chat(
        model='bakllava',
        messages=[
            #{
            #    'role': "system",
            #    "content": "Você é um sistema OCR que apenas responde perguntas relacionadas a imagem forncecida. Responda as perguntas do usuário sempre no idioma que ele utilizou."
            #},
            {
                'role': 'user',
                'content': 'Descreve essa imagem. O que está escrito nela?',
                'images': ['C:/mnt/CCI1202_0.png']
            }
        ],
        keep_alive='1h'
    )
    print(res['message']['content'])