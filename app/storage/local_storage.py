import os
import shutil
from collections.abc import Generator
from app.storage.base_storage import BaseStorage
import json
from typing import Any, List
import glob

# '/home/rogerio_rodrigues/python-workspace/rag_python/local_storage/'
# https://cohere.com/blog/search-cohere-langchain  https://www.youtube.com/watch?v=1FERFfut4Uw


class LocalStorage(BaseStorage):
    """Implementação para o local storage."""

    def __init__(self):
        super().__init__()
        folder = '/home/rogerio_rodrigues/python-workspace/rag_python/local_storage/' # 'C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/local_storage/'
        self.folder = folder
        print(f"diretório storage: {self.folder}")

    def save(self, filename: str, data):
        if not self.folder or self.folder.endswith("/"):
            filename = self.folder + filename
        else:
            filename = self.folder + "/" + filename

        folder = os.path.dirname(filename)
        os.makedirs(folder, exist_ok=True)
        print(F"\nARQUIVO SALVAR: {filename}\n")

        with open(os.path.join(os.getcwd(), filename), "wb") as f:
            print("\nF.WRITE\n")
            f.write(data)

    def load_json(self, filename: str) -> Any:
        print(f"\nCARREGANDO O ARQUIVO {filename}\n")
        if not self.folder or self.folder.endswith("/"):
            filename = self.folder + filename
        else:
            filename = self.folder + "/" + filename
        if not os.path.exists(filename):
            raise FileNotFoundError("Arquivo ou diretório não encontrado!")
        with open(filename, "rb") as f:
            data = json.load(f)
        return data

    def load_json_all(self) -> List:
        print(f"\nCARREGANDO O DIRETÓRIO {self.folder}\n")
        __json_files = []
        __files = os.listdir(self.folder)
        for __file in __files:
            with open(self.folder + __file, "rb") as f:
                __json = json.load(f)
                __json_files.append(__json)
        return __json_files

    def load_once(self, filename: str) -> bytes:
        print(f"carregando o arquivo {filename}")
        if not self.folder or self.folder.endswith("/"):
            filename = self.folder + filename
        else:
            filename = self.folder + "/" + filename

        if not os.path.exists(filename):
            raise FileNotFoundError("Arquivo não encontrado")

        with open(filename, "rb") as f:
            data = f.read()

        return data

    def load_stream(self, filename: str) -> Generator:
        def generate(filename: str = filename) -> Generator:
            if not self.folder or self.folder.endswith("/"):
                filename = self.folder + filename
            else:
                filename = self.folder + "/" + filename

            if not os.path.exists(filename):
                raise FileNotFoundError("Arquivo não encontrado")

            with open(filename, "rb") as f:
                while chunk := f.read(4096):  # Read in chunks of 4KB
                    yield chunk

        return generate()

    def download(self, filename, target_filepath):
        if not self.folder or self.folder.endswith("/"):
            filename = self.folder + filename
        else:
            filename = self.folder + "/" + filename

        if not os.path.exists(filename):
            raise FileNotFoundError("Arquivo não encontrado")

        shutil.copyfile(filename, target_filepath)

    def exists(self, filename: str):
        print(f"exists {filename}")
        if not self.folder or self.folder.endswith("/"):
            filename = self.folder + filename
        else:
            filename = self.folder + "/" + filename
        return os.path.exists(filename)

    def delete(self, filename):
        if not self.folder or self.folder.endswith("/"):
            filename = self.folder + filename
        else:
            filename = self.folder + "/" + filename
        if os.path.exists(filename):
            os.remove(filename)

storage = LocalStorage()