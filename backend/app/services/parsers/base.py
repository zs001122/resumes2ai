from abc import ABC, abstractmethod
from pathlib import Path


class ResumeParser(ABC):
    @abstractmethod
    def extract_text(self, file_path: Path) -> str:
        """Extract plain text from a resume file."""
