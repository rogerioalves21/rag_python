import ocrmypdf

if __name__ == '__main__':  # To ensure correct behavior on Windows and macOS
    ocrmypdf.ocr('./files/pdfs/CCI1010.pdf', './files/pdfs/CCI1010_deskew.pdf')