from pathlib import Path
from uuid import uuid4

from app.core.config import settings


class LocalStorageService:
    def create_resume_dir(self) -> Path:
        resume_dir = settings.upload_dir / "resumes" / str(uuid4())
        resume_dir.mkdir(parents=True, exist_ok=False)
        return resume_dir
