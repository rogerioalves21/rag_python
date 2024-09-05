# -*- coding: utf-8 -*-

class PdfToTextExtractor():
    """  """
    """ https://ronnywang.github.io/pdf-table-extractor/ """
    def to_text(self, diretorio: str):
        
        import subprocess
        import shutil

        if shutil.which('pdftotext'):
            cmd = ["pdftotext", "-layout", "-nodiag", "-enc", "UTF-8", "-colspacing", "0.3"]
            cmd += [diretorio, "-"]
            print(cmd)
            out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
            return out.decode('utf-8')
        else:
            raise EnvironmentError(
                "pdftotext not installed. Can be downloaded from https://poppler.freedesktop.org/"
            )

if __name__ == "__main__":
    pdftotext = PdfToTextExtractor()
    texto = pdftotext.to_text('/home/rogerio_rodrigues/python-workspace/rag_python/files/old_pdfs/CCI500_2023.pdf')
    print(texto)