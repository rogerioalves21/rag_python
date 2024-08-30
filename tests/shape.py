import cv2
from cv2.typing import MatLike
import fitz
import pytesseract
import numpy as np
from pytesseract import Output
from PIL import Image
from langchain_core.documents import Document
from langchain_core.document_loaders.base import BaseBlobParser
from langchain_core.document_loaders.blob_loaders import Blob
from langchain_community.document_loaders.pdf import BasePDFLoader
from typing import Iterator, List, Union
from rich import print
from app.api.prepdoclib.clean_symbols import CleanSymbolsProcessor, show_paragraphs
from PIL import ImageFont, Image, ImageDraw
from app.api.prepdoclib.image_utils import ImageProcessing

pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

def draw_rectangle(result, img, index, color=(255, 100, 0)):
    x = result['left'][index]
    y = result['top'][index]
    w = result['width'][index]
    h = result['height'][index]
    thickness = 2
    cv2.rectangle(img, (x, y), (x+w, y+h), color, thickness)
    return x, y, img

def write_text(text, x, y, img, text_size=12):
    font_type = ImageFont.truetype('assets/font/calibri.ttf', text_size)
    img_pil   = Image.fromarray(img)
    draw      = ImageDraw.Draw(img_pil)
    draw.text((x, y - text_size), text, font=font_type, fill=(0, 0, 255))
    img       = np.array(img_pil)
    return img

def get_image_df(img_rgb):
    config_pytesseract = f'--tessdata-dir assets/tessdata --oem 3 --psm 6' #-c preserve_interword_spaces=1 output-preserve-enabled=True'
    return pytesseract.image_to_data(image=img_rgb, lang='por', config=config_pytesseract, output_type=Output.DATAFRAME)

def get_image_data(img_rgb):
    config_pytesseract = f'--tessdata-dir assets/tessdata --oem 3 --psm 6 '# -c preserve_interword_spaces=1 output-preserve-enabled=True'
    return pytesseract.image_to_data(image=img_rgb, lang='por', config=config_pytesseract, output_type=Output.DICT)

def get_rgb_from_img(img_path):
    image_bgr = cv2.imread(img_path)
    img_rgb   = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    return img_rgb

def find_words_remove(img, img_data):
    img_copy = img.copy()
    
    words_remove = []
    
    for i in range(0, len(img_data['text'])):
        palavra = img_data['text'][i]
        confidence = int(float(img_data['conf'][i]))
        threshold = 70
        threshold2 = 65
        
        if confidence < threshold2 and not palavra.isspace() and len(palavra):
            words_remove.append(palavra)
        
        if confidence > threshold and not palavra.isspace() and len(palavra):
            print(palavra, confidence)
            x, y, img_copy = draw_rectangle(img_data, img_copy, i)
            img_copy = write_text(palavra, x, y, img_copy)
    
    #cv2.imshow('Image', img_copy)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    return words_remove

def linha_inteira(df, original_image):
    for line_num, words_per_line in df.groupby("line_num"):
        # filter out words with a low confidence
        words_per_line = words_per_line[words_per_line["conf"] >= 5]
        if not len(words_per_line):
            continue

        words = words_per_line["text"].values
        line = " ".join(words)
        print(f"{line_num} '{line}'")

        # if target_text in line:
        # print("Found a line with specified text")
        word_boxes = []
        for left, top, width, height in words_per_line[["left", "top", "width", "height"]].values:
            word_boxes.append((left, top))
            word_boxes.append((left + width, top + height))

        x, y, w, h = cv2.boundingRect(np.array(word_boxes))
        cv2.rectangle(original_image, (x, y), (x + w, y + h), color=(255, 0, 255), thickness=3)

    cv2.imshow('Image', original_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    img_processing = ImageProcessing()
    sicoob = './files/to_img/cci1029_0.png'
    comp = './files/to_img/comprovante_0.png'
    # comprovante = get_rgb_from_img(sicoob)
    comprovante = cv2.imread(sicoob)
    # gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
    config_pytesseract = r'--tessdata-dir assets/tessdata --oem 3 --psm 6' # -c preserve_interword_spaces=1 output-preserve-enabled=True'
    text_pdf = pytesseract.pytesseract.image_to_string(comprovante, lang='por', config=config_pytesseract)
    
    # boxes = pytesseract.pytesseract.image_to_boxes(comprovante, lang='por', config=config_pytesseract)
    # altura_total, largura_total, _ = comprovante.shape
    
    img_data = get_image_data(comprovante)
    img_df   = get_image_df(comprovante)
    
    words_remove = find_all(comprovante, img_data)
    print(words_remove)
    for w in words_remove:
        text_pdf = text_pdf.replace(w, '')
    print(text_pdf)
    
    #linha_inteira(img_df, comprovante)
    
    #print(img_data)
    
    #for box in boxes.splitlines():
    #    b = box.split(' ')
        # print(b)
    #    letra, eixo_x, eixo_y, largura, altura = b[0], int(b[1]), int(b[2]), int(b[3]), int(b[4])
    #    x, y, img_copy = draw_rectangle(img_data, img_copy, i)
    #    img_copy = write_text(text, x, y, img_copy)
        # cv2.rectangle(comprovante, (eixo_x, altura_total - eixo_y), (largura, altura_total - altura), (0,0,255), 1)
         
        # img_copy = write_text(text, x, y, img_copy) 
        #  cv2.putText(comprovante, letra, (eixo_x, altura_total-eixo_y+25), cv2.FONT_HERSHEY_SIMPLEX)
    #cv2.imshow('Comprovante', comprovante)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()