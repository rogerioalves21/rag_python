from app.api.prepdoclib.image_utils import PyTesseractLoader

if __name__ == '__main__':
    file_path = "./files/old_pdfs/0702763-79.2024.8.07.0014_0010.pdf"
    loader    = PyTesseractLoader(file_path)
    documents = loader.load()
    print(documents)