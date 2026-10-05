from abc import ABC, abstractmethod
from typing import BinaryIO, Optional

class BaseStorage(ABC):
    @abstractmethod
    def upload_file(self, file_obj: BinaryIO, destination_path: str, content_type: Optional[str] = None) -> str:
        """Uploads file and returns access path or URL."""
        pass

    @abstractmethod
    def download_file(self, source_path: str, local_destination: str) -> str:
        """Downloads file to local path."""
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Checks if file exists in storage."""
        pass
