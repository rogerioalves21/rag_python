import os
import shutil
from collections.abc import Generator

# https://cohere.com/blog/search-cohere-langchain  https://www.youtube.com/watch?v=1FERFfut4Uw

from app.storage.base_storage import BaseStorage


class LocalStorage(BaseStorage):
    """Implementação para o local storage."""

    def __init__(self):
        super().__init__()
        folder = '/home/rogerio_rodrigues/python-workspace/rag_python/local_storage/' # 'C:/Users/rogerio.rodrigues/Documents/workspace_python/rag_python/local_storage/'
        self.folder = folder

    def save(self, filename: str, data):
        if not self.folder or self.folder.endswith("/"):
            filename = self.folder + filename
        else:
            filename = self.folder + "/" + filename

        folder = os.path.dirname(filename)
        os.makedirs(folder, exist_ok=True)

        with open(os.path.join(os.getcwd(), filename), "wb") as f:
            f.write(data)

    def load_once(self, filename: str) -> bytes:
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

    def exists(self, filename):
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