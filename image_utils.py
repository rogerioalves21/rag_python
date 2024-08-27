import os
import cv2
from cv2.typing import MatLike
import fitz
from fitz import Page
from PIL import Image as ImagePIL
import easyocr
import pytesseract
from pytesseract import Output
from langchain_core.documents import Document
from langchain_core.document_loaders.base import BaseBlobParser
from langchain_core.document_loaders.blob_loaders import Blob
from langchain_community.document_loaders.pdf import BasePDFLoader
from typing import Iterator, List, Union, Tuple
from rich import print
from clean_symbols import CleanSymbolsProcessor
from app.api.prepdoclib.textparser import TextParser
from concurrent.futures import ThreadPoolExecutor, wait, as_completed

# pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"
pytesseract.pytesseract.tesseract_cmd = r"C:/Users/rogerio.rodrigues/AppData/Local/Programs/Tesseract-OCR/tesseract.exe"

os.environ['OMP_THREAD_LIMIT'] = '4'

class ImageProcessing:
    def __init__(self):
        # self.__eocrreader = easyocr.Reader(['pt','en'])
        print("image-processing")

    def find_words_remove(self, img_data):
        __words_remove = []
        __whitelist = ['ç','STI:','STI','CCI','-','—',"N",'IC','SICOOB']
        __threshold2 = 10
        
        for i in range(0, len(img_data['text'])):
            __palavra = img_data['text'][i]
            __confidence = int(float(img_data['conf'][i]))
            
            if __confidence < __threshold2 and not __palavra.isspace() and len(__palavra) and __palavra not in __whitelist:
                __words_remove.append(__palavra)
        print(__words_remove)
        return __words_remove

    def get_rgb_from_img(self, img_path: str) -> MatLike:
        image_bgr = cv2.imread(img_path)
        img_rgb   = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        return img_rgb

    def get_text_from_image(self, img_path: str) -> Union[str, None]:
        img_rgb            = cv2.imread(img_path) # self.get_rgb_from_img(img_path)
        config_pytesseract = r'--tessdata-dir assets/tessdata -l por --oem 3 --psm 6'#r'--tessdata-dir assets/tessdata -l por --oem 1 --psm 6 -c preserve_interword_spaces=2 output-preserve-enabled'
        text               = pytesseract.image_to_string(image=img_rgb, lang='por', config=config_pytesseract)
        print(f"\n\nTEXTO ATUAL\n\n{text}")
        words_remove       = self.find_words_remove(self.get_image_data(img_rgb))
        for w in words_remove:
            text = text.replace(w, '')
        return text

    def __task(self, __page: Page, __page_number: int, __img_path: str) -> Union[Tuple[int, str], None]:
        __pixmap: Page       = __page.get_pixmap(dpi=300)
        # __img                = ImagePIL.frombytes("RGB", [__pixmap.width, __pixmap.height], __pixmap.samples)
        
        __img, __new_img     = self.to_gray(__pixmap, __img_path, __page_number)
        # __img                = ImagePIL.frombytes(__to_gray.tobytes())
        __config_pytesseract = r'--tessdata-dir assets/tessdata -l por --oem 1 --psm 6 -c preserve_interword_spaces=1 output-preserve-enable=true'
        __texto              = pytesseract.image_to_string(image=__img, lang='por', nice=9, config=__config_pytesseract)
        # __texto              = '\n\n'.join(self.__eocrreader.readtext(__new_img, detail=0, paragraph=True, text_threshold=0.2))
        # __img.close()
        return __page_number, __texto

    def pdf_to_text(self, img_path: str) -> str:
        __conteudo_arquivo = []
        with fitz.open(img_path) as __pdf:
            with ThreadPoolExecutor(max_workers=4) as exe:
                futures = [exe.submit(self.__task, __page, __page.number, img_path) for __page in __pdf]
                wait(futures)
                for future in as_completed(futures):
                    __page_number, __texto = future.result()
                    __conteudo_arquivo.append({"content": __texto, "page": __page_number})
        __conteudo_arquivo.sort(key=lambda x: x['page'])
        __text = [f"{t['content']}\n\nPágina {t['page']}" for t in __conteudo_arquivo]
        return '-------------------------'.join(__text)

    def pdf_to_image(self, img_path: str, img_folder: str) -> List:
        pdf = fitz.open(img_path)
        imagens_criadas    = []
        for page in pdf:
            pixmap: Page   = page.get_pixmap(dpi=300)
            new_img_folder = img_folder.replace('.png', '_' + str(page.number) + '.png')
            pixmap.pil_save(new_img_folder, optimize=True)
            imagens_criadas.append((new_img_folder, page.number))
        return imagens_criadas

    def to_gray(self, __pixmap: Page, __img_path: str, __page: int):
        __path_foto = __img_path.replace('pdfs', 'to_img')
        __path_foto = __path_foto.replace('.pdf', f'_{__page}.png')
        print(f"CAMINHO FOTO: {__path_foto}")
        __pixmap.pil_save(__path_foto, optimize=True)
        __img_bgr      = cv2.imread(__path_foto)
        __gray         = cv2.cvtColor(__img_bgr, cv2.COLOR_BGR2GRAY)
        __new_img_path = __path_foto.replace('.png', '_GRAY.png')
        cv2.imwrite(__new_img_path, __gray)
        return cv2.imread(__new_img_path), __new_img_path

    # Limiarização simples
    def simple_threshold(self, img_path, mim_threshold=127):
        img = cv2.imread(img_path)
        cv2.imshow('Original Image', img)

        cv2.waitKey(0)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cv2.imshow('Gray', gray)

        cv2.waitKey(0)

        # pixel com valor < 127 será 0. Maior que 127 será 255
        val, thresh = cv2.threshold(gray, mim_threshold, 255, cv2.THRESH_BINARY)

        cv2.imshow('THRESH_BINARY', thresh)

        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # Limiarização com o método de otsu. O valor do threshold será calculado automaticamente
    def otsu_threshold(self, __pixmap: Page, __img_path: str, __page: int):
        __path_foto = __img_path.replace('pdfs', 'to_img')
        __path_foto = __path_foto.replace('.pdf', f'_{__page}.png')
        print(f"CAMINHO FOTO: {__path_foto}")
        __pixmap.pil_save(__path_foto, optimize=True)
        img       = cv2.imread(__path_foto)
        gray      = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        val, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        print('Limiar calculado (cada img possuirá um limiar diferente: ', val)
        new_img_path = __path_foto.replace('.png', '_OTSU.png')
        cv2.imwrite(new_img_path, otsu)
        return cv2.imread(new_img_path)

    def adaptive_threshold(selfs, img_path):
        img = cv2.imread(img_path)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        val, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        print('Limiar calculado (cada img possuirá um limiar diferente: ', val)
        adapt_media = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 9)
        
        new_img_path = img_path.replace('.png', 'THRESH2.png')
        cv2.imwrite(new_img_path, adapt_media)

    def get_image_data(self, img_rgb):
        config_pytesseract = r'--tessdata-dir assets/tessdata -l por --oem 3 --psm 6'# -c preserve_interword_spaces=1 output-preserve-enabled=True'
        return pytesseract.image_to_data(image=img_rgb, lang='por', config=config_pytesseract, output_type=Output.DICT)

    def adaptive_gaussian_threshold(self, img_path):
        img = cv2.imread(img_path)
 
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        adapt_gaussian = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 9)
        
        new_img_path = img_path.replace('.png', 'GAUS.png')
        cv2.imwrite(new_img_path, adapt_gaussian)

    def invert_color(self, img_path: str) -> str:
        img = cv2.imread(img_path)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        invert = 255 - gray

        new_img_path = img_path.replace('.png', 'INVERT.png')
        cv2.imwrite(new_img_path, invert)
        return new_img_path

class PyTesseractParser(BaseBlobParser):
    """Carga un PDF con pdf2image y extrae texto usando pytesseract."""
    def __init__(self, pdf_path: str):
        self._img_processing = ImageProcessing()
        self._pdf_path       = pdf_path
        self._text_parser    = TextParser()

        self._all_letters = " abcdefghijlmonpqrstuvxyzABCDEFGHIJLMNOPQRSTUVXYZ.,;'-0123456789"
    
    def __unicode_to_ascii(self, s: str) -> str:
        texto = ''
        for c in s:
            if c in self._all_letters:
                texto += c 
        return ''.join(texto)

    def __normalize_string(self, s: str) -> str:
        s = self.__unicode_to_ascii(s.lower().strip())
        return s.strip()
    
    def __tratar_linhas_texto(self, document: str) -> str:
        __text = document.replace('.\n','.\n\n').replace('!\n','!\n\n').replace('?\n','?\n\n').replace(':\n',':\n\n').replace(',\n',', ').replace(';\n',' ')
        __text = __text.replace('\\s\\n', '')
        __text = __text.replace('  ', ' ')
        return __text

    def __limpar_texto(self, txt: str) -> str:
        __txt = self._text_parser.parse(content=txt)
        __cleaner = CleanSymbolsProcessor()
        __t       = __cleaner.process_line(__txt).strip()
        return self.__tratar_linhas_texto(__t)

    def lazy_parse(self, blob: Union[Blob, None] = None) -> Iterator[Document]:
        __split       = self._pdf_path.split("/")
        __image_name  = self.__normalize_string(__split[-1]).replace(' ', '_')
        __image_name  = __image_name.replace('.pdf', '.png')
        __texto       = self._img_processing.pdf_to_text(self._pdf_path)
        yield from [
            Document(
                page_content=self.__limpar_texto(__texto),
                metadata={"source": self._pdf_path, "page": 0},
            )
        ]

class PyTesseractLoader(BasePDFLoader):
    def __init__(self, file_path: str) -> None:
        self.parser = PyTesseractParser(pdf_path=file_path)
        super().__init__(file_path)

    def load(self) -> List[Document]:
        return list(self.lazy_load())

    def lazy_load(self) -> Iterator[Document]:
        yield from self.parser.parse(None)

if __name__ == '__main__':
    file_path = "./files/pdfs/CCI1.081_2024.pdf"
    loader    = PyTesseractLoader(file_path)
    documents = loader.load()
    print(documents)
    
    