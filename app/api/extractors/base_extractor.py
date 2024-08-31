"""Abstract interface for document loader implementations."""
from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document


class BaseExtractor(ABC):
    """Interface for extract files.
    """

    @abstractmethod
    def extract(self) -> List[Document]:
        raise NotImplementedError