"""Classe abstrata para implementações de storage."""

from abc import ABC, abstractmethod
from collections.abc import Generator

class BaseStorage(ABC):
    """File storage."""

    def __init__(self):
        self.app = None

    @abstractmethod
    def save(self, filename: str, data):
        raise NotImplementedError

    @abstractmethod
    def load_once(self, filename: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def load_stream(self, filename: str) -> Generator:
        raise NotImplementedError

    @abstractmethod
    def download(self, filename: str, target_filepath: str):
        raise NotImplementedError

    @abstractmethod
    def exists(self, filename: str):
        raise NotImplementedError

    @abstractmethod
    def delete(self, filename: str):
        raise NotImplementedError