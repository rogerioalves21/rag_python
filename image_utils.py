import cv2
from cv2.typing import MatLike
import fitz
from typing import List, Union
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

class ImageProcessing:

    def __init__(self):
        print('Image Processing')

    def get_rgb_from_img(self, img_path: str) -> MatLike:
        image_bgr = cv2.imread(img_path)
        img_rgb   = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        return img_rgb

    def get_text_from_image(self, img_path: str) -> Union[str, None]:
        img_rgb            = self.get_rgb_from_img(img_path)
        config_pytesseract = r'--tessdata-dir assets/tessdata -l por --oem 1 --psm 6'
        text               = pytesseract.image_to_string(image=img_rgb, lang='por', config=config_pytesseract)
        return text

    def pdf_to_image(self, img_path: str, img_folder: str) -> List:
        pdf = fitz.open(img_path)
        imagens_criadas    = []
        for page in pdf:
            pixmap         = page.get_pixmap(dpi=500)
            new_img_folder = img_folder.replace('.png', '_' + str(page.number) + '.png')
            
            pixmap.pil_save(new_img_folder, optimize=True)
            # new_img_folder = self.invert_color(new_img_folder)
            imagens_criadas.append((new_img_folder, page.number))
        return imagens_criadas

    def to_gray(self, img_path):
        img_bgr = cv2.imread(img_path)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        cv2.imwrite(img_path.replace('.png', 'GRAY.png'), gray)
        
        cv2.imshow('Image', gray)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

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
    def otsu_threshold(self, img_path):
        img = cv2.imread(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        val, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        print('Limiar calculado (cada img possuirá um limiar diferente: ', val)
        cv2.imshow('THRESH_OTSU', otsu)

        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def adaptive_threshold(selfs, img_path):
        # Limiarização usando a média de pixels na região
        img = cv2.imread(img_path)
        cv2.imshow('Original Image', img)

        cv2.waitKey(0)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        val, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        print('Limiar calculado (cada img possuirá um limiar diferente: ', val)
        cv2.imshow('THRESH_OTSU', otsu)

        cv2.waitKey(0)

        adapt_media = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 9)
        cv2.imshow('ADAPT_MEDIA', adapt_media)

        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def adaptive_gaussian_threshold(self, img_path):
        #Menos ruídos - Testar com imagens com sombras
        img = cv2.imread(img_path)
        cv2.imshow('Original Image', img)
        cv2.waitKey(0)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        adapt_gaussian = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 9)
        cv2.imshow('ADAPT_MEDIA_GAUS', adapt_gaussian)

        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def invert_color(self, img_path: str) -> str:
        img = cv2.imread(img_path)
        # cv2.imshow('Original Image', img)
        # cv2.waitKey(0)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # print(gray)
        # cv2.waitKey(0)

        invert = 255 - gray

        # cv2.imshow('Imagem invertida', invert)
        # cv2.waitKey(0)
        new_img_path = img_path.replace('.png', 'INVERT.png')
        cv2.imwrite(new_img_path, invert)
        return new_img_path

if __name__ == '__main__':
    imgProcessing = ImageProcessing()
    
    